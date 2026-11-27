"""Collecte des séries publiques. Python 3.11+, aucune dépendance externe."""
import argparse
import concurrent.futures
import csv
import datetime as dt
import io
import json
import math
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAT = 'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
COMEXT = 'https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/'

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')

def url(base, **params):
    return base + '?' + urllib.parse.urlencode(params, doseq=True)

def get(address):
    last = None
    for attempt in range(2):
        try:
            request = urllib.request.Request(address, headers={'User-Agent':'PackagingMarketMonitor/1.0 (public statistics)','Accept':'*/*'})
            with urllib.request.urlopen(request, timeout=30) as resp:
                return resp.read().decode('utf-8-sig')
        except (OSError, UnicodeError) as exc:
            last = exc
            if attempt == 0: time.sleep(2)
    raise RuntimeError(f'Requete impossible: {last}')

def get_json(address):
    payload = json.loads(get(address))
    if not isinstance(payload, dict) or 'dimension' not in payload or 'value' not in payload:
        raise ValueError('Reponse Eurostat sans donnees statistiques (ou extraction asynchrone)')
    return payload

def number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError): return None

def categories(dimension):
    index = dimension['category']['index']
    if isinstance(index,list): return index
    return [k for k,v in sorted(index.items(),key=lambda kv:kv[1])]

def indexed(obj, i):
    if isinstance(obj, list): return obj[i] if i < len(obj) else None
    if isinstance(obj, dict): return obj.get(str(i))
    return None

def jsonstat_series(data, expected):
    """Une seule combinaison hors temps; validation des filtres et conservation des flags."""
    ids = data['id']; sizes = data['size']; dims = data['dimension']
    if len(ids) != len(sizes) or len(set(ids)) != len(ids): raise ValueError('Dimensions invalides')
    keys = [x.lower() for x in ids]
    t = next((i for i,k in enumerate(keys) if k in ('time','time_period')), None)
    if t is None: raise ValueError('Dimension temps absente')
    for key,val in expected.items():
        if key.lower() not in keys: raise ValueError('Filtre absent: '+key)
        i=keys.index(key.lower())
        if categories(dims[ids[i]]) != [val]: raise ValueError('Filtre inattendu: '+key)
    if any(n != 1 for i,n in enumerate(sizes) if i != t): raise ValueError('Requete non univoque')
    times = categories(dims[ids[t]])
    if len(times)!=sizes[t]: raise ValueError('Dimension temps incoherente')
    stride=math.prod(sizes[t+1:]); out=[]
    for i,period in enumerate(times):
        pos=i*stride; n=number(indexed(data['value'],pos)); flag=indexed(data.get('status',{}),pos) or ''
        if n is not None and 'c' not in str(flag).lower():
            out.append({'date':period,'value':n,'flag':str(flag)})
    return out

def ppi(spec,start):
    filters=dict(freq='M',indic_bt='PRC_PRR_DOM',s_adj='NSA',unit='I21',nace_r2=spec['code'],geo=spec['geo_code'])
    u=url(STAT+'sts_inppd_m',lang='EN',sinceTimePeriod=start[:7],**filters)
    return jsonstat_series(get_json(u),filters)

def comext(spec,start):
    common=dict(freq='M',reporter=spec['reporter'],partner=spec['partner'],product=spec['code'],flow='1')
    def fetch(indicator):
        f=dict(common,indicators=indicator)
        u=url(COMEXT+'ds-045409',lang='EN',sinceTimePeriod=start[:7],**f)
        return {p['date']:p for p in jsonstat_series(get_json(u),f)}
    values=fetch('VALUE_IN_EUROS'); masses=fetch('QUANTITY_IN_100KG')
    out=[]
    for d,v in values.items():
        m=masses.get(d)
        if m and m['value']>0 and v['value']>0:
            # 1 tonne = 10 units of 100 kg.
            flags=' / '.join(filter(None,[v['flag'],m['flag']]))
            out.append({'date':d,'value':round(10*v['value']/m['value'],2),'flag':flags,'trade_eur':v['value'],'mass_t':m['value']/10})
    return out

def csv_series(text, date_keys, value_key, flag_key=None):
    rows=csv.DictReader(io.StringIO(text))
    if not rows.fieldnames or value_key not in rows.fieldnames: raise ValueError('Colonne de valeur CSV absente')
    date_key=next((k for k in date_keys if k in rows.fieldnames),None)
    if not date_key: raise ValueError('Colonne date CSV absente')
    out=[]
    for row in rows:
        n=number(row.get(value_key))
        if n is not None: out.append({'date':row[date_key],'value':n,'flag':row.get(flag_key,'') or '' if flag_key else ''})
    return out

