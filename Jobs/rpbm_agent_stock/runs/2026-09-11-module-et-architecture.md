# Rapport d'exécution — `rpbm-preprod` — 2026-09-11

Statut : `COMPLETED` (module, architecture stock 1, catalogue articles et recette T1/T3 —
`verify_structural.py` : **53 contrôles, 0 FAIL, 0 WARN** ; catalogue : § 0.c ; recette : § 0.d)

## 0.d Complément (même jour) — recette fonctionnelle T1/T3 (`verify_flows.py`)

**Résultat final : T1 PASS, T3 PASS.** Trois itérations ont été nécessaires pour arriver à un
test qui vérifie réellement ce qu'il prétend vérifier — chaque bug trouvé est réel et documenté
ici plutôt que masqué.

**Bug 1 — mode d'expédition manquant.** Les deux premiers essais (SO7748/SO7749) ne posaient
aucun `carrier_id` sur la vente : Odoo est retombé sur la route native de l'entrepôt (« RPBM:
Livraisons Galleria », seule active par défaut) sans jamais invoquer nos 3 nouvelles routes —
confirmation en direct de ce que les docs prédisaient (les routes architecture 1 ne sont
sélectionnées que via le transporteur ou une route de ligne explicite). Corrigé :
`_create_sale_order()` pose désormais `carrier_id` explicitement.

**Bug 2 — assertion de test fausse.** Le contrôle T1 cherchait la sous-chaîne `"GALL/OUT"` dans
le **libellé humain** du type d'opération (`"RPBM: Livraison Galleria"`), qui ne contient jamais
le `sequence_code` machine. Un premier T1 après le fix carrier a donc été rapporté `FAIL` alors
que le routage était en réalité correct (`sequence_code = "GALL/OUT"` vérifié directement).
Corrigé : comparaison sur `sequence_code`, pas sur une sous-chaîne du nom.

**Bug 3 — `origin` mal ciblé (T3 et `rollback.py`).** `purchase.order.origin` (et
`stock.picking.origin`) portent le **nom de la vente** (`"SO7753"`), jamais le
`client_order_ref`. Le contrôle T3 et `rollback.py` cherchaient tous deux `origin like <tag>` et
ne trouvaient donc jamais rien. Corrigés : recherche par nom de vente résolu au préalable.

**Bug 4 — `rollback.py` croyait annuler alors que non.** `sale.order.action_cancel()` ouvre un
assistant de confirmation en interface ; appelé par XML-RPC il ne change jamais l'état (aucune
exception levée, donc faussement rapporté comme réussi). `purchase.order.button_cancel()`
change bien l'état mais ne retourne rien, ce que l'ancien point de terminaison XML-RPC ne sait
pas sérialiser — il lève une `Fault` même quand l'écriture a réussi. Les deux ont produit un
premier rollback qui rapportait « annulé » alors que `sale.order` restait `state=sale` (vérifié en
relisant l'état). Corrigé : `sale.order` est annulé par `write({"state": "cancel"})` direct ;
toute méthode de cancel est désormais vérifiée par relecture de l'état, jamais par l'absence
d'exception.

**Bug 5 — `unlink` refusé même en `draft`.** Un bon de commande fraîchement créé (jamais
confirmé, `state=draft`) a quand même refusé `unlink()` (« vous devez d'abord l'annuler ») dans
cette version d'Odoo. `rollback_record()` tente désormais l'unlink directement en premier, et ne
retombe sur l'annulation que si la suppression directe échoue — plus robuste que de deviner
selon l'état initial (observé aussi : `stock.picking.unlink()` réussit, lui, directement même
`assigned`/`waiting`).

**Preuve de bout en bout obtenue (avant nettoyage)** : T3 a produit exactement la chaîne prévue
par l'architecture — vente Galleria sans stock → picking `GALL/OUT` (waiting) → transfert
`DEP-GALL` (waiting, MTO) → bon de commande créé avec `picking_type_id = D2/IN` et
`partner_id` = fournisseur réel du produit (« HHH ») — validant du même coup l'amendement de la
règle *Acheter* fait en § 0. Toutes les données de recette (2 ventes, 3 pickings, 1 achat par
itération) ont été nettoyées via `rollback.py --run 20260911 --commit` ; l'instance ne porte plus
aucune trace `ARCH1-AUDIT-20260911-*`.

## 0.c Complément (même jour) — catalogue articles (`Jobs/Gestion Stock/import_odoo.py`)

Rejoué en entier sur `rpbm-preprod` après confirmation que le module et l'architecture stock
étaient en place (prérequis D5) : `prepare_migration_files.py` (volumes identiques au relevé
2026-08-05 : 3272 candidats, 43 exclus), `selfcheck` OK, puis `categories`, `suppliers`,
`products`, `supplierinfo`, `costs --commit` (phase la plus lente : ~3188 écritures individuelles,
passée en tâche de fond, terminée avec succès). P2/P3 (entrepôts/emplacements) toujours
volontairement non lancés — abandonnés au profit de l'architecture 1 (§ 0/0.a).

