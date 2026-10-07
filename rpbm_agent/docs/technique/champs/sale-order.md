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
| `rpbm_xglass_vehicle_id`, `rpbm_xglass_piece_id`, `rpbm_piece_oe_id`, `rpbm_piece_am_id` | non | restauration des sélections du widget : le devis ouvert par « Créer un devis » retrouve ainsi le véhicule X'Glass, la pièce et la pièce AM de l'opportunité, une fois X'Glass chargé (« Charger X'Glass », lot E2) |
| `rpbm_xglass_piece_label` | non | libellé de la pièce X'Glass (lot E2, `17.0.261006.2`) : lu par l'encart « Dossier », seul affichage de la pièce tant que X'Glass n'est pas chargé ; miroir `related` écrivable comme les autres, sans équivalent Studio |
| `rpbm_xglass_labor_operations` | non | main-d'œuvre X'Glass de la pièce (correctif `17.0.261007.1`, JSON) : lue par la section « 4. Main d'œuvre X'Glass » du devis ouvert sans X'Glass ; miroir `related` écrivable comme les autres, sans équivalent Studio. Sans opportunité liée, rien ne peut y être enregistré |
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

`views/sale_order_views.xml` hérite de trois vues standard :

- **formulaire** : l'onglet « Véhicule (X'Glass) », visible seulement si une opportunité est liée,
  affiche le widget et les miroirs natifs ; les lignes de devis portent les colonnes invisibles
  `rpbm_xglass_price` et `rpbm_labor_operation_key` ;
- **liste** (`sale.sale_order_tree`, donc aussi les listes devis et commandes) : immatriculation,
  marque et modèle après le client ;
- **recherche** (`sale.view_sales_order_filter`, donc aussi les recherches devis et commandes) :
  immatriculation, marque, modèle, VIN, eurocode et le champ combiné « Véhicule »
  (immatriculation, VIN, marque ou modèle) ; regroupements par marque et modèle. VIN et eurocode,
  non stockés, sont cherchés à travers l'opportunité.

Le bouton et les champs natifs dans l'en-tête Studio du devis sont ajoutés par le script
`studio_views.py` (voir [`Jobs/rpbm_agent_stock`](../../../../Jobs/rpbm_agent_stock/README.md)),
qui déplace aussi les anciens champs doublés dans un onglet « Anciens champs » (visible avec une
opportunité liée).

## Lu/écrit par

- Création du devis depuis l'opportunité : [6 — « Créer un devis »](../../fonctionnel/workflow/06-confirmation-crm-lead.md#créer-un-devis-lot-e1)
- Écriture et ouverture automatique du dialog : [7 — Confirmation sur Ordre de Vente](../../fonctionnel/workflow/07-confirmation-sale-order.md)
- Création produit et lignes : [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md), [sale-order-line.md](sale-order-line.md)
