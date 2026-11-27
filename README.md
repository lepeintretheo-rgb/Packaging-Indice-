# Packaging Market Monitor — V1

Observatoire web des indicateurs de marché packaging. Site statique en français, collecte quotidienne par GitHub Actions, hébergement GitHub Pages. Aucun abonnement de données ni clé API nécessaire pour les sources prévues. Le prototype public n'est pas destiné à héberger des données internes.

## 1. Avant de commencer

- Lire et appliquer les règles de la DSI de son entreprise avant tout usage professionnel de GitHub. Un dépôt public et un site GitHub Pages public sont visibles de tous. Ne pas y copier les historiques fournisseurs, tarifs négociés, volumes, budgets, noms de contacts, fichiers internes ni clés/API privées. Ne pas utiliser le nom/logo de l'entreprise sans accord.
- GitHub Pages Free fonctionne pour un dépôt public, sous réserve des limites et conditions GitHub. Ce kit est un prototype documentaire de veille, pas un service commercial SaaS.
- Les valeurs douanières ne sont pas des cours spot. Les indices Eurostat sont des indices de prix sectoriels. Une collecte quotidienne ne transforme pas les publications mensuelles en données quotidiennes.
- La liste de séries a été définie à partir de la documentation publique. Les requêtes réelles n'ont pas pu être exécutées depuis l'environnement de création (réseau indisponible). Les tests unitaires simulent les réponses; la première exécution GitHub est le test d'intégration indispensable. Le site commence sans chiffres plutôt qu'avec des données fictives. L'aperçu fictif, fourni séparément, ne doit pas être publié.

## 2. Créer le dépôt GitHub (méthode recommandée, navigateur uniquement)

1. Aller sur https://github.com/join et créer un compte gratuit (ou utiliser un compte autorisé par la DSI). Valider l'adresse de messagerie. Activer la double authentification.
2. Ouvrir https://github.com/new. Dans **Repository name**, saisir `packaging-market-monitor`. Choisir **Public**. Cocher **Add a README file** pour initialiser la branche `main`. Cliquer sur **Create repository**. Si la branche par défaut porte un autre nom, la renommer en `main` (ou adapter les deux références à `main` dans le workflow).
3. Décompresser l'archive `packaging-market-monitor.zip`. Dans la fenêtre du dépôt GitHub, cliquer sur **Add file > Upload files**. Glisser les fichiers `collecte.py`, `sources.json`, `README.md` et les dossiers `site`, `tests` depuis le dossier décompressé. Le dossier `site` doit garder ses fichiers et son sous-dossier `data`. Ne pas glisser le dossier parent `packaging-market-monitor` lui-même. Cliquer sur **Commit changes** (directement sur main). Vérifier que les fichiers et dossiers sont bien à la racine du dépôt. Si l'interface refuse les dossiers, utiliser GitHub Desktop (voir ci-dessous).
4. Le dossier `.github` est caché sous macOS. Pour le voir dans Finder, faire Cmd + Maj + . (point). Ne pas compter sur l'upload web pour le workflow caché. Dans le dépôt GitHub, cliquer sur **Add file > Create new file**. Dans le champ du nom, entrer exactement `.github/workflows/actualisation.yml`. Ouvrir le fichier de même nom du ZIP avec un éditeur texte (TextEdit en texte brut ou VS Code), copier tout son contenu et le coller dans l'éditeur GitHub. Ne pas ajouter les délimiteurs Markdown. Cliquer sur **Commit changes**. Ce fichier doit être directement sous `.github/workflows/` à la racine. Il est également fourni séparément avec le kit.
5. Aller dans **Settings > Pages**, sous **Build and deployment**, choisir **GitHub Actions** comme Source. Ne pas sélectionner « Deploy from a branch ». Ne pas créer un workflow Jekyll supplémentaire. Si GitHub propose un workflow de démarrage, ignorer cette proposition : le workflow est déjà fourni.
6. Aller dans **Settings > Actions > General**. Vérifier que les GitHub Actions sont autorisées et que les actions GitHub officielles sont permises. Dans Workflow permissions, le workflow demande explicitement `contents: write` pour sauvegarder les données et `pages: write`, `id-token: write` pour publier. Si l'organisation bloque l'écriture ou protège `main`, demander à son administrateur d'autoriser l'automatisation; ne pas désactiver des protections imposées. Sur un dépôt personnel, si nécessaire, choisir **Read and write permissions** et enregistrer. L'action n'a pas besoin de créer de pull request.
7. Ouvrir l'onglet **Actions**. Dans la barre latérale, sélectionner **Actualisation packaging**. Cliquer sur **Run workflow**, sélectionner `main`, puis **Run workflow** en vert. Si le premier lancement automatique avait échoué avant d'activer Pages, ce lancement manuel suffit à retenter.
8. Ouvrir le dernier run. Vérifier `collecte` puis `publication`. Dans l'étape **Recuperer les donnees publiques**, le journal indique le nombre d'observations pour chacune des 17 séries et les éventuelles erreurs. Le test de première mise en service n'est réussi que si les séries prioritaires fonctionnent et leurs métadonnées sont cohérentes. Une publication peut réussir avec des sources indisponibles : contrôler les avertissements sur le site.
9. Aller dans **Settings > Pages** et ouvrir **Visit site**, ou récupérer l'URL de l'environnement `github-pages` depuis le run. Pour un dépôt projet, l'adresse sera normalement `https://TON-IDENTIFIANT.github.io/packaging-market-monitor/`. Il n'est pas nécessaire d'acheter un nom de domaine.
10. Vérifier que le site contient des valeurs réelles, que le nombre de séries disponibles est correct, cliquer sur PP, sélectionner 3 mois puis 3 ans, comparer au Brent, filtrer la famille Plastiques et exporter le CSV. Vérifier au moins une valeur récente dans les bases officielles, notamment les valeurs et quantités Comext. Une donnée mensuelle peut avoir un décalage d'un à plusieurs mois.