**Contrôle `import_odoo.py check`** — tous les chiffres correspondent exactement à l'attendu, une
fois retirés les 2 produits de service et les 5 emplacements de ce lot (le domaine `check` de ce
script matche tout identifiant externe `like 'rpbm_%'`, ce qui inclut par coïncidence notre
préfixe `rpbm_arch1_*` — bruit de lecture, aucune collision de clé réelle) :

| Contrôle | Brut | Net (hors bruit rpbm_arch1_*) | Attendu |
|---|---:|---:|---:|
| Catégories | 15 | 15 | 15 |
| Fournisseurs | 30 | 30 | 30 |
| Produits | 3231 | 3229 | 3229 |
| Tarifs | 3137 | 3137 | 3137 |
| Produits à coût nul | 199 | 197 | 197 (156 préexistants + 41 sans PRIX RV) |
| Conflit tarif non-VSF | 1 | 1 | 1 (CARPOLISH, préexistant, connu) |
| Conflit tarif VSF (bloquant) | 0 | 0 | 0 |

Synchronisation VSF non bloquée. Catalogue prêt pour `verify_flows.py`.

## 0.b Complément (même jour) — transporteurs et corrections de nommage

**Transporteurs.** Décisions RPBM (2026-09-11) : le nom/prix de « Retrait comptoir » est conservé
tel quel (0.00, partagé Galleria/Genipa) ; « Frais de déplacement » est renommé **« Pose à
domicile »** (prix 0.00 pour l'instant). Les 2 produits de service (`detailed_type=service`) et
les 3 `delivery.carrier` sont créés — `phase_carriers` recherche désormais un transporteur
existant par nom avant `create()` (qui n'est pas idempotent via identifiant externe comme
`load()`), pour rester rejouable sans dupliquer.

**Corrections de nommage.** Les emplacements/types/règles créés dans ce lot portaient à tort des
noms sans accent (`Depot 1`, `Depots`, `Reception ...`) alors que la spec utilise `Dépôt 1`,
`Dépôts`, `Réception ...`. Corrigé dans le code et ré-appliqué sur l'instance (`picking_types`,
`rules`, `locations --commit` rejoués ; renommage direct des ids 14/1519 pour `Stock
D1`/`Stock D2` déjà renommés `Depot 1`/`Depot 2` lors du premier passage). Sans effet sur les
identifiants externes (`xmlid()` normalise déjà les accents).

## 0. Compléments (même jour)

**Amendement de la règle Acheter.** `setup_stock_architecture.py rules --commit` amende
désormais aussi la règle native *Acheter* (`buy_pull_id`, id **6**) : `location_dest_id` →
`RPBM/Stock` (id 1778), `picking_type_id` → `D2/IN` (id 39).

**Putaway.** Décision RPBM (2026-09-11) : pas de rack de réception dédié — `D1/IN`/`D2/IN`
livrent déjà directement sur `Depot 1`/`Depot 2` via leur `default_location_dest_id`, le
rangement précis en rack reste manuel. Les deux règles « réception → rack » de la spec §2.7
(lignes 1-2) sont donc **volontairement non créées** : redondantes avec ce que les types
d'opération font déjà. Seule la règle « filet » (`Stock` → `Depot 2`, id **3**) est implémentée
et vérifiée — elle reste nécessaire : sans elle, une réception fournisseur via la règle *Acheter*
(dont `location_dest_id` = `RPBM/Stock`) n'atterrirait jamais dans un dépôt.

Vérifié par `verify_structural.py` : **53 contrôles, 0 WARN, 3 FAIL** (transporteurs uniquement —
voir § Écarts connus, inchangé).

## 1. Contexte

