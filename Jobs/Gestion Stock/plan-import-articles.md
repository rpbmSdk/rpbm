# Plan d'import — catalogue articles et emplacements

Date : 2026-07-30, revise le 2026-08-05
Cible : `rpbm-preprod` (`https://rpbm-pre-prod.odoo.com/`), Odoo 17
Perimetre : import du catalogue articles et de la structure d'emplacements. **Le stock initial
est hors perimetre** : il reste bloque tant que l'inventaire corrige du 30/06/2026 n'est pas
fourni (Q2).

Ce document sequence l'import en phases executables. Les decisions metier sont dans
[decisions.md](decisions.md) ; ce qui reste a trancher est dans
[questions-ouvertes.md](questions-ouvertes.md) ; la coexistence avec le module `rpbm_agent` est
analysee dans
[reconciliation-stock-rpbm-agent.md](../../docs/cartographie/reconciliation-stock-rpbm-agent.md).

> **Revision du 2026-08-05** — trois decisions changent le contenu des phases :
> **D3** les 43 references a l'eurocode douteux ne sont **plus importees** (volumes revus ci-dessous) ;
> **D4** aucune donnee d'historique n'est conservee, la phase **P5bis est supprimee** et les champs
> Studio d'audit sont abandonnes ; **D8** la phase P7 n'a **aucun impact comptable**.
> **Les scripts sont alignes sur ces decisions** : `selfcheck` produit exactement les volumes
> annonces ci-dessous.

---

## Outillage

Deux scripts, environnement `pyenv 3.10.11`, bibliotheque standard uniquement (aucune dependance
a installer).

| Script | Role |
|---|---|
| [`prepare_migration_files.py`](prepare_migration_files.py) | Lit le CSV source, produit les fichiers de preparation. N'ecrit jamais dans Odoo. |
| [`import_odoo.py`](import_odoo.py) | Pousse les fichiers de preparation dans Odoo par XML-RPC, une phase a la fois. |

```
pyenv exec python prepare_migration_files.py
pyenv exec python import_odoo.py <phase> [--commit] [--limit N] [--url ...]
```

**Sans `--commit`, rien n'est ecrit.** Le script se connecte, lit Odoo, construit et affiche les
lignes, puis s'arrete. La regle de securite du projet (« Odoo reste strictement en lecture
seule ») reste donc respectee tant que le flag n'est pas passe explicitement.

Les identifiants sont lus depuis `~/.paradigme/.env` (`RPBM_PREPROD_DB`, `RPBM_USERNAME`,
`RPBM_PASSWORD`), jamais depuis le depot, jamais affiches.

### Idempotence

Chaque ligne porte un identifiant externe derive de sa cle metier
(`__import__.rpbm_<genre>_<cle>`). Odoo fait alors un `write` si l'identifiant existe deja, un
`create` sinon, et se repare tout seul si l'enregistrement a ete supprime a la main. **Rejouer
une phase est sans danger** : c'est le mode de reprise normal.

C'est aussi le seul mecanisme d'unicite disponible sur `product.supplierinfo`, qui n'a aucune
contrainte contre les doublons cote Odoo. Un import de tarifs sans identifiant externe multiplie
les lignes a chaque passage, en silence.

### Lots et erreurs

L'import passe par `load()`, qui est **tout-ou-rien par appel** : une seule ligne en erreur annule
tout le lot. Le script decoupe donc en lots de 200 lignes, signale les lots rejetes et poursuit.
Une reference fautive coute 200 lignes a rejouer, pas 3 272.

### Verification hors ligne

```
pyenv exec python import_odoo.py selfcheck
```

Verifie sans reseau la logique qui n'est pas evidente : normalisation des libelles, conversion des
decimales francaises, regle d'alimentation de `x_studio_eurocode`, decoupage en lots, et surtout
**l'unicite des identifiants externes de chaque genre**. A lancer avant tout `--commit`.

---

## Volumes de reference (releve du 2026-07-30)

