# Champs — `sale.order`

Modèle porteur de l'Ordre de Vente. Les champs eurocode/immatriculation sont des champs `related` pointant vers l'Opportunité liée (`opportunity_id`) — voir [crm-lead.md](crm-lead.md) pour les champs source.

| Champ | Type | Related → | Origine | Rôle |
|---|---|---|---|---|
| `x_studio_immatriculation_` | char | `opportunity_id.x_studio_field_NVioD` | Studio (existant) | Immatriculation |
| `x_studio_vehicle_id` | many2one → `fleet.vehicle` | — | `pre_init_hook` (nouveau) | Véhicule Odoo lié, lié à celui de la piste |
| `x_studio_categorie_xglass` | char | — | `pre_init_hook` (nouveau) | Catégorie X'Glass, liée à celle de la piste |
| `x_studio_base_eurocode` | char | `opportunity_id.x_studio_field_ORIyy` | Studio (existant) | Base Eurocode — nom technique différent de celui de la piste, voir [crm-lead.md](crm-lead.md#structure-des-3-champs-eurocode) |
| `x_studio_eurocode_joint` | char | `opportunity_id.x_studio_eurocode_joint` | Studio (existant) | Eurocode du joint |

Note : `x_studio_vehicle_id`/`x_studio_categorie_xglass` sur `sale.order` sont des champs **indépendants** (pas `related`) — ils sont écrits séparément par le widget lors de la confirmation, pas automatiquement synchronisés depuis la piste liée.

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
