# Rôles achats et livraisons

## Règle métier

- **Yan (Yvan PAPUS, `rpbm004@gmail.com`) et Mickaël (Mickaël MOHAMED, `rpbm003@gmail.com`)**
  sont les acheteurs : eux seuls créent et valident les commandes fournisseurs.
- **Les autres vendeurs** doivent **voir** les achats et **effectuer les livraisons et
  réceptions**, sans pouvoir valider une commande d'achat.
- **Exception** : les administrateurs Margot ROBIN et Romain HAYOT gardent la validation des
  achats.
- Les vendeurs voient un achat depuis sa réception. Ils n'ont pas besoin du menu Achats.

## Matrice cible

| Utilisateur | Achats | Inventaire |
|---|---|---|
| Yvan, Mickaël | `purchase.group_purchase_manager` | `stock.group_stock_user` |
| Autres vendeurs (David, Hervyn, Yourie…) | aucun | `stock.group_stock_user` |
| Margot, Romain (admins) | manager (inchangé) | manager (inchangé) |

## Pourquoi ces groupes (Odoo 17)

- La société est en `po_double_validation = one_step`. Dans ce mode, **tout
  `purchase.group_purchase_user` peut confirmer** une commande (`_approval_allowed` dans
  `purchase/models/purchase_order.py`). Il ne faut donc jamais donner ce groupe à un vendeur.
- `purchase_stock/security/ir.model.access.csv` donne à `stock.group_stock_user` la **lecture
  seule** de `purchase.order` et `purchase.order.line`. Un vendeur Inventaire voit donc la
  commande liée à une réception et peut valider livraisons et réceptions, sans pouvoir
  confirmer d'achat.

## Audit pré-prod du 2026-09-28 (avant correction)

| Utilisateur | Achats | Inventaire |
|---|---|---|
| Romain, Margot (admins) | user + manager | user + manager |
| Mickaël, Yvan | aucun | aucun |
| David, Hervyn, Yourie | aucun | aucun |

Aucune `ir.rule`, ACL ou automatisation personnalisée sur les achats ou le stock.

## Automatisation (pré-prod puis production)

Les droits sont appliqués par le module `rpbm_agent` lors de sa mise à jour sur Odoo.sh :

- [`security/rpbm_groups.xml`](../../rpbm_agent/security/rpbm_groups.xml) :
  `sales_team.group_sale_salesman` implique `stock.group_stock_user`. Tout vendeur, actuel ou
  futur, reçoit l'Inventaire.
- [`migrations/17.0.260928.1/post-roles-achats.py`](../../rpbm_agent/migrations/17.0.260928.1/post-roles-achats.py) :
  ajoute Achats (manager) et Inventaire aux deux acheteurs, identifiés par login. Aucun droit
  n'est retiré. Pour changer d'acheteur, modifier la liste `BUYERS` et bumper la version.
