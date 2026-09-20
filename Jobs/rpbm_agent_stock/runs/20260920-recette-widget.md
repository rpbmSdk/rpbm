# Recette widget — vérification run 20260920 — https://rpbm-pre-prod-37939198.dev.odoo.com

Date : 2026-09-20 14:37
Verdict : **PASS** (37 PASS, 0 WARN, 0 FAIL, 0 NOT_RUN)

| Statut | Contrôle | Détail |
|---|---|---|
| `PASS` | W1 véhicule lié | [5, 'RENAULT/MEGANE/BF857CZ'] |
| `PASS` | W1 catégorie X'Glass | PARE-BRISE |
| `PASS` | W1 pièce concernée | windshield |
| `PASS` | W1 base eurocode | 7275A |
| `PASS` | W1 rpbm_eurocode (article principal) | 7275AGNMV1P |
| `PASS` | W1 rpbm_vsf_designation (article principal) | PARE-BRISE TEINTÉ VERT RENAULT MEGANE 3 COUPÉ CAPTEUR DE PLU |
| `PASS` | W1 identifiants de pièce | 4949205 / 4949205 / 3595524 |
| `PASS` | W1 rpbm_vehicle_brand_id dérivé du véhicule | [69, 'RENAULT'] |
| `PASS` | W1 rpbm_vehicle_model_id dérivé du véhicule | [174, 'RENAULT/MEGANE'] |
| `PASS` | W1 rpbm_vin dérivé du véhicule | VF1DZ1S0643866330 |
| `PASS` | W1 rpbm_fuel_type dérivé du véhicule | diesel |
| `PASS` | W1 base eurocode = référence | 7275A vs 7275A |
| `PASS` | W1 Studio x_studio_field_NVioD synchronisé | 'BF857CZ' vs natif 'BF857CZ' |
| `PASS` | W1 Studio x_studio_field_NwRik synchronisé | '7275AGNMV1P' vs natif '7275AGNMV1P' |
| `PASS` | W1 Studio x_studio_field_eENQz synchronisé | 'Pare-Brise' vs natif 'Pare-Brise' |
| `PASS` | W1 Studio x_studio_field_ORIyy synchronisé | '7275A' vs natif '7275A' |
| `PASS` | W1 Studio x_studio_field_j8eh3 synchronisé | 'PARE-BRISE TEINTÉ VERT RENAULT MEGANE 3 COUPÉ CAPTEUR DE PLUIE 08- MO 1.90' vs natif 'PARE-BRISE TEINTÉ VERT RENAULT MEGANE 3 COUPÉ CAPTEUR DE PLUIE 08- MO 1.90' |
| `PASS` | W1 Studio marque synchronisée | [8, 'RENAULT'] vs [69, 'RENAULT'] |
| `PASS` | Fleet plaque | BF857CZ |
| `PASS` | Fleet conducteur = client | [15488, 'RECETTE-20260920 Client'] |
| `PASS` | Fleet énergie native | diesel |
| `PASS` | Fleet VIN | VF1DZ1S0643866330 |
| `PASS` | Fleet détail modèle | RENAULT MEGANE III COUPE PHASE 1 - 3P 2008-11->2012-01 1.9DCI 130 FAP |
| `PASS` | produit VSF (par eurocode) | [2349] 7275AGNMV1P |
| `PASS` | prix fournisseur VSF | [(83.22, '2026-09-15')] |
| `PASS` | devis lié à W1 | [(7752, 'SO7753', 'sale')] |
| `PASS` | SO7753 transporteur prérempli | [3, 'Retrait / pose Galleria'] |
| `PASS` | SO7753 miroirs natifs | BF857CZ / [5, 'RENAULT/MEGANE/BF857CZ'] |
| `PASS` | SO7753 ligne article VSF | [('[7275AGNMV1P] PB VT RENAULT ME', 170.1, 113.4)] |
| `PASS` | SO7753 prix ligne = prix X'Glass × 1,5 | 170.1 vs 170.1 |
| `PASS` | SO7753 lignes main-d'œuvre | [(23, 1.9, 90.32)] |
| `PASS` | SO7753 MO 4949205:8783449 | produit 23 qté 1.9 prix 90.32 (tarif 90.32000000000001) |
| `PASS` | SO7753 confirmé | sale |
| `PASS` | SO7753 livraison générée | [5182, 5181] |
| `PASS` | livraison : véhicule reporté | [5, 'RENAULT/MEGANE/BF857CZ'] |
| `PASS` | W3 véhicule existant réutilisé | [4, 'RENAULT/CLIO/FQ581EN'] / Fleet [{'id': 4, 'vin_sn': 'VF1RJA00X64812285', 'driver_id': [14853, 'SOC CELTIKS LOCATION']}] |
| `PASS` | verrou portail libéré |  |


Manifeste : D:\git\rpbm\.paradigme\tmp\recette-20260920.json
