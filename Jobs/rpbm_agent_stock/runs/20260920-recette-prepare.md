# Recette widget — préparation run 20260920 — https://rpbm-pre-prod-37939198.dev.odoo.com

Date : 2026-09-20 12:49
Verdict : **PASS** (13 PASS, 1 WARN, 0 FAIL, 0 NOT_RUN)

| Statut | Contrôle | Détail |
|---|---|---|
| `PASS` | version du module | 17.0.260921.6 (attendu 17.0.260921.6) |
| `PASS` | identifiants portails configurés | 4/4 clés |
| `PASS` | produits main-d'œuvre T1/T2/T3 | 24=83.87, 23=90.32000000000001, 113=97.7 |
| `PASS` | fournisseur VSF 5708 |  |
| `PASS` | transporteurs | {'Retrait / pose Galleria': 3, 'Retrait / pose Genipa': 4, 'Pose sur site (Camion)': 5} |
| `PASS` | plaque BF857CZ sans véhicule Fleet | [] |
| `PASS` | plaque FQ581EN avec véhicule Fleet | [{'id': 4, 'driver_id': [14853, 'SOC CELTIKS LOCATION']}] |
| `PASS` | verrou portail libre |  |
| `PASS` | attendus de référence BF857CZ | lead 12631 base=7275A eurocode=7275AGNMV1P marque=[69, 'RENAULT'] |
| `PASS` | attendus de référence FQ581EN | lead 12630 base=7310A eurocode=7310AGACMVZ marque=[69, 'RENAULT'] |
| `PASS` | opportunité W1 créée | id 12634 (BF857CZ) |
| `PASS` | opportunité W3 créée | id 12635 (FQ581EN) |
| `PASS` | double alimentation Studio à la création | {'id': 12634, 'x_studio_field_NVioD': 'BF857CZ', 'x_studio_lieu_intervention': 'GALLERIA'} |
| `WARN` | session web (profil) | refusée (odoo.exceptions.AccessDenied) : le mot de passe du profil n'ouvre pas de session interactive (clé API ?) — connexion manuelle requise dans le navigateur |


Identifiants créés : {"partner": 15488, "W1": 12634, "W3": 12635}