| Objet | Volume |
|---|---:|
| Lignes source | 10 066 |
| EUROCODE uniques (chaine brute) | 3 292 |
| References candidates (eurocode normalise) | 3 272 |
| dont variantes de casse/espacement fusionnees | 17 |
| **References au format eurocode suspect, exclues (D3)** | **43** |
| **Produits a creer** | **3 229** |
| References sans PRIX RV (cout non calculable) | 52 |
| Categories a creer | 8 racines + 7 sous-categories |
| Entrepots a creer | 5 |
| Emplacements a creer | 538 |
| Valeurs PLACE non exploitables (non importees) | 4 |
| Fournisseurs a creer | 30 |
| Valeurs FRS exclues (VSF ou non-fournisseur) | 16 |
| **Tarifs fournisseurs** | **2 749 VSF + 388 autres** |
| **Couts a ecrire** | **3 188** |

L'exclusion des 43 references (D3) ne touche que les phases alimentees par
`products_to_import.csv` — P5, P6 et P7. P1 a P4 lisent les fichiers de mapping et sont
inchangees. Detail de l'ecart : 3 272 → 3 229 produits, 2 763 → 2 749 tarifs VSF,
406 → 388 tarifs autres, 3 220 → 3 188 couts.

Le dedoublonnage se fait desormais sur l'**eurocode normalise** et non sur la chaine exacte : la
source contient 17 paires de variantes du meme article (`2454ASMC` / `2454asmc`,
`6084BGNRZ-O` / `6084BGNRZ - O`). Les grouper sur la chaine brute aurait cree deux fiches Odoo
pour une seule reference physique — precisement le doublon que la migration cherche a eviter.
L'orthographe retenue est la plus frequente dans la source, et la note de la ligne concernee liste
les variantes fusionnees.

---

## Sequencement

```
P0 prerequis  ->  P1 categories  ->  P2 entrepots  ->  P3 emplacements
                        |                                    |
                        +--> P4 fournisseurs                  |
                                  |                           |
                        P5 produits <-------------------------+
                              |
                        P6 tarifs  ->  P7 couts  ->  P8 controle
```

*P5bis (notes d'audit) est supprimee depuis le 2026-08-05 : plus aucune donnee d'historique n'est
reprise dans Odoo (D4).*

Les dependances sont reelles : les produits referencent les categories par identifiant externe,
les tarifs referencent produits et fournisseurs, les emplacements referencent les entrepots.

---

## P0 — Prerequis et gel

**Aucune ecriture. Aucune question bloquante : D5 et D4 sont tranchees.**

1. **Installer `rpbm_agent` sur `rpbm-preprod` avant l'import** (D5). Son `pre_init_hook`
   ([`hooks.py`](../../rpbm_agent/hooks.py), `FIELDS_TO_ENSURE`) cree `x_studio_eurocode` et les
   champs de dimensions une seule fois, reutilises ensuite par l'import.
   *Fait le 2026-08-05* : le module etait en realite **desinstalle** en preproduction et
   `x_studio_eurocode` avait disparu de `product.template` — contrairement a ce qu'affirmait le
   releve du 2026-07-30. La phase `products` a refuse de tourner, ce qui est le comportement
   voulu. Installe par `button_immediate_install`, version `17.0.260730.6`, champ recree.
2. **Aucun champ d'audit a creer** (D4). Les quatre `x_studio_*` envisages en juillet sont
   abandonnes : plus aucune donnee d'historique du fichier Excel n'est reprise dans Odoo.
3. **Geler le CSV source.** Relever l'empreinte de `Gestion Stock V4 - Stock Complet.csv` :
   l'import lit par index de colonne, une regeneration de l'export decalerait tout.
4. **Regenerer les fichiers de preparation** : `pyenv exec python prepare_migration_files.py`.
5. **Regenerer `product_reconciliation.csv`** : l'ancien (pipeline PowerShell du 20/07, volumes
   divergents) est passe dans `archive/`. Sans ce rapprochement par `default_code`, l'import peut
   creer un doublon pour chaque reference deja presente dans Odoo — `data_quality_report.md`
   signale son absence a chaque generation.
