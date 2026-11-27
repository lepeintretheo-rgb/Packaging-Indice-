import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import collecte as c

def fixture(filters,dates,values,status=None):
    ids=list(filters)+['time']; dims={k:{'category':{'index':{v:0}}} for k,v in filters.items()}
    dims['time']={'category':{'index':{d:i for i,d in enumerate(dates)}}}
    return {'id':ids,'size':[1]*len(filters)+[len(dates)],'dimension':dims,'value':values,'status':status or {}}

class CollecteTests(unittest.TestCase):
    def test_sparse_flags(self):
        d=fixture({'unit':'I21'},['2025-01','2025-02','2025-03','2025-04'],{'0':100,'2':115,'3':120},{'2':'p','3':'c'})
        pts=c.jsonstat_series(d,{'unit':'I21'})
        self.assertEqual(pts,[{'date':'2025-01','value':100.0,'flag':''},{'date':'2025-03','value':115.0,'flag':'p'}])
    def test_reject_bad_dimension(self):
        with self.assertRaises(ValueError):c.jsonstat_series(fixture({'unit':'I15'},['2025-01'],[100]),{'unit':'I21'})
    def test_comext_conversion(self):
        spec=dict(reporter='FR',partner='WORLD',code='390210')
        f=dict(freq='M',reporter='FR',partner='WORLD',product='390210',flow='1')
        dates=['2025-01','2025-02','2025-03']
        v=fixture(dict(f,indicators='VALUE_IN_EUROS'),dates,[25000000,100,None])
        q=fixture(dict(f,indicators='QUANTITY_IN_100KG'),dates,[200000,0,50])
        with patch.object(c,'get_json',side_effect=[v,q]):
            self.assertEqual(c.comext(spec,'2021-01-01'),[{'date':'2025-01','value':1250.0,'flag':'','trade_eur':25000000.0,'mass_t':20000.0}])
    def test_csv_missing(self):
        text='observation_date,DCOILBRENTEU\n2025-01-01,.\n2025-01-02,80.5\n2025-01-03,NaN\n'
        self.assertEqual(c.csv_series(text,['observation_date','DATE'],'DCOILBRENTEU'),[{'date':'2025-01-02','value':80.5,'flag':''}])
    def test_csv_ecb(self):
        pts=c.csv_series('TIME_PERIOD,OBS_VALUE,OBS_STATUS\n2025-01-03,1.04,A\n',['TIME_PERIOD'],'OBS_VALUE','OBS_STATUS')
        self.assertEqual(pts,[{'date':'2025-01-03','value':1.04,'flag':'A'}])
    def test_cache_on_error(self):
        s=dict(id='x',provider='ppi',code='C2016',geo_code='EU27_2020',unit='2021=100',frequency='Mensuelle')
        pts=[{'date':'2025-01-01','value':100,'flag':''}]
        old={'x':dict(s,points=pts,last_success='old')}
        with patch.dict(c.PROVIDERS,{'ppi':lambda *_: (_ for _ in ()).throw(RuntimeError('API indisponible'))}):
            row=c.update_one(s,old,'2021-01-01','now');self.assertEqual(row['status'],'cached');self.assertEqual(row['points'],pts);self.assertEqual(row['last_success'],'old')
            self.assertEqual(c.update_one(dict(s,code='C2222'),old,'2021-01-01','now')['status'],'missing')
    def test_revision_and_sorting(self):
        s={'frequency':'Mensuelle','provider':'ppi'}
        pts=c.normalize([{'date':'2025-02','value':101},{'date':'2025-01','value':100} ],s,'2021-01-01')
        self.assertEqual([x['date'] for x in pts],['2025-01-01','2025-02-01'])
    def test_output(self):
        s=dict(id='pp',name='PP',geo='FR',unit='EUR/t',source='Eurostat',status='ok',points=[{'date':'2025-01-01','value':1250}])
        p=dict(series=[s],demo=False)
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);c.write_outputs(p,folder);self.assertEqual(json.loads((folder/'market.json').read_text()),p);self.assertIn('window.MARKET_DATA',(folder/'market.js').read_text());self.assertIn('1250',(folder/'historique.csv').read_text())

if __name__=='__main__':unittest.main()