Exécuté après un rebuild de `rpbm-preprod` qui avait remis le module et l'architecture stock à
zéro (voir `Jobs/Gestion Stock/README.md` § « Comment vérifier l'état actuel »). Profil
`rpbm-preprod` (résolu via `.paradigme.yaml`), scripts de
[`Jobs/rpbm_agent_stock/`](../README.md).

## 2. Relevé initial (avant exécution)

- `rpbm_agent` absent de `ir.module.module` (pas seulement désinstallé — jamais listé).
- `RPBM` (entrepôt id 1) : `lot_stock_id` = `RPBM/Stock D1` (id 14) — la structure plate connue
  (`GALLERIA`, `GENIPA`, `Stock D1`, `Stock D2` tous enfants directs de `RPBM`, aucun nœud `Stock`
  intermédiaire).
- 452 `stock.location`, 5 `stock.picking.type` (natifs), 5 `stock.route` (natives), 6 `stock.rule`
  (natives), 0 `stock.putaway.rule`, 1 `delivery.carrier` (natif).
- Racks : 179 sous `Stock D1` (id 14, 8 quants), 255 sous `Stock D2` (id 1519, 12 quants) — total
  434, cohérent avec le relevé historique de `questions-ouvertes.md`.

**Correction en cours de route** : la vérification initiale de ce lot (conversation précédente)
avait conclu à tort que `Galleria`/`Genipa` avaient disparu — erreur d'un contrôle `like`
sensible à la casse (données réelles en `GALLERIA`/`GENIPA` majuscules). Corrigé avant toute
écriture ; `resolve_location()` recherche désormais par nom exact insensible à la casse.

## 3. Exécuté

| Étape | Commande | Résultat |
|---|---|---|
| Module | `install_module.py --commit` | `rpbm_agent` absent de la liste des apps → `update_list()` → `button_immediate_install()`. Id module **1551**, `x_studio_eurocode` confirmé présent après coup. |
| Emplacements | `setup_stock_architecture.py locations --commit` | Créé `RPBM/Stock` (id **1778**), `RPBM/Stock/Depots` (id **1779**), `RPBM/Camion` (1780), `RPBM/A controler` (1781), `Virtual Locations/CASSE` (1782). Re-rattaché **sans recréer** : `Stock D1`→`Depot 1` (id 14, sous Depots), `Stock D2`→`Depot 2` (id 1519, sous Depots), `GALLERIA`/`GENIPA` (1775/1776, sous Stock, `replenish_location=True`). `warehouse.lot_stock_id` repointé sur `RPBM/Stock`. |
| Types d'opération | `setup_stock_architecture.py picking_types --commit` | 34 types créés (23 internal + 4 incoming + 3 outgoing + 4 retours), retours rattachés à leur réception. |
| Routes | `setup_stock_architecture.py routes --commit` | 3 routes créées ; route `Buy` amendée (`product_categ_selectable=True`). |
| Règles | `setup_stock_architecture.py rules --commit` | 6 règles métier créées. |
| Putaway | `setup_stock_architecture.py putaway --commit` | 1 règle « filet » créée (id 3), voir § 0. Les 2 règles « réception → rack » de la spec ne sont pas créées (décision RPBM). |
| Transporteurs | `setup_stock_architecture.py carriers --commit` | 3 transporteurs créés (voir § 0.b). |

## 4. Vérification post-exécution (`verify_structural.py`)

État final (après § 0/0.b) : **53 contrôles, 53 PASS, 0 WARN, 0 FAIL**.

- **Racks et quants préservés** : 179+255=434 racks, 8+12=20 quants inchangés après le
  re-rattachement de `Stock D1`/`Stock D2`.
- **`lot_stock_id` repointé sans effet secondaire observé** sur `wh_input_stock_loc_id`
  (`RPBM/Input`, id 15) ni `wh_output_stock_loc_id` (`RPBM/Output`, id 12) — le point non vérifié
  §6.4 de `01-architecture-1-zones.md` est donc désormais **observé**, pas seulement déduit du
  code.
- **WARN règle Acheter (`buy_pull_id`, id 6)** : `location_dest_id` = `RPBM` (id 11), pas
  `RPBM/Stock` comme cible ; `picking_type_id` = `RPBM: Réceptions` (id 5), pas `D2/IN`. Écart
  déjà documenté en §4.2 de la spec — amendement d'un enregistrement natif, volontairement hors
  périmètre des phases de création.

## 5. Corrections apportées au code pendant l'exécution

- `common.Odoo.call()` : `update_list()`/`create()` (méthodes sans recordset cible) plantaient
  (`TypeError: takes 1 positional argument but 2 were given`) car `ids=[]` était envoyé comme
  argument positionnel réel. Fixé avec `ids=None` → aucun argument envoyé.
- `phase_picking_types`/`phase_rules` : `Partners/Vendors`/`Partners/Customers` ont
  `usage='supplier'`/`'customer'`, pas `'view'` — corrigé.
- `resolve_location()` : recherche désormais par `name =ilike` exact, plus par `complete_name
  like` (substring, ambigu et sensible à la casse).
- `phase_locations` réécrite : elle créait à tort `Depots` sous `warehouse.lot_stock_id` en
  supposant qu'un nœud `Stock` existait déjà. Elle crée maintenant explicitement `Stock`, puis
  `Depots`/`Galleria`/`Genipa`/`Camion` dessous, et repointe `lot_stock_id`.

## 6. Écarts connus

Aucun écart structurel restant (53/53 contrôles PASS). Pour mémoire :

- ~~Transporteurs~~ — **fait** (voir § 0.b).
- ~~Putaway~~ — **fait** (voir § 0) : décision RPBM de ne pas cibler de rack précis.
- ~~Règle Acheter (`buy_pull_id`)~~ — **fait** (voir § 0).

## 7. Périmètre non exécuté (décision explicite de ce lancement)

Catalogue articles (`Jobs/Gestion Stock/import_odoo.py`) et recette fonctionnelle
(`verify_flows.py`) : hors périmètre de ce lancement, à faire dans un lot séparé.