6. **Lancer `selfcheck`** puis le dry-run de chaque phase.

---

## P1 — Categories

**Aucune condition d'entree : D1 et D8 sont tranchees.** `pyenv exec python import_odoo.py categories`

Cree 8 categories racines sous `All / Saleable` et 7 sous-categories sous `Autres`
(decision RPBM du 23/07). Source : [`categories_odoo_proposition.csv`](categories_odoo_proposition.csv),
qui fait foi pour les libelles.

`Accessoires` et `Main d'Oeuvre` existent deja en preproduction : marquees `reuse_existing`, elles
ne sont pas recreees.

Deux lots successifs, car les racines se rattachent a une categorie Odoo existante (par identifiant
base) et les sous-categories a leur parent `Autres` (par identifiant externe).

**Points de vigilance**
- `complete_name` est calcule par Odoo : jamais envoye.
- `parent_id` est en `ondelete='cascade'` — supprimer `Autres` emporterait ses 7 enfants.
- Odoo n'impose **aucune unicite** sur le nom de categorie : la deduplication repose entierement
  sur les identifiants externes.
- `property_cost_method = standard` et `property_valuation = manual_periodic` sont poses par cette
  phase (D8). Ce sont les valeurs par defaut d'Odoo 17 — l'`ir.default` est pose par
  `stock_account/data/stock_account_data.xml` — donc aucun compte comptable n'est requis. Elles
  sont ecrites explicitement plutot que laissees implicites : en AVCO,
  `stock_account/models/stock_move.py` reecrit `standard_price` a chaque reception entrante et le
  `PRIX RV` charge en P7 serait ecrase des la premiere reception fournisseur. La preproduction
  contient deja des categories en `average`/`real_time` : l'explicite evite d'en heriter.
- Ces deux champs sont `company_dependent` : la valeur posee vaut pour la societe courante.

**Controle** : 15 categories portant un identifiant externe `rpbm_categ_*`, arborescence
`Autres / Optique` etc. visible dans Odoo.

---

## P2 — Entrepots

🚧 **Condition d'entree : Q1, seule question encore bloquante.** Si la reponse est « un entrepot
unique a 5 zones », **cette phase disparait** et P3 rattache les emplacements a l'arborescence
existante.

`pyenv exec python import_odoo.py warehouses`

Cree 5 `stock.warehouse` : `Galleria` (GALL), `Genipa` (GENI), `Depot 1` (DEP1), `Depot 2` (DEP2),
`Camion` (CAM).

⚠️ **Cette phase ne restructure rien.** La preproduction a un entrepot `RPBM` avec 434 emplacements
sous `Stock D1` / `Stock D2`. Promouvoir D1/D2 en entrepots autonomes est une restructuration de
l'existant, pas une creation, et ce n'est pas automatise. Apres cette phase, les deux structures
coexistent — c'est precisement ce que Q1 cherche a eviter.

**A corriger avant toute mise en service, quelle que soit la reponse a Q1** : le `lot_stock_id` de
l'entrepot `RPBM` pointe sur `RPBM/Stock D1`, dont `GALLERIA`, `GENIPA` et `Stock D2` sont des
freres et non des enfants. Une commande client ne peut donc reserver que 67 unites sur 799.

**Controle** : 6 entrepots au total (`RPBM` + les 5 nouveaux), chacun avec son emplacement de stock
cree automatiquement par Odoo.

---

## P3 — Emplacements

**Depend de Q1 pour le parent des emplacements. D11, D12, D13 et D14 sont tranchees.**
`pyenv exec python import_odoo.py locations`

Regle validee : **un emplacement par reference distincte de `PLACE`**, sans regroupement par plage.

Cette phase est **volontairement partielle**. Elle cree :

- un emplacement interne **`A controler`** sous `Physical Locations` ;
- **538 emplacements** sous `A controler`, un par valeur `PLACE` normalisee ;
- **`CASSE`** sous `Virtual Locations`, en `usage=inventory` et `scrap_location`, pour qu'il
  n'alimente jamais le stock vendable.

