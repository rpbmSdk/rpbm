# Champs — `sale.order.line`

Lignes de devis créées par le widget depuis un devis lié à une opportunité (voir
[7 — Confirmation sur Ordre de Vente](../../fonctionnel/workflow/07-confirmation-sale-order.md)).
Le widget ne modifie jamais une ligne qu'il n'a pas créée pendant la dialog courante, sauf pour
retirer une ligne de main-d'œuvre qu'il a créée lors d'une session précédente (reconnue par sa
clé de provenance). Champs déclarés dans `models/sale_order.py`.

| Champ | Type | Rôle | Studio historique synchronisé |
|---|---|---|---|
| `rpbm_xglass_price` | float | Prix RPBM de l'article VSF (`articleVsf.prixVenteRPBM`). **Pilote le prix** : l'automatisation Studio « Tarif x glass » force `price_unit = x_studio_prix_x_glass × 1,5` (voir [cartographie/automatisations.md](../../../../docs/cartographie/automatisations.md)). Le widget ne renseigne jamais `price_unit`. | `x_studio_prix_x_glass` (double alimentation, dans les deux sens) |
| `rpbm_labor_operation_key` | char, `copy=False`, indexé | Provenance d'une ligne de main-d'œuvre : `"<id pièce X'Glass>:<id opération>"`. Interdit les doublons à la réouverture et limite le retrait aux lignes du widget. | — |

## Lignes article VSF

`addArticleToSaleOrder()` (`agent_widget_dialog_sale_order.js`) crée la ligne avec
`default_product_id` = produit trouvé/créé, `product_uom_qty = 1` et `rpbm_xglass_price`. Les
`onchange` Odoo calculent le reste (taxes, description) ; le mixin recopie le prix vers
`x_studio_prix_x_glass`, ce qui déclenche l'automatisation.

## Lignes de main-d'œuvre X'Glass

`addSelectedLaborOperations()` crée une ligne de service par opération cochée (taux T1/T2/T3
reconnu) : `default_product_id` = produit paramétré (`rpbm_agent.labor_product_t1/t2/t3`, voir
[configuration](../configuration.md#paramètres-système-requis)), `product_uom_qty` = durée
X'Glass en heures, `rpbm_labor_operation_key` = clé de provenance. Prix et taxes viennent du
produit Odoo. Une opération sans identifiant, sans durée positive ou sans taux reconnu reste non
ajoutable (`unavailableReason` renvoyé par `/getPieces`).