### Alternative avec GitHub Desktop

Télécharger https://desktop.github.com/, se connecter, puis **File > Clone repository** et choisir le dépôt créé à l'étape 2. Ouvrir le dossier cloné avec **Show in Finder**. Copier TOUT le contenu du ZIP décompressé dans le dossier cloné (pas le dossier parent), y compris `.github` (Cmd + Maj + . pour afficher les fichiers cachés). Ne pas modifier le dossier `.git` créé par GitHub Desktop. Dans GitHub Desktop, contrôler les changements, entrer « Installation Packaging Market Monitor » comme Summary, puis **Commit to main > Push origin**. Reprendre à l'étape 5. GitHub Desktop est plus pratique pour les mises à jour ultérieures.

## 3. Ce que fait l'automatisation

Le workflow déclenche la collecte à 7 h 15, fuseau `Europe/Paris`, chaque jour; il peut aussi être lancé manuellement et lors d'une modification du code sur `main`. Les exécutions planifiées peuvent être retardées. Les workflows de dépôts publics peuvent être désactivés après 60 jours sans activité (GitHub); les commits automatiques quotidiens sont prévus mais vérifier périodiquement l'état d'Actions.

1. Récupération du projet et installation de Python 3.12.
2. Exécution de 8 tests unitaires (sans réseau).
3. Interrogation des API et du CSV FRED, par groupes de cinq requêtes concurrentes au maximum, avec deux tentatives réseau et timeout par requête.
4. Les historiques sont récupérés depuis janvier 2021. Contrôle du format, des unités, des filtres, des valeurs manquantes et doublons. Les révisions sont intégrées par remplacement de la série; pas de création de fausses observations. Le code rejette un historique dont le dernier point est antérieur à celui déjà stocké. Les dates mensuelles sont stockées au premier du mois par convention.
5. Lorsqu'une source ne répond pas, l'historique déjà sauvegardé est conservé et l'erreur est affichée. Une source n'ayant jamais répondu reste indisponible. Si aucune série n'est exploitable, le job échoue sans déployer; consulter le journal. Si toutes échouent mais que des données anciennes existent, elles sont publiées comme cache avec avertissement. Chaque collecte et dernière réussite portent leur horodatage.
6. Les fichiers `site/data/market.json`, `market.js` et `historique.csv` sont enregistrés dans le dépôt. GitHub conserve également les anciennes versions dans l'historique de commits. Le site est publié depuis le dossier `site` uniquement. Une mise à jour n'a pas besoin que ton ordinateur soit allumé.
7. Le tableau de bord calcule les variations sur 1 et 12 mois. Pour une observation mensuelle, le mois de comparaison doit exister exactement. Pour une observation quotidienne, il prend la dernière valeur au plus tard à la date cible (tolérance max 7 jours). Le comparateur base 100 utilise uniquement les mois communs, les moyennes des observations journalières disponibles et écarte le mois en cours pour les séries journalières. Les alertes à l'écran signalent variations et anomalies. **Aucun e-mail automatique n'est configuré dans V1.**

## 4. Données et sources

Toutes les séries sont définies dans `sources.json`. Pas de clé secrète. Les codes sont des paramètres techniques modifiables; la disponibilité de chaque combinaison doit être vérifiée lors du premier run.