Elle ignore les 9 valeurs deja resolues (entrepots source `GALLERIA`/`GENIPA`, racine `D2`
existante) et exclut 4 valeurs non exploitables (`!!!`, `-`, `?`, `???`, 19 lignes source au total),
listees a l'execution.

**Repartition tranchee le 2026-08-05 (D12)** : `R101` a `R336` -> Depot 1 ; `R401` a `R937`,
`J...` et `T...` -> Depot 2. Les codes `J`/`T` doivent porter au moins un chiffre, ce qui ecarte
les libelles (`JDESSUS`, `TRINGLE`). Implemente dans `prepare_migration_files.place_warehouse()`,
verifiable hors ligne par `python prepare_migration_files.py --check`.

Les racks rattaches sont crees sous le `lot_stock_id` de leur depot, sous leur **cle normalisee** :
deux graphies d'un meme rack (`J11A` / `J11a`) donnent un seul emplacement Odoo.

**Pourquoi `A controler` subsiste** : 49 valeurs ne sont pas couvertes par la repartition et sont
**ignorees** (D13) — cellules multi-racks (`R108 - R109`, `R303 / R324`), libelles non codifies
(`Tringle`, `Rack Plafond`, `JDESSUS`, `Palette Savon`), statuts (`PERDU`, `NON TROUVE`,
`Vendu ?`), et valeurs designant un entrepot sans emplacement precis (`GALLERIA`, `Depot 2`).
`Centre` — la plus grosse valeur source avec 1 320 lignes — n'a toujours ni nature ni entrepot
parent (Q7). Rattacher au juge produirait une structure fausse et difficile a corriger.
Sous `A controler`, aucune donnee n'est perdue, aucun rattachement n'est affirme, et la reprise se
fait par un simple **rejeu de la phase** : les identifiants externes font que les emplacements sont
**deplaces**, pas dupliques. La phase imprime la liste complete des non rattaches.

**Structure reelle des racks** : la numerotation compte **9 blocs** — R1xx a R4xx (36 chacun),
R5xx 501-538, R6xx 601-642, R7xx 701-**739**, R8xx 801-837, R9xx 900-937 — plus un code `R35`
isole, hors de toute plage et donc non rattache. Les documents anterieurs au 2026-08-05 annoncaient
« 7 blocs, R7xx de 701 a 728 » : c'etait faux, et une revision intermediaire de ce document parlait
de 10 blocs en comptant `R35` comme un bloc a part entiere.

Regle ferme : les informations d'acces physique (cles, reseau Wi-Fi) ne sont **jamais** importees
dans Odoo.

**Controle** : 540 emplacements avec identifiant externe — 489 sous le stock de leur depot
(109 Depot 1, 380 Depot 2), 49 sous `A controler`, 1 en casse, 1 emplacement tampon.

---

## P4 — Fournisseurs

**Aucune condition d'entree : D9 et D10 sont tranchees.** Le rapprochement fin des 55 valeurs `FRS`
n'a en revanche pas ete valide ligne a ligne par le client (Q4) — sans consequence sur le
deroulement de la phase, mais un partenaire mal fusionne se corrige a la main ensuite.

`pyenv exec python import_odoo.py suppliers`

Cree 30 `res.partner` a partir des 55 valeurs `FRS`, apres fusion des doublons de casse
(`BLUE AUTO` / `Blue Autos` / `BLUE AUTOS`, `AUTOS GM` / `AUTO GM` / `Auto GM`, `A+ GLASS` /
`A+ Glass`, `SOCAUMAR` / `Socaumar`…). L'orthographe retenue est la plus frequente dans la source.

**16 valeurs sont exclues, sans exception :**

