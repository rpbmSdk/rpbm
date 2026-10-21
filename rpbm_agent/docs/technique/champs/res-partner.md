# Champs — `res.partner`

[Index](../../README.md) › [Champs Odoo par modèle](README.md) › Champs — `res.partner`

Date et lieu de naissance de l'assuré, demandés par la procédure FFC. Déclarés dans
`models/res_partner.py`, réservés au groupe vendeur (`sales_team.group_sale_salesman`, donnée
personnelle). Aucun champ Studio équivalent.

| Champ | Type | Libellé |
|---|---|---|
| `rpbm_birth_date` | date | Date de naissance |
| `rpbm_birth_place` | char | Lieu de naissance |

## Vue

`views/res_partner_views.xml` hérite de `base.view_partner_form` et place les deux champs après
le champ `function`, **sans condition `is_company`** : des assurés sont enregistrés à tort comme
sociétés. L'opportunité les expose en `related` écrivable ([`crm-lead.md`](crm-lead.md#client-procédure-ffc)).
Pas encore d'impression : en attente du document FFC visé.

---
Précédent : [Champs — `crm.lead`](crm-lead.md) · Suivant : [Champs — `sale.order`](sale-order.md)
