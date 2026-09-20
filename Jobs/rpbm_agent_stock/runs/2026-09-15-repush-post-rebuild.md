# Rapport d'exécution — `rpbm-preprod` — 2026-09-15

Statut : `COMPLETED` (module, architecture stock 1, catalogue articles —
`verify_structural.py` : **53 contrôles, 53 PASS, 0 WARN, 0 FAIL** ; catalogue : § 4)

## 1. Contexte

Demande explicite de repush suite à un nouveau rebuild constaté de `rpbm-preprod` (bandeau
« Base de données neutralisée pour les tests » observé le jour même lors d'une recette
indépendante du commit `317bcac`). Contrairement au rebuild du 2026-09-11, celui-ci a
également effacé le nœud `RPBM/Stock` et tout son arbre créés lors du lot précédent — la
remise à zéro est donc plus profonde cette fois (voir § 2). Profil `rpbm-preprod` (résolu via
`.paradigme.yaml`), scripts de [`Jobs/rpbm_agent_stock/`](../README.md) et
[`Jobs/Gestion Stock/import_odoo.py`](../../Gestion%20Stock/import_odoo.py).

## 2. Relevé initial (avant exécution, lecture seule)

- `rpbm_agent` : **installé et à jour** (`ir.module.module` id 1551, version `17.0.260915.2`,
  déployé le jour même par un lot séparé) — seul le module a survécu au rebuild, pas les
  données applicatives.
- `verify_structural.py` : **0/34 types d'opération, 0/3 routes, 0/6 règles**, crash de
  `check_putaway` sur `Emplacement 'Stock' introuvable` — confirme que `RPBM/Stock` (id 1778
  au lot précédent) n'existe plus du tout.
- `import_odoo.py check` : **0 catégorie, 0 fournisseur, 0 produit, 0 tarif** importés
  (identifiants externes `rpbm_*` absents) — catalogue entièrement à refaire.
- Tests hors ligne (`tests/test_install_module.py`, `tests/test_setup_stock_architecture.py`,
  `import_odoo.py selfcheck`) : OK avant tout `--commit`.

## 3. Exécuté

| Étape | Commande | Résultat |
|---|---|---|
| Module | `install_module.py --commit` | Déjà installé → aucune action (no-op confirmé). |
| Catégories | `import_odoo.py categories --commit` | 8 racines + 7 sous-catégories chargées. |
| Fournisseurs | `import_odoo.py suppliers --commit` | 30 partenaires chargés (16 valeurs exclues : VSF, inventaire, doublons de casse, etc.). |
| Produits | `import_odoo.py products --commit` | 3229 produits chargés, 0 échec. |
| Tarifs fournisseurs | `import_odoo.py supplierinfo --commit` | 2749 tarifs VSF + 388 autres, 0 échec. |
| Coûts | `import_odoo.py costs --commit` | 3188 coûts standard écrits (société 1), aucun impact comptable (valorisation manual_periodic, produits sans stock). |
| Emplacements | `setup_stock_architecture.py locations --commit` | `Stock`/`Dépôts`/`Camion`/`A contrôler`/`CASSE` créés ; `Stock D1`→`Dépôt 1`, `Stock D2`→`Dépôt 2`, `GALLERIA`/`GENIPA` re-rattachés sans recréation ; `lot_stock_id` repointé sur `RPBM/Stock`, sans effet secondaire sur Input/Output. |
| Types d'opération | `setup_stock_architecture.py picking_types --commit` | 34/34 types créés (23 internal + 4 incoming + 3 outgoing + 4 retours), retours rattachés à leur réception. |
| Routes | `setup_stock_architecture.py routes --commit` | 3 routes créées ; route Buy amendée (`product_categ_selectable=True`). |
| Règles | `setup_stock_architecture.py rules --commit` | 6 règles métier créées ; règle Acheter native amendée (`location_dest_id`→`RPBM/Stock`, `picking_type_id`→`D2/IN`). |
| Putaway | `setup_stock_architecture.py putaway --commit` | 1 règle « filet » créée (Stock → Dépôt 2). |
| Transporteurs | `setup_stock_architecture.py carriers --commit` | 3 transporteurs créés (2 produits de service à l'appui). |

## 4. Vérification post-exécution

**`verify_structural.py`** : 53 contrôles, **53 PASS, 0 WARN, 0 FAIL** — meilleur résultat que
le lot du 2026-09-11 (qui avait clos avec le WARN Acheter avant son § 0 correctif) ; ici
l'amendement Acheter est posé dès la phase `rules`, donc directement conforme.

**`import_odoo.py check`** :

| Contrôle | Brut | Net (hors 2 produits de service `carriers`) | Attendu (réf. 2026-09-11) |
|---|---:|---:|---:|
| Catégories | 15 | 15 | 15 |
| Fournisseurs | 30 | 30 | 30 |
| Produits | 3231 | 3229 | 3229 |
| Tarifs | 3137 | 3137 | 3137 |
| Produits à coût nul | 199 | 197 | 197 |
| Conflit tarif non-VSF | 1 | 1 | 1 (préexistant, connu) |
| Conflit tarif VSF (bloquant) | 0 | 0 | 0 |

Tous les volumes correspondent exactement à la référence du lot précédent, aux 2 produits de
service près (attendu, cf. `carriers`).

## 5. Périmètre non exécuté (décision explicite de ce lancement)

`verify_flows.py` (recette fonctionnelle T1-T8/MTO) : non demandé pour ce lot, qui portait
explicitement sur la seule reconstitution de l'architecture et du catalogue. À faire dans un
lot séparé si une recette fonctionnelle est souhaitée.

## 6. Écarts connus

Aucun écart structurel (53/53 PASS). Le conflit tarif non-VSF (CARPOLISH) est préexistant et
connu depuis le lot du 2026-09-11, non bloquant.

## 7. Observation pour la suite

C'est le **deuxième rebuild constaté** en une semaine sur `rpbm-preprod` (2026-09-11 et
2026-09-15), chaque fois sans trace préalable dans le dépôt. Le bandeau odoo.sh « Base de
données neutralisée pour les tests » est un signal fiable à surveiller en début de recette
(voir aussi la mise à jour du piège n°3 de
[`odoo-sh-build-connect`](../../.claude/skills/odoo-sh-build-connect/SKILL.md) le même jour,
sujet distinct mais même instance). Pas d'action supplémentaire proposée ici — ce dossier
existe justement pour que ce rejeu reste une commande de quelques minutes plutôt qu'une
reconstitution manuelle.