- **toutes les variantes VSF** (`VSF Centre`, `VSF Ouest`, `VSF Sud`, `VSF Sud-Ouest`, `VSF ?`,
  `Vsf Centre`). Le partenaire `VSF - VITRO SERVICE FRANCE` (id `5708`) existe deja et
  `rpbm_agent` s'y refere par son identifiant. **Verifie le 2026-07-30 : c'est le seul partenaire
  VSF en preproduction.** En creer un second casserait definitivement l'historisation des prix du
  module ;
- les valeurs qui ne designent pas un fournisseur : `-`, `??`, `INVENTAIRE` (161 lignes), `CLIENT`,
  `Palette a identifier`, `Centre`, `OCCASION`, `CENTRALE CASSE`.

**Controle** : 30 partenaires `rpbm_partner_*`, aucun nomme « VSF ».

---

## P5 — Produits

**Aucune condition d'entree : D2, D3 et D4 sont tranchees.** `pyenv exec python import_odoo.py products`

Cree **3 229** `product.template`, un par eurocode normalise valide.

| Champ Odoo | Source |
|---|---|
| `default_code` | `EUROCODE` |
| `name` | `DESIGNATION`, repli sur l'eurocode |
| `categ_id` | categorie et sous-categorie issues de `TYPE` (P1) |
| `detailed_type` | `product` — **tous stockables sans exception** (D2) |
| `list_price` | `PRIX BRUT` (regle definitive a confirmer, Q3) |
| `x_studio_eurocode` | `EUROCODE` |

**Les 43 references au format d'eurocode suspect sont exclues** (D3) : annotations entre
parentheses, suffixes `-PERDU`, codes concatenes, texte libre comme `17/03 : COTTET Eric`. Elles ne
sont plus importees « telles quelles hors synchronisation » — sans `x_studio_eurocode` valide, elles
seraient invisibles au widget et non synchronisables a vie, tout en occupant une fiche.
Filtre : `eurocode_format_valide = false` dans `products_to_import.csv`.

**Aucune donnee d'audit n'est reprise** (D4) : ni `AUTRE CODE`, ni `EUROCODE INTERNE`, ni
fournisseur source, ni emplacements source, ni notes d'inventaire — ni en champ, ni en note.

**`x_studio_eurocode` est la cle de re-synchronisation VSF**, pas un champ d'audit :
`sync_vsf_information()` le lit et echoue s'il est vide. Apres D3, **tous** les produits crees en
portent un valide.

**La phase refuse de tourner si `x_studio_eurocode` est absent de `product.template`.** Sans ce
champ, les fiches migrees seraient invisibles a `_find_existing_product()` du widget, qui en
creerait des doublons, et resteraient hors synchronisation VSF a vie. `rpbm_agent` doit donc etre
installe avant — c'est son `pre_init_hook` qui cree le champ.

**Points de vigilance**
- L'import passe par `product.template` : Odoo cree automatiquement le variant unique. Ne jamais
  creer un `product.product` avec des lignes d'attributs.
- `detailed_type` et `type` doivent rester coherents : le script n'envoie que `detailed_type`.
- `is_storable` n'existe pas en Odoo 17 (c'est un champ de la version 18).
- `categ_id` et `standard_price` ne sont pas ecrits par le widget `rpbm_agent` : les articles qu'il
  creera **apres** la migration echapperont a la categorisation et au cout. Limite connue, non
  corrigee par cet import.

**Controle** : 3 229 produits `rpbm_prod_*`, aucun sans categorie, **aucun sans
`x_studio_eurocode`**, aucun non stockable.

---

## P5bis — Notes d'audit — **supprimee (2026-08-05)**

Cette phase publiait les donnees d'audit de la migration en note au chatter de chaque produit. Elle
est **abandonnee** : D4 tranche qu'aucune donnee d'historique du fichier Excel n'est reprise dans
Odoo. L'historique reste dans le fichier Excel, conserve hors Odoo.

La sous-commande `import_odoo.py auditnote` existe encore dans le script et **ne doit plus etre
lancee** — voir « A faire dans le code ».

---

## P6 — Tarifs fournisseurs

**Aucune condition d'entree : D9 et D10 sont tranchees.** `pyenv exec python import_odoo.py supplierinfo`

