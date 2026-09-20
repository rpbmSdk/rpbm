# Champs — `sale.order`

Modèle porteur de l'Ordre de Vente. Tous les champs `rpbm_*` du devis sont des miroirs `related`
vers `opportunity_id.rpbm_*` (`models/sale_order.py`), **écrivables** : une valeur saisie ou écrite
par le widget depuis le devis remonte à l'opportunité, qui reste la source de vérité. Ils portent
les mêmes noms que sur `crm.lead`, ce qui permet au widget d'utiliser une seule table de champs.

| Champ | Stocké | Rôle |
|---|---|---|
| `rpbm_vehicle_id`, `rpbm_vehicle_brand_id`, `rpbm_vehicle_model_id`, `rpbm_license_plate` | oui (recherche, regroupement) | identité du véhicule |
| `rpbm_vin`, `rpbm_fuel_type`, `rpbm_vehicle_detail_model`, `rpbm_first_registration_date` | non | détail du véhicule |
| `rpbm_xglass_category`, `rpbm_part_type`, `rpbm_eurocode_base`, `rpbm_eurocode`, `rpbm_vsf_designation`, `rpbm_vsf_stock`, `rpbm_constructor_reference` | non | pièce et article VSF principal |
| `rpbm_intervention_location` | non | lieu d'intervention (préremplissage du transporteur) |
| `rpbm_xglass_piece_id`, `rpbm_piece_oe_id`, `rpbm_piece_am_id` | non | restauration des sélections du widget |
| `carrier_id` | natif `delivery` | mode de remise et route logistique |

Les miroirs Studio historiques du devis (`x_studio_immatriculation_`, `x_studio_pice_concerne`,
`x_studio_base_eurocode`, `x_studio_eurocode_complet`, `x_studio_vsf_*`, marque/modèle, VIN…)
restent alimentés : ils sont `related` vers les champs Studio de l'opportunité, eux-mêmes
synchronisés depuis les natifs. Aucune synchronisation n'est nécessaire sur `sale.order`.

## Transporteur

`views/sale_order_carrier_views.xml` affiche `carrier_id` sous le client avec le libellé
« Transporteur / mode de remise » (création et ouverture rapide interdites, lecture seule sur une
vente confirmée, annulée ou verrouillée). À la création d'un devis lié à une opportunité,
`rpbm_intervention_location` préremplit le transporteur : `galleria` → « Retrait / pose
Galleria », `genipa` → « Retrait / pose Genipa », `domicile` → « Pose sur site (Camion) » ; les
lieux « lavage » et les transporteurs absents ou ambigus restent à choisir manuellement, sans
erreur. Le changement d'opportunité ne préremplit qu'un nouveau brouillon vide. `action_confirm()`
exige un transporteur.

## Vue

L'onglet « Véhicule (X'Glass) » (`views/sale_order_views.xml`), visible seulement si une
opportunité est liée, affiche le widget et les miroirs natifs ; les lignes de devis portent les
colonnes invisibles `rpbm_xglass_price` et `rpbm_labor_operation_key`.

## Lu/écrit par

- Écriture : [7 — Confirmation sur Ordre de Vente](../../fonctionnel/workflow/07-confirmation-sale-order.md)
- Création produit et lignes : [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md), [sale-order-line.md](sale-order-line.md)
