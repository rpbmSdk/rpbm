# Champs — `sale.order.line`

[Index](../../README.md) › [Champs Odoo par modèle](README.md) › Champs — `sale.order.line`

Lignes de devis créées par le widget depuis un devis lié à une opportunité (voir
[7 — Confirmation sur Ordre de Vente](../../fonctionnel/workflow/07-confirmation-sale-order.md)).
Le widget ne modifie jamais une ligne qu'il n'a pas créée pendant la dialog courante, sauf pour
retirer une ligne de main-d'œuvre qu'il a créée lors d'une session précédente (reconnue par sa
clé de provenance). Champs déclarés dans `models/sale_order.py`.

| Champ | Type | Rôle | Studio historique synchronisé |
|---|---|---|---|
| `rpbm_xglass_price` | float | Barème X'Glass HT de la ligne (libellé « Barème X'Glass HT » depuis `17.0.261015.1`, auparavant « Prix X'Glass »), colonne visible et modifiable de la liste des lignes, avant le prix unitaire, en lecture seule une fois la ligne facturée (`qty_invoiced > 0`). Le widget y écrit, pour l'article VSF **principal**, le Prix XGlass HT de la pièce d'origine (`rpbm_xglass_piece_price` du dossier, [VD-08](../../validations-metier.md#historique-des-décisions)) ; plus jamais `prixVenteRPBM` (VM-10 remplacé) ; rien sans pièce d'origine. Une ligne saisie à la main peut aussi le porter. **Pilote le prix** : l'automatisation Studio « Tarif x glass » force `price_unit = x_studio_prix_x_glass × 1,5` (voir [cartographie/automatisations.md](../../../../docs/cartographie/automatisations.md)). Le module optionnel `rpbm_pricing` garde cette règle quand il est installé (majoration réservée aux dossiers assurance si son paramètre `rpbm_pricing.rule8_insurance_only` l'exige) : voir [Interaction avec rpbm_pricing](../rpbm-pricing.md). Le widget ne renseigne jamais `price_unit`. | `x_studio_prix_x_glass` (double alimentation, dans les deux sens ; depuis `17.0.261013.1`, une valeur Studio saisie l'emporte sur un natif vide, voir [configuration](../configuration.md#priorité-en-cas-de-double-saisie)). Sa colonne Studio « Prix XGlass » est renommée « Prix XGlass (ancien) » et masquée par `Jobs/rpbm_agent_stock/studio_views.py` |
| `rpbm_supplier_price` | float, calculé stocké modifiable, `copy=True` | Prix fournisseur net de la pièce (« Prix fournisseur (net) », colonne affichée par défaut). Le widget y écrit le coût VSF net (`prixVenteRPBM`) de l'article VSF ajouté ; à défaut (ligne manuelle, autre fournisseur), calcul depuis l'article : `_select_seller` (fournisseur prioritaire par séquence, puis son prix le plus bas valable à la date du devis), prix net de remise converti dans la devise du devis. Recalculé **seulement** au changement d'article : une saisie ou la valeur du widget survit à la quantité. Jamais lu par un calcul de prix de vente (P-10, P-44). Lignes antérieures à `17.0.261015.1` : vides (colonne créée par migration, sans recalcul). | — |
| `rpbm_supplier_id` | many2one `res.partner`, même calcul | Fournisseur de ce prix (colonne masquable, masquée par défaut). Sera relié au « fournisseur prévu » (P-36, Q-20). | — |
| `rpbm_labor_operation_key` | char, `copy=False`, indexé | Provenance d'une ligne de main-d'œuvre : `"<id pièce X'Glass>:<id opération>"`. Interdit les doublons à la réouverture et limite le retrait aux lignes du widget. | — |

## Lignes article VSF

`addArticleToSaleOrder()` (`agent_widget_dialog_sale_order.js`) crée la ligne avec
`default_product_id` = produit trouvé/créé, `product_uom_qty = 1`, `rpbm_xglass_price` (barème de la
pièce d'origine, article principal seulement) et `rpbm_supplier_price` / `rpbm_supplier_id` (net VSF,
renvoyés par `/createProduct`). Les `onchange` Odoo calculent le reste (taxes, description) ; le
mixin recopie le barème vers `x_studio_prix_x_glass`, ce qui déclenche l'automatisation. La ligne ne porte pas de clé de
provenance : `removeArticleFromSaleOrder()` la retrouve par son produit parmi les lignes du devis,
pour les seuls articles ajoutés pendant la dialog courante (R28, lot correctif `17.0.261006.1`, voir
[frontend](../frontend.md#ligne-de-devis-ajoutée-par-le-widget-r28)).

## Lignes de main-d'œuvre X'Glass

`addSelectedLaborOperations()` crée une ligne de service par opération cochée (taux T1/T2/T3
reconnu) : `default_product_id` = produit paramétré (`rpbm_agent.labor_product_t1/t2/t3`, voir
[configuration](../configuration.md#paramètres-système-requis)), `product_uom_qty` = durée
X'Glass en heures, `rpbm_labor_operation_key` = clé de provenance. Prix et taxes viennent du
produit Odoo. Une opération sans identifiant, sans durée positive ou sans taux reconnu reste non
ajoutable (`unavailableReason` renvoyé par `/getPieces`).

Les opérations proposées viennent de la pièce chargée par X'Glass ou, depuis le correctif du 2026-10-07 (`17.0.261007.1`), de `rpbm_xglass_labor_operations` ([`crm.lead`](crm-lead.md)) tant que X'Glass n'est pas chargé. Dans ce second cas, le produit de service est résolu à l'ajout, par taux, avec les paramètres `rpbm_agent.labor_product_*` courants (`/rpbm_labor_products`), et non repris de l'enregistrement.

---
Précédent : [Champs — `sale.order`](sale-order.md) · Suivant : [Champs — `fleet.vehicle`](fleet-vehicle.md)

Voir aussi : [7 — Confirmation sur Ordre de Vente (`sale.order`)](../../fonctionnel/workflow/07-confirmation-sale-order.md) · [Automatisations (`base.automation` / `ir.actions.server`)](../../../../docs/cartographie/automatisations.md) · [Interaction avec rpbm_pricing](../rpbm-pricing.md) · [Configuration & déploiement](../configuration.md) · [Frontend (OWL)](../frontend.md) · [Champs — `crm.lead`](crm-lead.md)