def fred(spec,start):
    u=url('https://fred.stlouisfed.org/graph/fredgraph.csv',id=spec['code'],cosd=start)
    return csv_series(get(u),['observation_date','DATE'],spec['code'])

def ecb(spec,start):
    u=url('https://data-api.ecb.europa.eu/service/data/EXR/'+spec['code'],format='csvdata',startPeriod=start)
    return csv_series(get(u),['TIME_PERIOD'],'OBS_VALUE','OBS_STATUS')

PROVIDERS={'ppi':ppi,'comext':comext,'fred':fred,'ecb':ecb}

def normalize(points,spec,start):
    out={}; monthly=spec['frequency']=='Mensuelle'; today=dt.date.today()
    for p in points:
        d=p['date']; n=number(p['value'])
        try:
            if monthly and len(d)==7: d+='-01'
            date=dt.date.fromisoformat(d)
        except (TypeError, ValueError): raise ValueError('Date invalide: '+str(d))
        if monthly and date.day!=1: raise ValueError('Observation mensuelle non attendue')
        if date>today: continue
        if date.isoformat()<start or n is None: continue
        if n<=0 and spec['provider']!='fred': continue
        if d in out and out[d]['value']!=n: raise ValueError('Doublon contradictoire: '+d)
        out[d]=dict(p,date=d,value=n)
    return [out[k] for k in sorted(out)]

def update_one(spec,previous,start,stamp):
    row=dict(spec,points=[],last_success=None,checked_at=stamp,status='missing',error=None)
    old=previous.get(spec['id'],{})
    # Do not reuse stale cache if the source definition changed.
    comparable=all(old.get(k)==spec.get(k) for k in ('provider','code','reporter','partner','geo_code','unit','frequency'))
    try:
        pts=normalize(PROVIDERS[spec['provider']](spec,start),spec,start)
        if not pts: raise ValueError('Aucune observation exploitable')
        if comparable and old.get('points') and pts[-1]['date']<old['points'][-1]['date']:
            raise ValueError('La source renvoie un historique plus ancien que le cache')
        row.update(points=pts,last_success=stamp,status='ok')
    except Exception as exc:
        row.update(error=str(exc)[:300])
        if comparable and old.get('points'):
            row.update(points=old['points'],last_success=old.get('last_success'),status='cached')
    return row

def atomic(path,text):
    tmp=path.with_suffix(path.suffix+'.tmp'); tmp.write_text(text,encoding='utf-8'); os.replace(tmp,path)

def write_outputs(payload,folder):
    folder.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)
    atomic(folder/'market.json',raw+'\n')
    atomic(folder/'market.js','window.MARKET_DATA = '+raw.replace('<','\\u003c')+';\n')
    buf=io.StringIO(); w=csv.writer(buf,delimiter=';'); w.writerow(['id','matiere','date','valeur','unite','zone','source','flag','valeur_import_eur','masse_import_t','derniere_collecte','statut'])
    for s in payload['series']:
        for p in s['points']:
            w.writerow([s['id'],s['name'],p['date'],str(p['value']).replace('.',','),s['unit'],s['geo'],s['source'],p.get('flag',''),p.get('trade_eur',''),p.get('mass_t',''),s.get('last_success') or '',s['status']])
    atomic(folder/'historique.csv','\ufeff'+buf.getvalue())

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--init',action='store_true',help='Initialise un site vide sans requete; ecrase les donnees!'); parser.add_argument('--output',type=Path,default=ROOT/'site/data'); args=parser.parse_args()
    config=json.loads((ROOT/'sources.json').read_text(encoding='utf-8')); stamp=now(); previous={}
    if args.init:
        payload={'generated_at':None,'demo':False,'series':[dict(s,points=[],status='missing',last_success=None,checked_at=None,error=None) for s in config['series']]}
        write_outputs(payload,args.output); return
    cache=args.output/'market.json'
    if cache.exists():
        old=json.loads(cache.read_text(encoding='utf-8'))
        if not old.get('demo'): previous={s['id']:s for s in old.get('series',[])}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        series=list(pool.map(lambda s:update_one(s,previous,config['start'],stamp),config['series']))
    for s in series:
        print(f"{s['id']}: {s['status']} - {len(s['points'])} observations"+(f" ({s['error']})" if s['error'] else ''))
    payload={'generated_at':stamp,'demo':False,'series':series}
    write_outputs(payload,args.output)
    available=sum(bool(s['points']) for s in series); failed=sum(s['status']!='ok' for s in series)
    print(f'{available}/{len(series)} series disponibles; {failed} echec(s) de collecte.')
    if failed: print(f'::warning::{failed} source(s) en echec, voir les logs et le site.')
    if not available: raise SystemExit('Aucune donnee disponible; verifier la connectivite et les logs.')

if __name__=='__main__': main()
