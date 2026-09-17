# Champs — `sale.order`

## Sélections persistantes du widget

Les champs `x_rpbm_xglass_piece_id`, `x_rpbm_piece_oe_id` et
`x_rpbm_piece_am_id` sont des miroirs `related` stockés des champs de
l’opportunité liée. Le devis conserve ainsi le même contexte que le CRM.

Modèle porteur de l'Ordre de Vente. Les champs eurocode/immatriculation sont des champs `related` pointant vers l'Opportunité liée (`opportunity_id`) — voir [crm-lead.md](crm-lead.md) pour les champs source. Le mode logistique est porté par le champ natif `carrier_id`.

| Champ | Type | Related → | Origine | Rôle |
|---|---|---|---|---|
| `x_studio_immatriculation_` | char | `opportunity_id.x_studio_field_NVioD` | Studio (existant) | Immatriculation |
| `x_studio_vehicle_id` | many2one → `fleet.vehicle` | `opportunity_id.x_studio_vehicle_id` | `pre_init_hook` + migration | Véhicule Odoo lié, recopié depuis la piste |
| `x_studio_categorie_xglass` | char | `opportunity_id.x_studio_categorie_xglass` | `pre_init_hook` + migration | Catégorie X'Glass, recopiée depuis la piste |
| `x_studio_pice_concerne` | selection | `opportunity_id.x_studio_field_eENQz` | Studio (existant) | Pièce concernée, valeur de la sélection X'Glass |
| `x_studio_base_eurocode` | char | `opportunity_id.x_studio_field_ORIyy` | Studio (existant) | Base Eurocode — nom technique différent de celui de la piste, voir [crm-lead.md](crm-lead.md#structure-des-3-champs-eurocode) |
| `x_studio_eurocode_joint` | char | `opportunity_id.x_studio_eurocode_joint` | Studio (existant) | Eurocode du joint |
| `carrier_id` | many2one → `delivery.carrier` | — | `delivery` (natif) | Mode de remise et route logistique de la commande |

Les deux champs X'Glass suivent la convention de l'instance : l'opportunité est la source et le devis les lit via des champs `related` stockés. La migration `17.0.260725.6` aligne les anciens champs indépendants en place uniquement s'ils sont vides : elle ne les supprime pas, car des vues peuvent les référencer pendant l'upgrade. Elle bloque l'upgrade au lieu d'écraser une valeur inattendue.

## Référentiel Fleet, miroirs historiques et article principal

Le devis conserve `x_studio_vehicle_id` comme lien vers le véhicule Fleet. Le
lot AG01-01 ne crée plus les huit champs techniques `x_rpbm_vehicle_*` ; ceux
qui existeraient déjà dans une base ne sont ni supprimés, ni renommés, ni
migrés.

À la confirmation du dialogue, le véhicule Fleet est reporté dans les champs
historiques de l'opportunité, puis lu par les miroirs `related` du devis :

| Miroir historique du devis | Related → opportunité | Source Fleet indirecte |
|---|---|---|
| `x_studio_immatriculation_` | `x_studio_field_NVioD` | `license_plate` |
| `x_studio_many2one_field_rP62C` | `x_studio_field_KyCjB` | `model_id.brand_id.name` |
| `x_studio_many2one_field_DkgHx` | `x_studio_field_ZhaeY` | `model_id.name` |
| `x_studio_vin_` | `x_studio_field_PfJlB` | `vin_sn` |
| `x_studio_nergie_moteur` | `x_studio_field_TAhpP` | énergie Fleet supportée |
| `x_studio_dtails_modle` | `x_studio_field_i8fWl` | `x_studio_detail_model` |
| `x_studio_date_1re_mec` | `x_studio_field_Eh6Wd` | `x_studio_date_mec`, format `MM/YYYY` |

Une source vide, une énergie non supportée ou un manque de droits produit un
avertissement non bloquant et conserve la valeur historique existante. Une
correspondance de référentiel ambiguë produit également un avertissement, mais
la première correspondance est retenue. Le kilométrage n'est jamais écrit.
Sans opportunité liée, aucune écriture dans ces champs `related` n'est
préparée. Les champs Fleet réels et `x_rpbm_vsf_constructor_reference` restent
inchangés.

Le widget peut contenir plusieurs articles VSF. L'utilisateur désigne un seul
article principal ; son Eurocode complet, sa désignation et son stock sont
écrits via les champs `related` existants du devis vers l'opportunité. La
référence constructeur utilise le miroir
`x_rpbm_vsf_constructor_reference`. Les prix restent exclusivement pilotés par
les automatisations et les lignes de commande.

## `product.product`/`product.supplierinfo` créés depuis un article VSF

Lors de la création d'un article (bouton "Créer" sur un article VSF affiché), le widget crée :
- un `product.product` (voir [product-product.md](product-product.md))
- un `product.supplierinfo` associé (fournisseur VSF, prix d'achat remisé)

Puis une ligne de commande (`sale.order.line`) est ajoutée via le bouton "Ajouter" (indépendant du bouton "Confirm" de la fenêtre — voir [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md)).

## Vue

L'onglet "Véhicule (X'Glass)" ajouté par `views/sale_order_views.xml` affiche le
widget, `x_studio_vehicle_id` et `x_studio_categorie_xglass`. Les miroirs
historiques nécessaires à la préparation peuvent être chargés dans un groupe
invisible ; le groupe d'identité Fleet en doublon n'est pas affiché.

La vue versionnée `views/sale_order_carrier_views.xml` affiche `carrier_id` sous
le client avec le libellé « Transporteur / mode de remise ». Le champ interdit la
création ou l'ouverture rapide d'un transporteur et devient en lecture seule sur
une vente confirmée, annulée ou verrouillée. Il n'est pas `required` dans le
formulaire : le contrôle métier est effectué par `action_confirm()`.

Lorsqu'un nouveau devis est lié à une opportunité, le module peut reprendre le
lieu historique `x_studio_lieu_intervention` : GALLERIA, GENIPA et DOMICILE sont
associés aux trois transporteurs de l'architecture stock. Les valeurs LAVAGE,
les valeurs inconnues et les transporteurs manquants restent à choisir
manuellement. Aucun transporteur n'est créé et aucun devis existant n'est
réécrit automatiquement.

## Lu/écrit par

- Écriture : [7 — Confirmation sur Ordre de Vente](../../fonctionnel/workflow/07-confirmation-sale-order.md)
- Création produit : [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md)
