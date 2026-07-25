# Automatisations (`base.automation` / `ir.actions.server`)

Relevé sur `rpbm-pre-prod` le 2026-07-25. Ces règles ont été créées **dans l'interface
Studio/Automatisations par des utilisateurs non techniques** pour étendre le comportement de
l'instance sans code. Elles sont invisibles depuis le code du module `rpbm_agent` mais
**agissent sur les mêmes champs** : un champ que le widget écrit peut déclencher (ou être lu
par) l'une de ces règles, ce qui déplace le rayon d'effet d'une écriture bien au-delà du
widget. À prendre en compte avant toute modification des champs listés en
[crm-lead.md](crm-lead.md) / [sale-order.md](sale-order.md).

7 automatisations touchent les modèles du périmètre (`crm.lead`, `sale.order.line`) ; aucune
sur `sale.order` directement. (4 autres existent sur `account.move` — chèques cadeaux — hors
périmètre.)

## `crm.lead`

| # | Nom | Déclencheur | Condition (`filter_domain`) | Action serveur | Effet |
|---|---|---|---|---|---|
| 1 | **Audit Formulaire** | on_create_or_write | *(aucune)* | `code` | Crée un enregistrement `x_audit` (traçabilité des modifs : utilisateur, date, opportunité). Se déclenche à **chaque** write sur la piste. |
| 5 | **Revenu Espéré (RPB)** | on_create_or_write | `x_studio_prix_retenu = "PRix RPB (TTC)"` *(sic, casse)* | `object_write` eq. | `expected_revenue = record.x_studio_field_gUd4S` (Prix RPB TTC) |
| 6 | **Revenu Espéré (XGlass)** | on_create_or_write | `x_studio_prix_retenu = "Prix XGlass (TTC)"` | `object_write` eq. | `expected_revenue = record.x_studio_field_yBqOW` (Prix XGlass TTC) |
| 7 | **Revenu Espéré (px proposé)** | on_create_or_write | `x_studio_prix_retenu = "Prix Proposé (TTC)"` | `object_write` eq. | `expected_revenue = record.x_studio_field_O1pEU` (Prix Proposé TTC) |
| 15 | **Parrainage >250** | on_create_or_write | `expected_revenue >= 250` | `object_write` eq. | `x_studio_revenu_parrain_ttc = expected_revenue * 0.04` |
| 16 | **Parrainage <250** | on_create_or_write | `expected_revenue < 250` | `object_write` eq. | `x_studio_revenu_parrain_ttc = expected_revenue * 0` (= 0) |

**Chaîne à connaître.** `x_studio_prix_retenu` (saisi manuellement) → une des 3 règles
« Revenu Espéré » écrit `expected_revenue` (champ CRM natif, pilote le forecast) → les 2 règles
« Parrainage » recalculent la commission du parrain à partir de `expected_revenue`. Une seule
des 3 sources de prix (RPB) est reliée à la cascade de calcul documentée dans
[prix-devis](prix-devis/README.md) ; les deux autres (XGlass, Proposé) sont des saisies
manuelles. Le widget n'écrit aujourd'hui **aucun** de ces champs, mais s'il venait à alimenter
`x_studio_field_gUd4S`/`yBqOW`/`O1pEU` ou `x_studio_prix_retenu`, il modifierait `expected_revenue`
et la commission parrain par ricochet.

> Coquille à signaler : la condition de « Revenu Espéré (RPB) » teste `"PRix RPB (TTC)"`
> (double majuscule) — à vérifier qu'elle matche bien la valeur de sélection réelle de
> `x_studio_prix_retenu`, sinon la règle ne se déclenche jamais.

## `sale.order.line`

| # | Nom | Déclencheur | Condition | Action serveur | Effet |
|---|---|---|---|---|---|
| 8 | **Tarif x glass** | on_create_or_write | `x_studio_prix_x_glass != 0` | `object_write` eq. | `price_unit = record.x_studio_prix_x_glass * 1.5` |

**Impact direct sur [L1.6](../../rpbm_agent/docs/roadmap.md).** Si le widget renseigne
`x_studio_prix_x_glass` sur la ligne de devis qu'il ajoute (depuis le prix de la pièce OE
X'Glass), cette automatisation **écrase automatiquement le prix unitaire** de la ligne à
`prix_x_glass × 1.5`. Autrement dit : poser `x_studio_prix_x_glass` **est** le mécanisme de
tarification de la ligne, pas une simple donnée d'affichage. À intégrer explicitement dans
L1.6 (et cohérent avec la volonté [L4](../../rpbm_agent/docs/roadmap.md) de repasser sur des
mécanismes de prix natifs : ce `×1.5` en dur est exactement le genre de règle à porter par une
liste de prix).

## Conséquences pour la roadmap

- **L1.3** (écriture des prix VSF) et **L1.2.b** (« Pièce concernée ») touchent des champs qui
  alimentent la cascade de prix `crm.lead` (voir [prix-devis](prix-devis/README.md)), pas ces
  `base.automation` directement — mais le résultat final (`expected_revenue`) dépend des deux.
- **L1.6** (ligne de devis) : écrire `x_studio_prix_x_glass` déclenche « Tarif x glass ».
- **L4** (refonte prix) : ces règles `object_write`/`equation` et le `×1.5` codé en dur font
  partie du périmètre à reprendre en mécanismes natifs (coût + liste de prix).
