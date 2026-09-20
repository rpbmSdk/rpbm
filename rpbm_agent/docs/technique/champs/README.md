# Champs Odoo par modèle

Référence des champs lus ou écrits par `rpbm_agent`, un fichier par modèle porteur. Depuis la
version `17.0.260921.1`, le module ne crée que des **champs natifs** préfixés `rpbm_` (déclarés
dans `models/*.py`) ; les champs Studio historiques de l'instance ne sont plus cités que dans la
table de correspondance `models/legacy_fields.py`, qui les alimente en double tant qu'ils existent
(voir [configuration](../configuration.md#champs-natifs-et-champs-studio-historiques)). Pour le
détail étape par étape de quand chaque champ est lu/écrit, voir
[le parcours en 9 étapes](../../fonctionnel/workflow/README.md).

- [`crm-lead.md`](crm-lead.md) — Piste/Opportunité, source de vérité du dossier.
- [`sale-order.md`](sale-order.md) — Ordre de Vente (miroirs de l'opportunité).
- [`sale-order-line.md`](sale-order-line.md) — lignes de devis créées par le widget (articles VSF, main-d'œuvre).
- [`fleet-vehicle.md`](fleet-vehicle.md) — véhicule Odoo créé/réutilisé par le widget, référentiel canonique.
- [`product-product.md`](product-product.md) — article créé depuis un résultat VSF.

`account.move.rpbm_vehicle_id` (calculé depuis les lignes de vente facturées, stocké) et
`stock.picking.rpbm_vehicle_id` (related `sale_id`, stocké) exposent le véhicule sur la facture et
la livraison sans vue dédiée.
