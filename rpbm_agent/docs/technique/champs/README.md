# Champs Odoo par modèle

[Index](../../README.md) › Technique › Champs Odoo par modèle

Référence des champs lus ou écrits par `rpbm_agent`, un fichier par modèle porteur. Depuis la
version `17.0.260921.1`, le module ne crée que des **champs natifs** préfixés `rpbm_` (déclarés
dans `models/*.py`) ; les champs Studio historiques de l'instance ne sont plus cités que dans la
table de correspondance `models/legacy_fields.py`, qui les alimente en double tant qu'ils existent
(voir [configuration](../configuration.md#champs-natifs-et-champs-studio-historiques)). Pour le
détail étape par étape de quand chaque champ est lu/écrit, voir
[le parcours en 9 étapes](../../fonctionnel/workflow/README.md).

- [`crm-lead.md`](crm-lead.md) — Piste/Opportunité, source de vérité du dossier.
- [`res-partner.md`](res-partner.md) — client : date et lieu de naissance (procédure FFC).
- [`sale-order.md`](sale-order.md) — Ordre de Vente (miroirs de l'opportunité).
- [`sale-order-line.md`](sale-order-line.md) — lignes de devis créées par le widget (articles VSF, main-d'œuvre).
- [`fleet-vehicle.md`](fleet-vehicle.md) — véhicule Odoo créé/réutilisé par le widget, référentiel canonique.
- [`product-product.md`](product-product.md) — article créé depuis un résultat VSF.
- [`account-move.md`](account-move.md) — facture client : véhicule, immatriculation, marque, modèle,
  eurocode et pièce repris du devis facturé.

`stock.picking.rpbm_vehicle_id` (related `sale_id`, stocké) expose le véhicule sur la livraison
sans vue dédiée. `stock.picking._action_done` refuse une réception dont une ligne cochée, de
quantité non nulle, reste sur un emplacement qui contient des emplacements internes (racks) : le
rangement est manuel (☰ › « Stocker dans »), sans règle de rangement vers les racks.

---
Précédent : [Historique des versions](../versions.md) · Suivant : [Champs — `crm.lead`](crm-lead.md)

Voir aussi : [Configuration & déploiement](../configuration.md) · [Parcours — étape par étape](../../fonctionnel/workflow/README.md)
