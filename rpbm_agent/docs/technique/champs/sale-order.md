# Champs — `sale.order`

Modèle porteur de l'Ordre de Vente. Les champs eurocode/immatriculation sont des champs `related` pointant vers l'Opportunité liée (`opportunity_id`) — voir [crm-lead.md](crm-lead.md) pour les champs source.

| Champ | Type | Related → | Origine | Rôle |
|---|---|---|---|---|
| `x_studio_immatriculation_` | char | `opportunity_id.x_studio_field_NVioD` | Studio (existant) | Immatriculation |
| `x_studio_vehicle_id` | many2one → `fleet.vehicle` | `opportunity_id.x_studio_vehicle_id` | `pre_init_hook` + migration | Véhicule Odoo lié, recopié depuis la piste |
| `x_studio_categorie_xglass` | char | `opportunity_id.x_studio_categorie_xglass` | `pre_init_hook` + migration | Catégorie X'Glass, recopiée depuis la piste |
| `x_studio_pice_concerne` | selection | `opportunity_id.x_studio_field_eENQz` | Studio (existant) | Pièce concernée, valeur de la sélection X'Glass |
| `x_studio_base_eurocode` | char | `opportunity_id.x_studio_field_ORIyy` | Studio (existant) | Base Eurocode — nom technique différent de celui de la piste, voir [crm-lead.md](crm-lead.md#structure-des-3-champs-eurocode) |
| `x_studio_eurocode_joint` | char | `opportunity_id.x_studio_eurocode_joint` | Studio (existant) | Eurocode du joint |

Les deux champs X'Glass suivent la convention de l'instance : l'opportunité est la source et le devis les lit via des champs `related` stockés. La migration `17.0.260725.6` aligne les anciens champs indépendants en place uniquement s'ils sont vides : elle ne les supprime pas, car des vues peuvent les référencer pendant l'upgrade. Elle bloque l'upgrade au lieu d'écraser une valeur inattendue.

## Référentiel Fleet et article principal

Les nouveaux champs `x_rpbm_vehicle_*` sont des miroirs `related` stockés de
`opportunity_id.x_rpbm_vehicle_*` : marque, modèle, VIN, détail modèle,
énergie et date de première MEC. Ils remplacent dans les nouvelles vues et
documents les relations Studio marque/modèle obsolètes.

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

Affiché dans l'onglet "Véhicule (X'Glass)" ajouté par `views/sale_order_views.xml` (hérite de `sale.view_order_form`) : widget + `x_studio_vehicle_id` + `x_studio_categorie_xglass` uniquement — immatriculation/eurocode déjà visibles ailleurs sur ce formulaire, non dupliqués ici.

## Lu/écrit par

- Écriture : [7 — Confirmation sur Ordre de Vente](../../fonctionnel/workflow/07-confirmation-sale-order.md)
- Création produit : [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md)
