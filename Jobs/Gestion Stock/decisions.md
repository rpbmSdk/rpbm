# Décisions arrêtées — migration stock RPBM

Source unique des décisions métier prises pour cette migration. Chaque ligne est **tranchée** :
elle ne doit plus être reposée au client. Les réponses brutes du client sont conservées telles
quelles dans [Réponses_rpbm.md](Réponses_rpbm.md) ; ce document en donne l'état consolidé et les
conséquences techniques.

Ce qui reste à trancher est dans [questions-ouvertes.md](questions-ouvertes.md).

---

## Catalogue et catégories

### D1 — Arborescence de catégories *(2026-07-23)*

8 catégories racines sous `All / Saleable` (`Pare-brise`, `Lunette`, `Glace latérale`, `Joint`,
`Consommable`, `Film solaire`, `Autres`, `Services`) et 7 sous-catégories sous `Autres` :
`Optique`, `Rétroviseur EXT`, `Rétroviseur INT`, `Toit panoramique`, `Cache rétro`, `Lève-vitre`,
`Baie de pare-brise`.

- `CAMERA` reste dans `Autres` **sans sous-catégorie** (article rare, exception explicite).
- `Accessoires` et `Main d'Oeuvre` existent déjà en préproduction sous `All / Saleable` : elles
  sont **réutilisées**, jamais recréées (`reuse_existing` dans
  [categories_odoo_proposition.csv](categories_odoo_proposition.csv), qui fait foi pour les libellés).

### D2 — Tous les articles importés sont stockables *(2026-08-05)*

`detailed_type = product` sans exception pour les 3 229 références importées. La question du
régime des consommables (kit colle, gel capteur, agrafes, cales) ne concerne que la saisie
**postérieure** à la migration, pas cet import.

### D3 — Les 43 références à l'eurocode douteux ne sont pas importées *(2026-08-05)*

43 références sur 3 272 portent un « eurocode » qui n'en est pas un : annotation entre parenthèses
(`52185922 (CODE CONSTRUCTEUR)`), suffixe de statut (`8374LGNH5FDW-PERDU`), codes concaténés
(`K137 / 355558132 / 356408132`), texte libre (`17/03 : COTTET Eric`).

Elles sont **exclues de l'import**, et non plus importées « telles quelles hors synchronisation ».
Motif : sans `x_studio_eurocode` valide elles seraient définitivement invisibles au widget
`rpbm_agent` et non synchronisables, tout en occupant une fiche Odoo. Liste extractible de
[products_to_import.csv](products_to_import.csv) via `eurocode_format_valide = false`.

Volumes après exclusion :

| Phase | Avant | Après |
|---|---:|---:|
| P5 produits | 3 272 | **3 229** |
| P6 tarifs VSF | 2 763 | **2 749** |
| P6 tarifs autres fournisseurs | 406 | **388** |
| P7 coûts | 3 220 | **3 188** |

P1 à P4 sont inchangées : catégories, entrepôts, emplacements et fournisseurs sont dérivés des
fichiers de mapping et non du catalogue dédoublonné.

### D4 — Aucune donnée d'historique du fichier Excel n'est conservée dans Odoo *(2026-08-05)*

Le CSV V4 sert **uniquement** à créer les articles, les prix fournisseurs, les emplacements et les
catégories. `AUTRE CODE`, `EUROCODE INTERNE`, fournisseur d'origine, emplacements historiques,
notes et états d'inventaire **ne sont pas repris**.

Conséquences :

- les 4 champs Studio d'audit (`x_studio_autre_code`, `x_studio_eurocode_interne`,
  `x_studio_fournisseur_source`, `x_studio_emplacements_source`) sont **abandonnés** — rien à créer
  sur l'instance ;