| Indicateur | Code | Zone | Nature |
|---|---|---|---|
| PE densité < 0,94 | 390110 | FR, tous partenaires | valeur unitaire d'importation |
| PE densité >= 0,94 | 390120 | FR, tous partenaires | valeur unitaire d'importation |
| PP | 390210 | FR, tous partenaires | valeur unitaire d'importation |
| PET viscosité >= 78 ml/g | 390761 | FR, tous partenaires | valeur unitaire d'importation |
| Kraftliner écru | 480411 | FR, tous partenaires | valeur unitaire d'importation |
| Plastiques primaires | C2016 | UE-27 | indice 2021=100 |
| Emballages plastiques | C2222 | UE-27 | indice 2021=100 |
| Pâte à papier | C1711 | UE-27 | indice 2021=100 |
| Papier et carton | C1712 | UE-27 | indice 2021=100 |
| Carton ondulé et emballages papier/carton | C1721 | UE-27 | indice 2021=100 |
| Production aluminium | C2442 | UE-27 | indice 2021=100 |
| Emballages métalliques légers | C2592 | UE-27 | indice 2021=100 |
| Verre creux | C2313 | UE-27 | indice 2021=100 |
| Emballages bois | C1624 | UE-27 | indice 2021=100 |
| Brent | DCOILBRENTEU | Europe | USD/baril |
| EUR/USD | D.USD.EUR.SP00.A | Zone euro | USD/EUR |
| EUR/CNY | D.CNY.EUR.SP00.A | Zone euro | CNY/EUR |

**Comext** : dataset `ds-045409`. `freq=M`, `reporter=FR`, `partner=WORLD`, `flow=1` (import), `product=code`. Deux requêtes, `VALUE_IN_EUROS` et `QUANTITY_IN_100KG`. Valeur €/t = valeur EUR / (quantité en unités de 100 kg / 10). Les agrégats WORLD et HS6 sont utilisés tels quels; on ne somme pas les pays ni les subdivisions. Les séries n'isolent pas le grade alimentaire, vierge ou recyclé. Il faut contrôler la composition et les anomalies de masse. Source : Eurostat, [DS-045409](https://ec.europa.eu/eurostat/databrowser/view/ds-045409/default/table?lang=fr), [documentation Comext](https://ec.europa.eu/eurostat/en/web/user-guides/data-browser/api-data-access/api-getting-started/comext-database).