Cree **2 749** lignes VSF (partenaire `5708`) et **388** lignes pour les autres fournisseurs, prix =
`PRIX ACHAT`. Les tarifs des 43 references exclues en P5 le sont ici aussi (14 VSF, 18 autres).

**Deux regles non negociables**, imposees par le comportement reel de `rpbm_agent` :

1. **`date_start` est toujours renseignee** (date de l'import). Sans elle, la ligne est active pour
   toujours, et l'historisation J-1/J de la synchronisation VSF ne peut plus fonctionner. Avec
   elle, la premiere synchronisation cloture proprement le prix issu du CSV 2025 et cree le prix
   VSF du jour.
2. **Une seule ligne active par couple produit/fournisseur.** `_active_vsf_supplierinfo()` leve une
   `UserError` des qu'il en trouve deux pour le partenaire VSF : la synchronisation de ce produit
   est alors bloquee definitivement.

**Traitement des tarifs preexistants** (D9) : avant tout envoi, la phase
releve les tarifs VSF deja actifs.

1. Ceux **sans `date_start`** sont dates au jour de l'import, ce qui les rend exploitables par
   l'historisation du module.
2. Les produits qui en portent un et qui appartiennent a cet import sont **retires du lot** : ils ne
   recoivent pas de seconde ligne. La ligne conservee est reprise par la premiere synchronisation,
   qui l'historise elle-meme si le prix a change.

Un produit inconnu de l'import n'est jamais concerne : il recevra sa propre fiche, donc sa propre
ligne de tarif, sans jamais en cumuler deux sur le meme enregistrement.

**Etat au 2026-07-30** : 6 tarifs VSF sur 6 produits distincts, dont **4 sans `date_start`**. La
phase les traite desormais automatiquement au lieu de s'interrompre.

L'ecart de semantique est assume : la migration ecrit `PRIX ACHAT` (2025), la synchronisation ecrit
le prix VSF remise du jour. Ce ne sont pas la meme grandeur ; `date_start` les range en historique
au lieu de les confondre.

**Controle** : zero produit avec plus d'un tarif actif pour le partenaire VSF.

---

## P7 — Couts

`pyenv exec python import_odoo.py costs`

Ecrit `standard_price` = `PRIX RV` (D6) sur **3 188** references. Les 52 references sans `PRIX RV`
exploitable sont **exclues** plutot que forcees a zero, comme les 43 references exclues en P5
(dont 32 avaient un cout).

Le fret est inclus dans `PRIX RV` (D7) : rien a ajouter.

**Cette phase n'a aucun impact comptable** (D8), contrairement a ce qu'annoncaient les versions
anterieures de ce plan. Trois raisons cumulees, verifiees dans le code d'Odoo 17 :

1. les categories sont en `manual_periodic` : aucune ecriture comptable n'est generee, quoi qu'il
   arrive ;
2. `_change_standard_price` (`stock_account/models/product.py:268`) sort sur `quantity_svl <= 0`
   avant meme de creer une `stock.valuation.layer` — or les produits crees en P5 n'ont aucun stock,
   le stock initial etant hors perimetre ;
3. les ecritures comptables du meme mecanisme ne concernent que `valuation == 'real_time'`.

Le cout ecrit reste stable dans le temps, contrairement a ce qu'aurait fait un AVCO — c'est la
raison d'etre de la methode `standard` posee en P1.

**Points de vigilance techniques**
- `standard_price` est un champ dependant de la societe : le script passe explicitement
  `allowed_company_ids`, faute de quoi la valeur atterrirait dans la societe de l'utilisateur
  d'integration.
- L'ecriture se fait sur `product.product` et non sur `product.template` : sur un template a
  plusieurs variantes, Odoo ignore l'ecriture **en silence**.
- Cette phase n'utilise pas `load()` mais un `write` par reference : elle est plus lente, et
  s'interrompt proprement en signalant les references introuvables.

**Controle** : nombre de produits a cout nul, avant et apres.

---

## P8 — Controle

`pyenv exec python import_odoo.py check`

Lectures seules : comptages par modele, produits sans `x_studio_eurocode`, produits a cout nul, et
le controle qui compte — **les produits portant plus d'un tarif actif pour un meme fournisseur**,
en distinguant le partenaire VSF (bloquant) des autres (ambigu mais non bloquant).

Apres D3, tout produit `rpbm_prod_*` sans `x_studio_eurocode` signale une anomalie d'import, et non
plus une reference volontairement laissee de cote.

*Releve avant tout import (2026-07-30)* : 169 produits sans `x_studio_eurocode`, 162 a cout nul,
et **1 conflit de tarif sur le partenaire CARPOLISH** (deux prix actifs sans `date_start` sur
`[ECO1250] QUICK PUR PURIFIANT SYSTEME CLIM`). Non bloquant pour la synchronisation VSF, mais Odoo
choisit alors le tarif par ordre de prix — a arbitrer avec le metier.

---

## Reprise et retour arriere

**Rejouer une phase** est le mode de reprise normal : les identifiants externes font qu'Odoo met a
jour au lieu de dupliquer. C'est vrai y compris apres correction d'un mapping (une categorie
renommee, un emplacement rattache a son vrai parent).

**Repartir de zero** en preproduction n'est pas automatise. La procedure manuelle est de
rechercher les `ir.model.data` de module `__import__` dont le nom commence par `rpbm_`, puis de
supprimer les enregistrements correspondants — en commencant par les dependants (tarifs, produits)
avant les references (categories, fournisseurs). A ne faire qu'en preproduction.

---

## Alignement du code (fait le 2026-08-05)

- **D3** : `read_catalog()` filtre `eurocode_format_valide` en un seul point, utilise par les trois
  constructeurs (produits, tarifs, couts). `x_studio_eurocode` est desormais inconditionnel.
  `selfcheck` verifie que les references exclues n'apparaissent dans aucun lot et qu'aucun tarif ni
  cout ne porte sur une reference absente du lot produits.
- **D4** : la phase `auditnote` et tout le code d'audit sont supprimes.
- **D8** : le message de la phase `costs` n'annonce plus d'impact comptable.
- **D10** : `suppliers_mapping.csv` ne dit plus « a confirmer » sur les variantes VSF.
- `products_to_import.csv` porte desormais un `import_status` exploitable
  (`import` / `exclusion_format_eurocode`) au lieu de `to_check` partout.
- `NON_SUPPLIER_KEYS` a ete deplace dans `prepare_migration_files.py` : une seule liste pour les
  deux scripts.
- Archives : `prepare_migration_files.ps1`, `import_product.ipynb` et `product_reconciliation.csv`
  sont passes dans `archive/`. Le rapport de qualite signale desormais l'absence du rapprochement.

## Suivi

Les dix questions du document envoye le 2026-07-30 sont toutes tranchees (voir
[decisions.md](decisions.md) et [Réponses_rpbm.md](Réponses_rpbm.md)). Il ne reste que la question
structurante **« entrepots distincts ou zones d'un meme entrepot »**, numerotee **Q1** dans
[questions-ouvertes.md](questions-ouvertes.md), qui conditionne P2 et P3 — toutes les references
`Q…` de ce document renvoient a cette nouvelle numerotation.

> **A verifier avant de se fier a ce tableau.** Ce qui suit est un **journal d'execution**
> (2026-08-05, rejoue a l'identique le 2026-09-11 apres un rebuild d'instance — voir
> `Jobs/rpbm_agent_stock/runs/2026-09-11-module-et-architecture.md` § 0.c), pas un etat courant
> garanti : un rebuild d'instance (duplication depuis la production, reset applicatif) remet le
> catalogue et le module a zero sans que ce document ne le sache. Avant de supposer qu'une phase
> marquee « OK » est toujours en place, relancer son controle :
> `pyenv exec python import_odoo.py check` (P1-P8, lecture seule) et
> `Jobs/rpbm_agent_stock/install_module.py` sans `--commit` (P0). Voir aussi
> [`README.md` § « Comment vérifier l'état actuel »](README.md#comment-vérifier-létat-actuel).

| Phase | Dry-run | Etat des decisions | Ecriture preprod (2026-08-05, a reverifier) | Controle a rejouer | Ecriture prod |
|---|---|---|---|---|---|
| P0 prerequis | — | D4, D5 | module installe | `install_module.py` (sans `--commit`) | |
| P1 categories | fait | D1, D8 | 15 chargees, 0 echec | `import_odoo.py check` | |
| P2 entrepots | fait | 🚧 **bloquee par Q1** | non lancee (abandonnee, voir architecture 1) | — | |
| P3 emplacements | — | D11-D14, parent selon Q1 | non lancee (abandonnee, voir architecture 1) | — | |
| P4 fournisseurs | fait | D9, D10 | 30 chargees, 0 echec | `import_odoo.py check` | |
| P5 produits | fait | D2, D3, D4 | 3 229 chargees, 0 echec | `import_odoo.py check` | |
| P6 tarifs | fait | D9, D10 | 2 749 + 388, 0 echec | `import_odoo.py check` | |
| P7 couts | fait | D6, D7, D8 | 3 188 ecrits, 0 introuvable | `import_odoo.py check` | |
| P8 controle | fait | — | lecture seule | `import_odoo.py check` | |

P2/P3 restent volontairement non lancees independamment de Q1 desormais : l'entrepot unique +
zones (architecture 1) les rend caduques — voir
[`Jobs/rpbm_agent_stock/setup_stock_architecture.py`](../rpbm_agent_stock/setup_stock_architecture.py).

**Journal de l'import du 2026-08-05 en preproduction** (profil `rpbm-preprod` selectionne par
`.paradigme.yaml`, transport xmlrpc) — conserve comme preuve que le script fonctionne, pas comme
etat courant. P2 et P3 volontairement **non lancees** : creer les 5 entrepots trancherait Q1
de fait, et demonter des entrepots porteurs de mouvements est difficile.

Releve avant import : 13 categories, 169 produits, 1 entrepot `RPBM`, 156 produits a cout nul,
un conflit de tarif non bloquant sur le partenaire CARPOLISH.

**Controles P8 apres import**, tous coherents entre eux :

| Controle | Valeur | Lecture |
|---|---:|---|
| Produits sans `x_studio_eurocode` | 169 | exactement les 169 produits preexistants — **aucun produit migre** n'en manque |
| Produits a cout nul | 197 | 156 preexistants + 41 references importees sans `PRIX RV` (3 229 − 3 188) |
| Tarifs actifs multiples sur le partenaire VSF | **0** | la synchronisation VSF n'est bloquee sur aucun produit |
| Tarifs actifs multiples, autres fournisseurs | 1 | le conflit CARPOLISH preexistant, non bloquant |
| Partenaires nommes VSF | 1 | `res.partner` 5708, aucun doublon cree (D10) |

**Verification de D8, sur l'instance et non sur le papier** : `stock.valuation.layer` et
`account.move` crees le 2026-08-05 = **0**. Les 201 couches et 34 ecritures existantes datent de
2021 et suivantes. Ecrire 3 188 `standard_price` n'a produit aucun mouvement de valorisation, comme
l'annoncait `_change_standard_price` (`quantity_svl <= 0`).

**Point d'attention releve au passage** : les categories preexistantes `Accessoires`,
`Consommables Atelier` et `Pieces de Rechange` sont en `average`/`real_time`. Aucun article de cet
import n'y est rattache, mais tout article qu'on y placerait ensuite verrait son `standard_price`
reecrit a chaque reception — precisement ce que D8 cherche a eviter. `Accessoires` etant designee
par D1 comme categorie a reutiliser, son alignement est a trancher avant de s'en servir.

Le passage en production ne se prepare qu'apres validation complete en preproduction, colonne par
colonne.