- la phase **P5bis (notes d'audit au chatter) est supprimée** du plan d'import ;
- l'historique reste dans le fichier Excel, qui est conservé hors Odoo.

### D5 — Le module `rpbm_agent` est un prérequis de l'import *(2026-08-05)*

`rpbm_agent` est installé sur la cible **avant** la phase produits. Son `pre_init_hook`
([`hooks.py`](../../rpbm_agent/hooks.py), `FIELDS_TO_ENSURE`) crée `x_studio_eurocode`, clé de
synchronisation VSF sans laquelle les fiches migrées seraient invisibles au widget et dupliquées
par lui. La visibilité du bouton et de l'écran du widget pour les utilisateurs est acceptée.

---

## Prix, coûts et valorisation

### D6 — Le coût Odoo est la colonne `PRIX RV` *(2026-07-23)*

`standard_price` = `PRIX RV`. La signification exacte de la colonne (revient ou revente) n'a pas
besoin d'être tranchée : elle est retenue comme coût quel que soit son nom. Les 52 références sans
`PRIX RV` exploitable sont **exclues** de la phase coûts plutôt que forcées à zéro.

### D7 — Le fret est inclus dans `PRIX RV` *(2026-08-05)*

Aucune règle d'allocation de fret à définir, aucune reprise de la colonne `FRET`.

### D8 — Coût standard, valorisation manuelle, aucun paramétrage comptable *(2026-08-05)*

`property_cost_method = standard` et `property_valuation = manual_periodic` sur les catégories
créées. Ce sont les **valeurs par défaut d'Odoo 17** — l'`ir.default` est posé par
`stock_account/data/stock_account_data.xml` — donc « ne rien mettre en place » produit exactement
cette configuration. Aucun compte de valorisation, d'entrée ou de sortie de stock n'est requis.

Elles sont tout de même écrites explicitement sur les nouvelles catégories : en AVCO,
`stock_account/models/stock_move.py` réécrit `standard_price` à chaque réception entrante et le
`PRIX RV` importé serait écrasé dès la première réception fournisseur. La préproduction contient
déjà des catégories en `average`/`real_time` — l'explicite évite d'en hériter par erreur.

**Conséquence vérifiée dans le code Odoo 17** : écrire `standard_price` sur un produit dont la
quantité valorisée est nulle ne crée **rien**. `_change_standard_price`
(`stock_account/models/product.py:268`) sort sur `quantity_svl <= 0` avant toute création de
`stock.valuation.layer`, et les écritures comptables ne concernent que
`valuation == 'real_time'`. La phase P7 tournant **avant tout stock**, elle est sans impact
comptable — contrairement à ce qu'annonçaient les versions précédentes de la documentation.

### D9 — Un prix fournisseur pour tous les fournisseurs *(2026-07-29, précisé le 2026-08-05)*

`product.supplierinfo` au prix `PRIX ACHAT` pour tous les fournisseurs, pas seulement VSF ; le
`res.partner` manquant est créé (30 partenaires issus des 55 valeurs `FRS`, après fusion des
doublons de casse).

Deux règles imposées par le comportement réel de `rpbm_agent` :

1. **`date_start` toujours renseignée** (date de l'import). Sans elle la ligne est active pour
   toujours et l'historisation J-1/J de la synchronisation VSF ne fonctionne plus. Les tarifs VSF
   préexistants sans `date_start` sont datés au jour de l'import.
2. **Une seule ligne active par couple produit/fournisseur.** `_active_vsf_supplierinfo()` lève une
   `UserError` dès qu'il en trouve deux pour le partenaire VSF : la synchronisation du produit est
   alors bloquée définitivement. Les produits portant déjà un tarif VSF actif sont retirés du lot.

### D10 — `VSF Centre` et `VSF Ouest` = le partenaire existant `res.partner` id 5708 *(2026-08-05)*

Toutes les variantes VSF (`VSF Centre`, `VSF Ouest`, `VSF Sud`, `VSF Sud-Ouest`, `VSF ?`) désignent
`VSF - VITRO SERVICE FRANCE`, celui que `rpbm_agent.vsf_partner_id` référence. **Aucun second
partenaire VSF n'est créé** : il produirait deux prix VSF concurrents que l'historisation du module
ne réconcilie jamais. Concerne 89 % des lignes source.

---

## Emplacements et entrepôts

### D11 — Un emplacement Odoo par référence distincte de `PLACE` *(2026-07-23)*

Pas de regroupement par plage. Les variantes de casse d'un même rack (`J11A` / `J11a`) sont fusionnées
en un seul emplacement.

### D12 — Répartition des racks entre dépôts déportés *(2026-08-05)*

- `R101` à `R336` → **Dépôt 1**
- `R401` à `R937`, `J…`, `T…` → **Dépôt 2**

Les bornes tombent exactement sur la frontière réelle des blocs (`R3xx` s'arrête à 336, `R4xx`
commence à 401). Les codes `J`/`T` doivent porter au moins un chiffre, ce qui écarte les libellés
(`JDESSUS`, `TRINGLE`). Couverture : 489 emplacements — 109 Dépôt 1, 380 Dépôt 2.

**La numérotation compte 9 blocs**, pas 7 : `R1xx` 101-136, `R2xx` 201-236, `R3xx` 301-336,
`R4xx` 401-436, `R5xx` 501-538, `R6xx` 601-642, `R7xx` 701-**739**, `R8xx` 801-837, `R9xx` 900-937,
plus un code `R35` isolé. Les documents antérieurs au 2026-08-05 annonçaient « 7 blocs, R7xx de 701
à 728 » : c'était faux.

### D13 — Les 49 emplacements ambigus sont ignorés *(2026-08-05)*

Cellules multi-racks (`R108 - R109`, `R303 / R324`), libellés non codifiés (`Tringle`,
`Rack Plafond`, `JDESSUS`, `Palette Savon`), statuts (`PERDU`, `NON TROUVE`, `Vendu ?`) et valeurs
désignant un entrepôt sans emplacement précis (`GALLERIA`, `Dépôt 2`) sont créés sous un emplacement
d'attente `A controler`, pour rattachement manuel ultérieur. `Centre` (1 320 lignes source) en fait
partie. Aucune donnée n'est perdue et le rejeu de la phase **déplace** les emplacements au lieu de
les dupliquer.

### D14 — `CASSE` est un emplacement de rebut *(2026-08-05)*

Créé sous `Virtual Locations` en `usage = inventory` et `scrap_location`, il n'alimente jamais le
stock vendable.

---

## Périmètre

### D15 — Vérification live des eurocodes contre le portail VSF : écartée *(2026-07-29)*

Risque de repérage du portail sur un volume de requêtes inhabituel. À documenter si la question est
reconsidérée — voir
[reconciliation-stock-rpbm-agent.md](../../docs/cartographie/reconciliation-stock-rpbm-agent.md) §2.13.

### D16 — Field Service écarté *(2026-07-23)*

RPBM reste sur le circuit devis → commande classique. Les poses sur site passent par une ligne de
service (tâche Project) et des lignes stockables routées, sans l'application Field Service.

### D17 — Hors périmètre de cette migration *(2026-07-23)*

- **Conditions de paiement client** (acompte 40 % hors assurance, paiement après installation pour
  les assurances) : explicitement signalé par le client comme hors du cadre du projet stock.
- **Stock initial** : bloqué tant que l'inventaire corrigé du 30/06/2026 n'est pas fourni — ce n'est
  pas une décision mais un prérequis manquant, voir [questions-ouvertes.md](questions-ouvertes.md).
- **Champs `categ_id` et `standard_price` sur les produits créés par le widget** : le widget continue
  de ne pas les renseigner, c'est au client de les compléter. Limite connue, non corrigée par cet
  import.

---

## Correspondance avec l'ancienne numérotation

Les questions Q1 à Q10 du document envoyé le 2026-07-30
([archive](archive/questions-import-articles-2026-07-30.md)) sont toutes tranchées :

| Ancien | Décision |
|---|---|
| Q1 module visible | D5 |
| Q2 champs d'historique | D4 (sans objet — rien n'est conservé) |
| Q3 valorisation | D8 |
| Q4 emplacements existants | absorbée par la question ouverte sur les entrepôts |
| Q5 répartition des racks | D12 |
| Q6 `Centre`, `Tringle`, `CASSE` | D13, D14 |
| Q7 fournisseur VSF | D10 |
| Q8 consommables | D2 |
| Q9 43 références douteuses | D3 |
| Q10 fret | D7 |
| Q11 entrepôts distincts ou zones | **toujours ouverte** — voir [questions-ouvertes.md](questions-ouvertes.md) |
