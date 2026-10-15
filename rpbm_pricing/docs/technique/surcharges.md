# Surcharges

[RPBM Pricing](../../README.md) › [Documentation](../README.md) › [Manuel technique](README.md) › Surcharges

Quatre méthodes Odoo sont surchargées. Chacune l'est pour une raison précise ; aucune ne change une
signature.

| Méthode | Fichier | Raison |
|---|---|---|
| `sale.order.line._compute_price_unit` | [`models/sale_order_line_rule8.py:153-166`](../../models/sale_order_line_rule8.py) | une quantité modifiée ne ramène plus au `list_price` |
| `stock.rule._get_partner_id` | [`models/stock_rule.py:7-10`](../../models/stock_rule.py) | le client livré n'est jamais fournisseur (P-36) |
| `stock.rule._make_po_get_domain` | [`models/stock_rule.py:12-14`](../../models/stock_rule.py) | un brouillon bateau ne reçoit pas les besoins (P-47) |
| `sale.order.line._prepare_invoice_line` | [`models/sale_order_line_invoice.py:7-12`](../../models/sale_order_line_invoice.py) | recopier le barème sur la facture (IMP-10) |

## `sale.order.line._compute_price_unit`

**Problème.** L'automatisation Studio de la règle 8 ne repasse que lorsque le Prix X'Glass change. Mais le
natif `_compute_price_unit` dépend aussi de la quantité : à chaque changement de quantité, il ramène le prix
au `list_price` de l'article et efface la majoration.

**Surcharge.** Si la garde est active ([`models/sale_order_line_rule8.py:117-121`](../../models/sale_order_line_rule8.py)),
chaque ligne reçoit `_rpbm_rule8_value()` quand :

- la ligne n'est pas dans `_lines_without_price_recomputation()` (lignes d'option de `sale_management`,
  `/root/git/odoo17/odoo/addons/sale_management/models/sale_order_line.py:39-44`) ;
- elle n'est pas facturée (`qty_invoiced <= 0`) ;
- `_rpbm_rule8_value()` ne renvoie pas `None`.

Les lignes ainsi traitées sont retirées du recordset passé à `super()` ; les autres suivent le natif
(`models/sale_order_line_rule8.py:166`). Garde active signifie : automatisation de la règle 8 active et valeur
de l'action égale à la garde. Sans cela, le comportement est strictement celui d'Odoo.

**Conséquence.** Un prix saisi à la main revient à barème × coefficient si la quantité change (le natif le
ramenait au `list_price`). Une ligne déjà facturée n'est pas recalculée.

## `stock.rule._get_partner_id`

**Problème.** Le natif renvoie `values.get("supplierinfo_name")` ou, à défaut, le partenaire du groupe
d'approvisionnement, donc le client livré (`/root/git/odoo17/odoo/addons/purchase_stock/models/stock_rule.py:340-341`).
Quand le client est aussi fournisseur, la demande de prix lui était adressée.

**Surcharge.** Renvoie `values.get("supplierinfo_name")` ou un partenaire vide. `_select_seller` prend alors le
premier prix fournisseur valable par séquence, soit VSF en séquence 1. Le natif appelle cette méthode à
`purchase_stock/models/stock_rule.py:63`.

## `stock.rule._make_po_get_domain`

**Problème.** Une demande de prix déjà créée pour un envoi par bateau ne doit plus grossir : les besoins
automatiques s'y regroupaient.

**Surcharge.** Ajoute `("rpbm_transport_mode", "!=", "boat")` au domaine du natif
(`purchase_stock/models/stock_rule.py:305`, appelé en `:83`). Un brouillon bateau n'est plus candidat, une
autre demande est créée. Seuls les brouillons sont concernés : le natif filtre déjà `state = draft`.

## `sale.order.line._prepare_invoice_line`

**Problème.** Le contrôle IMP-10 demande de garder le barème X'Glass sur la facture, sans jamais
l'imprimer.

**Surcharge.** Appelle `super()` puis ajoute `rpbm_xglass_price` pour les lignes qui ne sont pas des
sections ou des notes (`not self.display_type`). Le champ de `account.move.line` n'a ni vue ni impression
(test : [`tests/test_invoice.py`](../../tests/test_invoice.py), le rendu HTML de `account.account_invoices`
ne contient ni le barème ni « remise fournisseur »).

## Ce qui n'est pas surchargé

- `sale.order.line.price_unit` : aucune dépendance ajoutée, la remise n'est pas touchée.
- `_compute_pricelist_id` : intact, contrainte de l'itération 2.
- Le déclencheur et le domaine de l'automatisation Studio : seule la valeur de l'action 1510 change, voir
  [Garde de la règle 8](regle-8.md).

Voir aussi : [Colisage VSF](colisage.md)

---
Précédent : [Modèles et champs](modeles.md) · Suivant : [Garde de la règle 8](regle-8.md)
