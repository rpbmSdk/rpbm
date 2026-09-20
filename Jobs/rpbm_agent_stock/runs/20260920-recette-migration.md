# Recette migration champs natifs — https://rpbm-pre-prod-37939198.dev.odoo.com

Date : 2026-09-20 12:41
Verdict : **FAIL** (29 PASS, 1 WARN, 1 FAIL, 0 NOT_RUN)

| Statut | Contrôle | Détail |
|---|---|---|
| `PASS` | version du module | 17.0.260921.5 (attendu 17.0.260921.5) |
| `PASS` | champs natifs crm.lead | 19 présents |
| `PASS` | champs natifs sale.order | 7 présents |
| `PASS` | champs natifs sale.order.line | 2 présents |
| `PASS` | champs natifs fleet.vehicle | 2 présents |
| `PASS` | champs natifs product.template | 3 présents |
| `PASS` | champs natifs product.product | 1 présents |
| `PASS` | champs natifs account.move | 2 présents |
| `PASS` | champs natifs stock.picking | 1 présents |
| `PASS` | crm.lead rpbm_license_plate vs x_studio_field_NVioD | 10305 / 10305 remplis (100%) |
| `PASS` | crm.lead rpbm_vehicle_brand_id vs x_studio_field_KyCjB | 10264 / 10264 remplis (100%) |
| `PASS` | crm.lead rpbm_vehicle_model_id vs x_studio_field_ZhaeY | 10184 / 10194 remplis (100%) |
| `PASS` | crm.lead rpbm_vin vs x_studio_field_PfJlB | 5908 / 5908 remplis (100%) |
| `PASS` | crm.lead rpbm_fuel_type vs x_studio_field_TAhpP | 9818 / 9818 remplis (100%) |
| `PASS` | crm.lead rpbm_vehicle_detail_model vs x_studio_field_i8fWl | 9930 / 9930 remplis (100%) |
| `FAIL` | crm.lead rpbm_first_registration_date vs x_studio_field_Eh6Wd | 5352 / 9559 remplis (56%) |
| `PASS` | crm.lead rpbm_part_type vs x_studio_field_eENQz | 10187 / 10187 remplis (100%) |
| `PASS` | crm.lead rpbm_eurocode_base vs x_studio_field_ORIyy | 9304 / 9304 remplis (100%) |
| `PASS` | crm.lead rpbm_eurocode vs x_studio_field_NwRik | 9592 / 9592 remplis (100%) |
| `PASS` | crm.lead rpbm_vsf_designation vs x_studio_field_j8eh3 | 8102 / 8102 remplis (100%) |
| `PASS` | crm.lead rpbm_vsf_stock vs x_studio_field_BKtpw | 7381 / 7538 remplis (98%) |
| `PASS` | crm.lead rpbm_constructor_reference vs x_studio_field_MNzfJ | 3572 / 3572 remplis (100%) |
| `PASS` | crm.lead rpbm_intervention_location vs x_studio_lieu_intervention | 4577 / 4577 remplis (100%) |
| `PASS` | sale.order miroir immatriculation | 7206 / 7206 |
| `PASS` | sale.order.line prix X'Glass natif | 5079 / 5079 |
| `PASS` | product.template.rpbm_eurocode | 3229 produits |
| `PASS` | fleet.vehicle FQ581EN | détail='RENAULT CLIO V PHASE 1 - 5P 2019-04-> 1.5DCI 85 FAP' MEC=2020-06-01 énergie=diesel |
| `PASS` | fleet.vehicle GH915QH | détail='PEUGEOT 3008 II (P84) PHASE 2 - 5P 2020-09->2024-03 1.2i TURBO 130 FAP' MEC=2022-07-01 énergie=gasoline |
| `WARN` | champs créés par l'ancien module supprimés | conservés (référencés ou erreur, voir journal Odoo.sh) : ['sale.order.x_rpbm_vehicle_brand_id', 'sale.order.x_rpbm_vehicle_model_id', 'crm.lead.x_rpbm_vehicle_brand_id', 'crm.lead.x_rpbm_vehicle_model_id', 'sale.order.x_studio_vehicle_id', 'crm.lead.x_studio_vehicle_id', 'product.template.x_studio_eurocode', 'product.template.x_studio_largeur_mm', 'product.template.x_studio_longueur_mm'] |
| `PASS` | marque native = marque Studio (échantillon 25) | identiques |
| `PASS` | verrou portail libre |  |