**Eurostat PPI** : `sts_inppd_m`, `freq=M`, `indic_bt=PRC_PRR_DOM`, `s_adj=NSA`, `unit=I21`, `geo=EU27_2020`, `nace_r2=code`. Source : [Eurostat PPI](https://ec.europa.eu/eurostat/databrowser/view/sts_inppd_m/default/table?lang=fr). [API Statistics](https://ec.europa.eu/eurostat/en/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/api-statistics). [Droits de réutilisation](https://ec.europa.eu/eurostat/help/copyright-notice).

**Brent** : [EIA via FRED, DCOILBRENTEU](https://fred.stlouisfed.org/series/DCOILBRENTEU); téléchargement de CSV graphique `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU&cosd=2021-01-01`. Les données de cette série sont indiquées comme domaine public avec citation demandée par FRED. Pas d'API FRED avec clé dans cette version.

**Devises** : [BCE, documentation API](https://data.ecb.europa.eu/help/api/data-examples). Endpoint `https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata&startPeriod=2021-01-01`. Les taux sont exprimés en unités de devise pour un euro.

Les séries manquantes ne doivent pas être remplacées par une autre zone, une autre base ou une autre matière sans changer leur nom et définition. Les données Eurostat peuvent être révisées; le site conserve les flags disponibles et l'historique Git permet de retrouver les versions antérieures.

## 5. Modifier le site

- `site/index.html` : texte, sections, structure.
- `site/style.css` : couleur, police, mise en page responsive. Variables de couleur au début du fichier.
- `site/app.js` : affichage, calculs, filtre, graphique SVG, comparaison base 100, alertes et export. Aucun service externe de graphique, aucune dépendance JavaScript.
- `sources.json` : liste des séries et paramètres. Ajouter une entrée en dupliquant une entrée du même `provider` (`ppi`, `comext`, `fred`, `ecb`). Donner un `id` unique; vérifier le code et son unité avant de publier. `stale_days` définit le délai d'alerte sur l'âge de la période d'observation; adapter à la cadence réelle. `start` vaut `2021-01-01`. Un changement de provider, code, zone, unité ou fréquence invalide le cache antérieur.
- `collecte.py` : ajouter un nouveau fournisseur si nécessaire; les fonctions doivent renvoyer une liste de `{date, value, flag}`. Ne pas ajouter un scraping d'un site payant ou d'un site dont les droits de republication ne sont pas vérifiés.
- `.github/workflows/actualisation.yml` : horaire et déploiement. Par exemple `cron: '30 8 * * *'`, `timezone: 'Europe/Paris'` pour 8 h 30.
- `tests/test_collecte.py` : tests de calcul et format, incluant la conservation du cache.

Après modification via le web, **Commit changes**. Le workflow se déclenche sur les modifications de code; sinon le lancer manuellement depuis Actions. Pour réduire le nombre de commits, ne pas éditer les fichiers générés de `site/data` à la main. Le fichier `market.js` est une version JavaScript du JSON pour que le site fonctionne aussi en local sans serveur.

## 6. Tester sur ton ordinateur (facultatif)

Si Python 3.11+ est disponible, ouvrir Terminal sur Mac ou PowerShell sur Windows. Aller dans le dossier du projet (par exemple `cd ~/Downloads/packaging-market-monitor` sur Mac; adapter le chemin). Exécuter :

```bash
python3 -m unittest discover -s tests -v
python3 collecte.py
python3 -m http.server 8000 --directory site
```

Sur Windows, remplacer `python3` par `py` si nécessaire. Ouvrir `http://localhost:8000/` dans ton navigateur. Ctrl+C arrête le serveur. On peut aussi simplement ouvrir `site/index.html` dans le navigateur (les données JavaScript sont locales). Ne pas exécuter `collecte.py --init` sur une base déjà alimentée : cette option efface le cache et produit des fichiers vides.

## 7. Diagnostic

| Problème | Action |
|---|---|
| Le bouton Run workflow n'apparaît pas | Vérifier le fichier `.github/workflows/actualisation.yml`, la branche main et l'activation d'Actions. |
| Publication impossible / Pages not enabled | Settings > Pages > Source : GitHub Actions, puis relancer. |
| Erreur 403 à `git push` | Vérifier permissions Actions et protection de main. Demander autorisation si nécessaire. |
| `non-fast-forward` au push | Une modification concurrente du dépôt est intervenue. Relancer le workflow depuis main. |
| Le site apparaît vide | Actions > dernier run > collecte > logs. Vérifier la présence de `site/data/market.js` non vide et les erreurs réseau. |
| Une série est indisponible | Cliquer sur la matière pour lire l'erreur. Contrôler le code, la zone, la période et les dimensions dans le Data Browser officiel. Certaines combinaisons peuvent être non diffusées. Ne pas remplacer une observation manquante par un chiffre inventé. |
| Erreur HTTP 429 ou 5xx | L'API est temporairement saturée/indisponible. Le script réessaie et garde le cache s'il existe. Relancer ultérieurement; réduire la concurrence si nécessaire. |
| Eurostat répond sans données / extraction asynchrone | Vérifier les filtres de `sources.json` et les URLs construites dans `collecte.py`, puis utiliser le Query Builder officiel pour confirmer la combinaison. |
| Les prix ne changent pas depuis plusieurs semaines | Vérifier la cadence (mensuelle pour la plupart des matières) et la date d'observation. C'est normal si aucune nouvelle période n'a été publiée. |
| La date de collecte ne change plus | Vérifier Actions, éventuelle désactivation des tâches planifiées et relancer manuellement. |
| Les anciennes valeurs restent affichées | L'API peut être en panne ou une série obsolète. Le statut cache/à vérifier et les alertes le signalent. |

## 8. Recette de mise en service

- [ ] Les 17 séries ont été vérifiées; les séries non diffusées sont explicitement signalées.
- [ ] PP, PE et carton : comparer une observation de chaque avec le Data Browser, et pour Comext vérifier le ratio valeur/masse.
- [ ] Brent et EUR/USD : date, valeur et unité correspondent aux sources.
- [ ] Vérifier 1 mois, 1 an, comparateur base 100 et export Excel CSV.
- [ ] Contrôler les runs manuels et le premier run planifié. Vérifier que la date de collecte change.
- [ ] Vérifier que le dépôt ne contient aucune donnée interne ni secret.
- [ ] Faire valider l'outil et sa méthodologie par le service achats et, pour l'usage professionnel, la DSI.

## 9. Évolutions conseillées

Après validation de V1 : ajouter PEBDL, autres grades PET, testliner et autres qualités de papier via codes douaniers vérifiés; ajouter des indices INSEE plus précis; connecter des sources professionnelles sous licence via secrets GitHub ou hébergement interne; développer alertes e-mail/Teams; importer clauses contractuelles et budgets uniquement dans une instance privée approuvée. Le code actuel ne contient ni accès aux données payantes, ni authentification, ni envoi automatique de mails, ni module d'achat fournisseur.
