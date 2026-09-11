# Réconciliation architecture — module `rpbm_agent` × migration stock (`Jobs/Gestion Stock/`)

Date : 2026-07-28, révisé plusieurs fois :
- 2e passe (28/07) : contrainte `product.template`, séquencement d'installation (§§2.11, 2.12).
- 3e passe (28/07) : lecture directe du CSV brut (pas seulement des fichiers intermédiaires) —
  colonnes `AUTRE CODE`/`FRS`/`EUROCODE INTERNE`/dimensions non extraites par
  `prepare_migration_files.py`, mesure réelle de la fiabilité de format d'`EUROCODE` (1,3 % de
  rejets), confirmation `FRS` = VSF sur 89 % des lignes, recommandation technique de nettoyage
  (§2.13), et répartition des questions en techniques (§4.A) vs métier (§4.B).
- 4e passe (29/07) : filtre de format implémenté dans `prepare_migration_files.py`
  (`eurocode_format_valide`), vérification live contre VSF **écartée par décision RPBM**
  (risque de détection du portail), et décision RPBM de créer un `product.supplierinfo` +
  `res.partner` (si manquant) pour **tous** les fournisseurs `FRS`, pas seulement VSF — voir
  §2.6, §2.13, `suppliers_mapping.csv`.
- 5e passe (30/07) : prise en compte de `sync_vsf_information()` (commits `0d24ff3` et `7e053a4`,
  postérieurs aux passes précédentes). Le module ne fait plus que **créer** des produits, il en
  **réécrit** désormais des champs et historise le prix fournisseur. Deux nouveaux points P0
  (§2.14 effacement des données d'audit par `description`, §2.15 blocage de la synchro sur
  ligne fournisseur en doublon), requalification de `x_studio_eurocode` en clé fonctionnelle
  (§2.1), et retrait de la recommandation d'importer les dimensions (§2.10).

Analyse croisée. Seule écriture réalisée : régénération locale des fichiers de préparation
(`prepare_migration_files.py`) — toujours aucune écriture Odoo.

## 1. Résumé des deux projets

**`rpbm_agent`** ([roadmap](../../rpbm_agent/docs/roadmap.md),
[état des lieux](../../rpbm_agent/docs/etat-des-lieux.md)) est un module Odoo : un widget
recherche véhicule → catégorie → pièce → eurocode → article via les portails X'Glass et VSF,
écrit des champs `x_studio_*` sur `crm.lead`/`sale.order`, et **crée des `product.product` à la
volée** (`/createProduct`) quand l'article VSF sélectionné n'existe pas encore dans Odoo. En
cours de fiabilisation (lots L0 à L4 de la roadmap), jamais déployé aux équipes.

**`Jobs/Gestion Stock/`** ([README](../../Jobs/Gestion%20Stock/README.md),
[infos.md](../../Jobs/Gestion%20Stock/infos.md)) est la migration du référentiel articles et du
stock (Google Sheets → Odoo) : ~3 289 références candidates par `EUROCODE`, restructuration des
entrepôts (1 entrepôt `RPBM` → 5 entrepôts distincts `Galleria`/`Genipa`/`Dépôt 1`/`Dépôt
2`/`Camion`), création d'une arborescence de 10 catégories produit (+7 sous-catégories sous
`Autres`). Phase de préparation, **lecture seule sur Odoo**, aucune écriture encore effectuée.

Les deux créent/modifient des `product.product` selon des conventions construites
indépendamment, sans se référencer aujourd'hui. Sans réconciliation, le jour où les deux tournent
en production, le widget créera des doublons produits et des articles hors catégorisation —
l'inverse de l'objectif d'assainissement des deux chantiers.

## 2. Analyse croisée — points de convergence et de divergence

### 2.1 — Collision de clé `default_code`, et fiabilité de la colonne `EUROCODE` source (priorité maximale)

`rpbm_agent` crée les produits avec `default_code` = référence constructeur VSF, repli sur le
code VSF si absente (`product_creation_values()`,
[`controllers/vsf.py:59-73`](../../rpbm_agent/controllers/vsf.py#L59-L73)). La recherche
d'existant avant création se fait en 3 temps
(`_find_existing_product()`, [`controllers/main.py:169-186`](../../rpbm_agent/controllers/main.py#L169-L186)) :
`default_code`, puis `product_tmpl_id.x_studio_eurocode`, puis nom.

La migration stock cible `default_code` = colonne `EUROCODE`
([`README.md` §« Colonnes principales »](../../Jobs/Gestion%20Stock/README.md)), confirmé dans
`products_to_import.csv` généré par
[`prepare_migration_files.py:186-226`](../../Jobs/Gestion%20Stock/prepare_migration_files.py#L186-L226)
(colonne `product_reference`).

**Risque** : un produit migré n'a `x_studio_eurocode` renseigné dans aucun des fichiers de
préparation actuels (`products_to_import.csv` ne contient pas cette colonne). Le widget ne le
retrouvera alors par aucun des 3 critères de recherche et créera un doublon sur le même article
physique dès que quelqu'un rouvre ce même eurocode dans le widget.

**Aggravation (5e passe, 30/07) : `x_studio_eurocode` n'est plus un simple critère anti-doublon,
c'est la clé fonctionnelle de la re-synchronisation VSF.** `_sync_vsf_information()`
([`models/product_template.py:113-115`](../../rpbm_agent/models/product_template.py#L113-L115))
lit ce champ et lève une `UserError` s'il est vide. Un produit migré sans `x_studio_eurocode`
n'est donc pas seulement dupliquable : il est **non synchronisable à vie** — ni prix VSF, ni
dimensions, ni tarif fournisseur ne pourront jamais être rafraîchis dessus.

Aucun changement de script n'est nécessaire : `products_to_import.csv` porte déjà l'eurocode en
colonne `product_reference` et son indicateur de fiabilité en `eurocode_format_valide`. La règle
d'import à écrire est `x_studio_eurocode = product_reference`, inscrite dans
[`plan-import-articles.md`](../../Jobs/Gestion%20Stock/plan-import-articles.md) §P5.
Corollaire tranché le 2026-08-05 : les 43 références rejetées par le filtre de format (§2.13) ne
sont **pas importées** du tout, plutôt qu'importées hors synchro VSF
([`decisions.md`](../../Jobs/Gestion%20Stock/decisions.md) D3). Tous les produits migrés portent
donc un `x_studio_eurocode` valide.

**Correction (relecture du CSV brut, pas seulement des fichiers intermédiaires) : le fichier
source contient bien des candidats de référence interne, mais `prepare_migration_files.py` ne
les extrait pas encore.** Le CSV brut (`Gestion Stock V4 - Stock Complet.csv`, en-têtes ligne 5)
a 60 colonnes ; `SOURCE_COLUMNS`
([`prepare_migration_files.py:16-28`](../../Jobs/Gestion%20Stock/prepare_migration_files.py#L16-L28))
n'en lit que 11. Colonnes disponibles mais non exploitées, pertinentes ici :

| Colonne (index) | Contenu | Remplissage | Pertinence |
|---|---|---:|---|
| `AUTRE CODE` (4) | code alternatif/antérieur | partiel | ex. observé : `2734AGS` en `AUTRE CODE` pour un article dont `EUROCODE`=`6549AGS` — probablement une révision antérieure du code, à confirmer avec RPBM |
| `FRS` (8) | fournisseur | 10 065/10 066 | voir §2.6 révisé — 89 % valent `VSF Centre`/`VSF Ouest` |
| `EUROCODE INTERNE` (58) | variante interne du code | 8 771/10 066 | **diffère de `EUROCODE`** sur 466 lignes/8 771 quand les deux sont remplies — lequel fait foi n'est pas déductible du fichier seul |
| `LONGUEUR (mm)` / `HAUTEUR (mm)` (49/50) | dimensions | — | à rapprocher de `x_studio_largeur_mm`/`x_studio_longueur_mm` déjà créés par `rpbm_agent` (attention : `HAUTEUR` n'a pas d'équivalent `x_studio_*` existant, nomenclature à réconcilier) |

Corrige l'affirmation précédente de cette section : ce n'est pas l'absence de donnée qui pose
problème, mais l'écart entre ce que le CSV contient et ce que le script de préparation en
extrait actuellement.

**La colonne `EUROCODE` elle-même n'est pas fiablement un vrai eurocode VSF — mais le taux de
propreté réel est bien meilleur qu'un premier survol ne le suggérait.** Le format réel d'un
eurocode VSF est illustré par la valeur par défaut de `VSFAgent.searchEurocodePage()`
([`controllers/vsf.py:220`](../../rpbm_agent/controllers/vsf.py#L220), `"6539RGSH5RD"`). Sur les
**3 289 eurocodes uniques** du fichier, un contrôle de plausibilité de format simple
(alphanumérique + tiret, 4 à 15 caractères) n'en rejette que **43 (1,3 %)**, et ces 43 portent
presque tous une marque explicite de non-fiabilité : annotations entre parenthèses
(`"52185922 (CODE CONSTRUCTEUR)"`, `"A1769064900 (REF XGLASS)"` — la donnée s'auto-désigne comme
non-eurocode), suffixes de statut (`"8374LGNH5FDW-PERDU"`, article perdu), texte de substitution
(`"eurocode corrigé"`), codes concaténés (`"K137 / 355558132 / 356408132"`), ou données non
produit comme **`"17/03 : COTTET Eric"`** (date + nom de client) — non filtrée par
`INVALID_CODES` actuel
([`prepare_migration_files.py:14`](../../Jobs/Gestion%20Stock/prepare_migration_files.py#L14),
`{"0","-","---","?"}`). Le reste (98,7 %) a un format plausible, sans qu'on puisse garantir à
100 % qu'il s'agit du même référentiel qu'utilise VSF (une référence constructeur qui ressemble
formellement à un eurocode reste possible) — voir recommandation en §2.13.

Recopier cette colonne telle quelle, sans nettoyage, dans `x_studio_eurocode` (dont la définition
constante dans le module est « Eurocode VSF complet ») risquerait de corrompre le sens de ce
champ sur les ~1,3 % de lignes concernées.

### 2.13 — Fiabiliser `EUROCODE` avant de peupler `x_studio_eurocode`

Question technique (pas métier) : comment identifier les « vrais » eurocodes avant l'import.

**Implémenté (29/07/2026) : nettoyage déterministe.** `EUROCODE_FORMAT_RE` + la fonction
`eurocode_format_valide()` dans
[`prepare_migration_files.py`](../../Jobs/Gestion%20Stock/prepare_migration_files.py) appliquent
un filtre de plausibilité de format (alphanumérique + tiret, 4 à 15 caractères) à chaque eurocode
candidat. Résultat mesuré à l'exécution : **43 des 3 289 références (1,3 %)** échouent le
contrôle — annotations entre parenthèses, suffixes `-PERDU`, texte libre, codes concaténés. Ces
lignes sont marquées `eurocode_format_valide=false` dans `products_to_import.csv` avec une note
explicite ; elles restent utilisables comme référence interne mais ne doivent **pas** être
copiées dans `x_studio_eurocode` sans vérification manuelle.

**Écarté par décision RPBM (29/07/2026) : vérification live contre le portail VSF.** L'option
envisagée (rejouer un échantillon de 30-50 codes via `VSFAgent.searchEurocodePage()`, même
mécanisme que [`debug_portals.py`](../../rpbm_agent/debug_portals.py), pour calibrer le taux de
faux positifs résiduel) n'est **pas mise en œuvre pour l'instant** : risque de se faire repérer
par le portail sur un volume de requêtes inhabituel, en dehors de l'usage normal du widget. À
documenter de nouveau si cette décision est reconsidérée plus tard — dans ce cas, prévoir un
espacement des requêtes et un créneau hors utilisation du widget en production (le verrou de
session de `rpbm_agent` sérialise déjà les deux usages, mais un script de vérification externe ne
passe pas par ce verrou).

Une piste écartée pour d'autres raisons (charge disproportionnée) : interroger VSF pour les
3 289 codes un par un plutôt qu'un échantillon — inutile de toute façon une fois le filtre de
format appliqué, qui traite déjà 98,7 % des cas sans ambiguïté.

### 2.2 — `categ_id` jamais renseigné par le widget

`product_creation_values()` ne fixe pas `categ_id` → tout produit créé par le widget tombe dans
la catégorie par défaut Odoo, alors que la migration construit une arborescence de 10 catégories
+ 7 sous-catégories sous `Autres`
([`categories_odoo_proposition.csv`](../../Jobs/Gestion%20Stock/categories_odoo_proposition.csv)).
Sans correctif, chaque nouvel article créé par le widget après la migration échappe à la
catégorisation — et donc à la politique de valorisation par catégorie que la migration cherche
justement à établir (les catégories existantes en préproduction ont déjà des politiques mixtes
`average`/`real_time` et `standard`/`manual_periodic`, cf. `data_quality_report.md`).

### 2.3 — `standard_price` (coût) jamais renseigné par le widget

Seul `list_price` (prix public VSF) est écrit à la création. La migration cible
`standard_price` = colonne `PRIX RV` (décision client du 2026-07-23,
[`README.md` §« Prix fournisseurs et coût de stock »](../../Jobs/Gestion%20Stock/README.md)).
La méthode retenue est le coût **standard** avec valorisation **manuelle**
([`decisions.md`](../../Jobs/Gestion%20Stock/decisions.md) D8), ce qui neutralise l'impact
comptable — mais un produit créé à coût nul par le widget reste un trou dans la valorisation du
stock, et le widget ne renseigne toujours ni `standard_price` ni `categ_id`.

### 2.4 — Deux mappings de catégorisation indépendants sur la même taxonomie physique

Le widget a son propre mapping calque X'Glass → « Pièce concernée »
([`calques-mapping.md`](calques-mapping.md), alimente `crm.lead.x_studio_field_eENQz`, 4
valeurs). La migration stock a le sien, colonne `TYPE` → catégorie Odoo
([`categories_mapping.csv`](../../Jobs/Gestion%20Stock/categories_mapping.csv)/
[`categories_odoo_proposition.csv`](../../Jobs/Gestion%20Stock/categories_odoo_proposition.csv),
10+7 valeurs). Les deux couvrent le même référentiel physique (pare-brise / lunette / glace
latérale / joint / …) depuis deux vocabulaires sources différents (libellés de calque X'Glass
d'un côté, colonne `TYPE` du Google Sheet historique de l'autre), construits sans se référencer
l'un l'autre.

### 2.5 — Précédent déjà en place pour les champs d'audit produit

`rpbm_agent` a déjà le mécanisme ([`hooks.py`](../../rpbm_agent/hooks.py) `FIELDS_TO_ENSURE` +
`pre_init_hook`, migrations versionnées `migrations/17.0.*`) pour créer des champs `x_studio_*`
reproductibles sur `product.template`/`product.product`
(`x_studio_reference_constructeur`, `x_studio_eurocode`, dimensions). La migration stock veut
conserver des champs d'audit (`AUTRE CODE`, `FRS`, `No`, notes d'inventaire) « dans des champs
d'audit si disponibles, sinon dans une note interne »
([`README.md` §« Import catalogue articles »](../../Jobs/Gestion%20Stock/README.md)) sans
préciser de mécanisme de création. Dans tous les cas, la même mécanique de création
(`FIELDS_TO_ENSURE`) devrait être réutilisée plutôt que dupliquée par un mécanisme séparé.

**Renforcement (5e passe, 30/07)** : la contrainte n'est plus seulement « ne pas dupliquer
`FIELDS_TO_ENSURE` », c'est aussi « ne jamais passer par `description` ». Le repli « sinon dans une
note interne » était directement destructeur — voir §2.14. Il a été retiré du README de migration ;
des champs `x_studio_*` dédiés sont désormais obligatoires.

**Précision après lecture du CSV brut (§2.1)** : `AUTRE CODE` et `x_studio_reference_constructeur`
ne sont probablement **pas** la même donnée. `x_studio_reference_constructeur` est alimenté par
le widget avec `articleVsf.refConstructeur` (la référence constructeur telle que VSF la renvoie).
`AUTRE CODE` dans le CSV historique ressemble plutôt à une révision antérieure du même eurocode
(exemple observé : `AUTRE CODE = 2734AGS` pour une ligne où `EUROCODE = 6549AGS`) — un « ancien
code », pas une référence constructeur. Question métier à trancher avant de choisir le champ
cible (voir section 4). `EUROCODE INTERNE` (colonne 58, remplie sur 8 771 lignes, **diverge de
`EUROCODE` sur 466 d'entre elles**) est un troisième candidat encore plus incertain — aucun des
trois fichiers ne permet de déduire lequel fait foi quand ils divergent.

### 2.6 — Fournisseur VSF partagé

Le widget a un partenaire VSF configurable (`rpbm_agent.vsf_partner_id`, défaut `5708`) pour son
`product.supplierinfo`. La migration stock doit rapprocher chaque valeur `FRS` du fichier source
vers un fournisseur Odoo ([`questions-ouvertes.md`](../../Jobs/Gestion%20Stock/questions-ouvertes.md)).

**Vérifié dans le CSV brut (colonne `FRS`, index 8) : oui, VSF est de très loin le premier
fournisseur du fichier historique.** `VSF Centre` (8 772 lignes) + `VSF Ouest` (150) + variante
de casse `Vsf Centre` (21) = **8 943 lignes sur 10 066 (89 %)**, couvrant 2 893 des 3 289
eurocodes uniques. Les autres valeurs `FRS` (`HHH`, `MA`, `BLUE AUTO`, `AUTOS GM`, `MPB`,
`SODIVA`, `CENTRE AUTO`, `MARTINIQUE AUTO`, `OCCASION`, `Panther Pro`, `INVENTAIRE`…) restent
minoritaires (1 114 lignes). C'est un fait technique établi, plus une question ouverte au sens
strict. La question résiduelle (métier) est **tranchée depuis le 2026-08-05** : `VSF Centre` et
`VSF Ouest` désignent tous deux le partenaire `rpbm_agent.vsf_partner_id` (id `5708`), aucun second
partenaire VSF n'est créé ([`decisions.md`](../../Jobs/Gestion%20Stock/decisions.md) D10).

Point de vigilance découvert au passage : la présence de `FRS = VSF Centre/Ouest` **n'implique
pas** à elle seule que la colonne `EUROCODE` de la ligne est un vrai eurocode VSF fiable — le
référentiel Eurocode est un standard industrie du vitrage (utilisé aussi par les autres
revendeurs de la colonne `FRS`), pas une numérotation propriétaire VSF ; le filtre de fiabilité
pertinent reste celui du §2.13 (format), pas un filtre par fournisseur.

**Décision RPBM (29/07/2026) : le traitement fournisseur ne se limite pas à VSF.** Pour les
54 autres valeurs `FRS` du fichier (`MPB`, `BLUE AUTO`, `A+ Glass`, `AUTOS GM`, `SODIVA`,
`CENTRE AUTO`, `MARTINIQUE AUTO`, etc. — 1 115 lignes, 11 % du fichier), le prix fournisseur
(`product.supplierinfo`, prix = `PRIX ACHAT`) doit être créé **au même titre que pour VSF**, y
compris en créant le `res.partner` Odoo correspondant s'il n'existe pas déjà. Généré le
29/07/2026 : [`suppliers_mapping.csv`](../../Jobs/Gestion%20Stock/suppliers_mapping.csv) — 55
valeurs `FRS` distinctes, avec une action de rapprochement proposée par ligne (réutiliser
`rpbm_agent.vsf_partner_id` pour VSF, rapprocher/créer un partenaire pour les autres). Reste
ouvert : le rapprochement `FRS` → `res.partner` Odoo existant proprement dit (fusionner avec la
question déjà posée dans
[`questions-ouvertes.md`](../../Jobs/Gestion%20Stock/questions-ouvertes.md)).

### 2.7 — Typage produit `type='product'` en dur côté widget

[`vsf.py:69`](../../rpbm_agent/controllers/vsf.py#L69) fixe `type: 'product'` sans condition,
alors que la migration distingue stockable/consommable/service par catégorie (colonne
`odoo_product_type` de `categories_odoo_proposition.csv`). Pas un conflit actif aujourd'hui — le
widget ne crée que des pièces vitrage issues de VSF, toujours stockables — mais à documenter
comme limite explicite du widget plutôt que d'aligner l'un sur l'autre sans réfléchir au
périmètre (le widget ne doit pas se mettre à créer des services/consommables).

### 2.8 — Routage logistique (`Camion`, entrepôts) non pris en compte par le widget

Le widget n'écrit jamais de stock (« le stock n'est jamais écrit par le widget », confirmé dans
[`docs/technique/champs/product-product.md`](../../rpbm_agent/docs/technique/champs/product-product.md)),
donc pas de conflit direct sur les `stock.quant`/emplacements. Point à vérifier néanmoins : les
lignes de commande ajoutées par le widget (`addToSaleOrder`) doivent-elles recevoir la route
dédiée « Pose sur site via Camion » proposée dans
[`routes_transferts_entrepots.md` §4.2](../../Jobs/Gestion%20Stock/routes_transferts_entrepots.md),
ou seulement une partie des ventes RPBM passe par ce circuit ?

### 2.9 — Convergence déjà réelle (point positif, rien à changer)

Gouvernance identique sur les deux chantiers : lecture seule Odoo tant que non validé, écritures
via la skill `paradigme-mcp`/profil `rpbm-preprod`, aucun secret committé, documentation
versionnée. À noter explicitement pour que la réconciliation ne rouvre pas ce qui fonctionne déjà
pareil des deux côtés.

### 2.10 — Cascade de prix de vente et `list_price`

La migration stock renvoie explicitement la question du prix de vente vers « les formules déjà
utilisées dans Odoo »
([`README.md`](../../Jobs/Gestion%20Stock/README.md)/[`Réponses_rpbm.md`](../../Jobs/Gestion%20Stock/Réponses_rpbm.md))
— c'est exactement la cascade documentée dans [`prix-devis/README.md`](prix-devis/README.md) et
le chantier séparé **L4** de [`rpbm_agent/docs/roadmap.md`](../../rpbm_agent/docs/roadmap.md#l4).
Les deux pointent vers le même chantier non démarré ; à fusionner en une seule initiative plutôt
que deux questions parallèles.

**Réduction de périmètre (5e passe, 30/07)** : `product_sync_values()`
([`controllers/vsf.py:104-111`](../../rpbm_agent/controllers/vsf.py#L104-L111)) réécrit
`list_price`, `x_studio_largeur_mm` et `x_studio_longueur_mm` à chaque synchronisation. Deux
conséquences pour le périmètre d'import :

- **`list_price`** posé à l'import sera écrasé par le prix public VSF pour les ~2 893 eurocodes
  fournis par VSF. La question du prix de vente ne porte donc réellement que sur les ~400
  références non-VSF (et reste de toute façon découplée de la cascade Studio, qui n'utilise pas
  `list_price`).
- **Dimensions : recommandation de la 3e passe retirée.** Extraire `LONGUEUR (mm)` / `HAUTEUR (mm)`
  du CSV 2025 (colonnes 49/50, non lues par `prepare_migration_files.py`) — y compris l'effort de
  réconciliation de nomenclature `HAUTEUR` vs `x_studio_longueur_mm` qui y était signalé — serait
  écrasé dès la première synchro. Ne pas le faire.

### 2.11 — La migration doit créer des `product.template` (pas de variantes)

Contrainte de conception explicite pour le futur script d'import, pas seulement une hypothèse.
Cohérent avec la convention déjà en place côté `rpbm_agent` : les champs partagés
(`x_studio_eurocode`, dimensions) sont sur `product.template` ; les champs propres au variant
(`default_code`, `x_studio_reference_constructeur`) sont sur `product.product`
([`hooks.py`](../../rpbm_agent/hooks.py) `FIELDS_TO_ENSURE`) — ce qui correspond exactement au
cas « un seul variant par template, pas d'attribut », confirmé côté client (le client n'utilise
pas encore de variantes). Le futur script d'import doit donc passer par
`product.template.create()` (Odoo crée alors automatiquement le variant unique), jamais par une
création directe de `product.product` avec des lignes d'attributs.

### 2.12 — Séquencement d'installation : `rpbm_agent` avant l'import stock

Proposition à documenter comme recommandation P0 : installer `rpbm_agent` sur `rpbm-preprod`
**avant** l'import du catalogue stock, pour que son `pre_init_hook`
([`hooks.py`](../../rpbm_agent/hooks.py)) crée `x_studio_eurocode` (et les autres champs
`product.template` de `FIELDS_TO_ENSURE` : `x_studio_largeur_mm`, `x_studio_longueur_mm`) une
seule fois, réutilisés ensuite par l'import — plutôt que l'import ait sa propre logique de
création de champ Studio en doublon. `pre_init_hook` est idempotent et ne touche à aucune donnée
existante (`_align_related_sale_order_fields` du même fichier ne modifie que des champs déjà
créés par ce même hook).

Nuance nécessaire (voir §2.1) : ce séquencement résout le *mécanisme* de création du champ, mais
pas la question de *quelles lignes source* peuvent légitimement l'alimenter — un filtre de
validité sur `EUROCODE` reste nécessaire avant l'écriture en masse.

Point d'attention distinct : « installer le module » active aussi tout de suite le widget
(bouton, JS, vues) pour tous les utilisateurs Odoo — pas seulement le champ Studio. À trancher
explicitement (voir question 7 ci-dessous).

### 2.14 — Les données d'audit de migration seront effacées par la synchronisation (P0, 5e passe)

Règle de migration en vigueur jusqu'au 30/07
([`README.md` §« Import catalogue articles »](../../Jobs/Gestion%20Stock/README.md)) :

> conserver `AUTRE CODE`, `FRS`, `FRET`, `No` et notes d'inventaire dans des champs d'audit si
> disponibles, **sinon dans une note interne**.

Or `product_sync_values()`
([`controllers/vsf.py:104-111`](../../rpbm_agent/controllers/vsf.py#L104-L111)) réécrit
`description` avec la note HTML VSF produite par `product_description(article)`. Et
`product.template.description` **est** le champ « Notes internes » d'Odoo 17 — vérifié dans le
source (`addons/product/views/product_views.xml`, `<group string="Internal Notes">` avec
`placeholder="This note is only for internal purposes."`), pas déduit de mémoire.

Le repli « sinon dans une note interne » visait donc exactement le champ que la synchronisation
écrase, **sans trace ni avertissement**, dès la première synchronisation d'un produit migré. Les
données d'audit disparaîtraient article par article, au fil des synchros, sans qu'aucune erreur ne
le signale — le mode de défaillance le plus difficile à détecter des deux nouveaux.

**Correction appliquée** : le repli est supprimé du README de migration ; des champs `x_studio_*`
dédiés sont obligatoires, créés via `FIELDS_TO_ENSURE` (§2.5).

### 2.15 — Ligne fournisseur VSF en doublon : synchronisation bloquée (P0, 5e passe)

La décision RPBM du 29/07 (§2.6) demande de créer un `product.supplierinfo` pour **tous** les
fournisseurs `FRS`, VSF compris, au prix `PRIX ACHAT`. Or
`_active_vsf_supplierinfo()`
([`models/product_template.py:56-68`](../../rpbm_agent/models/product_template.py#L56-L68)) :

```python
if len(active_lines) > 1:
    raise UserError(_("Plusieurs prix fournisseur VSF sont actifs pour ce produit ; "
                      "la synchronisation ne peut pas choisir lequel historiser."))
```

et une ligne sans `date_start` est considérée active pour toujours (`not line.date_start or …`,
ligne 60). Une ligne VSF importée sans `date_start`, plus une ligne créée par le widget sur le même
produit, et la synchronisation de ce produit est **définitivement bloquée** — le code refuse
délibérément de deviner laquelle historiser.

**Corrections à porter dans la politique d'import** :

1. `date_start` obligatoire (= date de l'import) sur toute ligne fournisseur migrée. C'est aussi ce
   qui fait fonctionner l'historisation J-1/J du module à la première synchro : le prix 2025 est
   clôturé la veille, le prix VSF du jour créé.
2. Une seule ligne active par couple (produit, fournisseur) à l'import.
3. L'écart de sémantique est assumé et documenté : la migration écrit `PRIX ACHAT` (2025), la
   synchro écrit `prixVenteRPBM` (= `prixVente × 0,8`). Ce ne sont pas la même grandeur ;
   `date_start` les range en historique au lieu de les confondre sur une même ligne.
4. La question « `VSF Centre`/`VSF Ouest` = `rpbm_agent.vsf_partner_id` (`5708`) ? » (§2.6, §4.B-3)
   était **bloquante** — un partenaire distinct aurait produit deux prix VSF concurrents que le
   mécanisme d'historisation ne réconcilie jamais. **Tranchée le 2026-08-05** : même partenaire,
   `5708`.

**État mesuré en préproduction (30/07, lecture MCP `rpbm-preprod`, aucune écriture)** :

| Mesure | Valeur |
|---|---|
| `res.partner` dont le nom contient « VSF » | **1 seul** : `VSF - VITRO SERVICE FRANCE` (id `5708`, `supplier_rank` 268) |
| `product.supplierinfo` du partenaire `5708` | 6, sur 6 produits distincts (ids 184-189) |
| dont lignes **sans `date_start`** | **4** |
| `product.template` avec `x_studio_eurocode` renseigné | 6 (sur 169 produits) |

Lecture : aucun produit n'a aujourd'hui deux lignes VSF actives, donc **rien n'est bloqué en
l'état**. Mais 4 des 6 lignes existantes n'ont pas de `date_start` — elles sont actives pour
toujours. Un import qui ajoute une seconde ligne VSF sur l'un de ces 6 produits le bloque
immédiatement. Les 4 lignes restent en revanche correctement historisables telles quelles : sans
`date_start`, la branche `line.date_start == today` est fausse, donc la synchro les clôture à J-1
et crée la nouvelle ligne — comportement voulu.

Conséquence pratique pour l'import : **`VSF Centre` et `VSF Ouest` ne doivent pas donner lieu à la
création de nouveaux `res.partner`**. La règle du 29/07 (« créer le `res.partner` correspondant
s'il n'existe pas déjà ») ne s'applique pas à ces valeurs : le partenaire VSF existe déjà et le
module s'y réfère par son id. Confirmé par RPBM le 2026-08-05.

**Sans effet sur §2.2 et §2.3** : `product_sync_values()` n'écrit ni `categ_id` ni
`standard_price`. Un produit créé par le widget garde donc un coût nul et une catégorie par défaut
même après synchronisation — la synchro ne répare aucune des deux lacunes.

## 3. Hiérarchie des priorités

**P0 — bloquant avant toute mise en production simultanée des deux chantiers** : §2.1 (clé
`default_code`/déduplication **et** fiabilité de la colonne `EUROCODE` source), §2.2 (`categ_id`
à la création), §2.3 (`standard_price` à la création), §2.11 (l'import stock doit créer des
`product.template`, pas de variantes), §2.12 (installer `rpbm_agent` avant l'import stock pour
créer `x_studio_eurocode` une seule fois), §2.13 (nettoyage de format d'`EUROCODE` — **implémenté**
dans `prepare_migration_files.py` ; vérification live VSF écartée par décision RPBM),
**§2.14** (données d'audit effacées par `description`) et **§2.15** (ligne fournisseur VSF en
doublon bloquant la synchro). Ces points créent une corruption silencieuse du référentiel
(doublons, articles hors catégorie, coûts faux, champ Studio dévoyé de son sens, perte des données
d'audit) si les deux chantiers tournent sans coordination.

Les deux derniers (§2.14, §2.15) sont apparus avec la synchronisation VSF du 30/07 et sont d'une
nature différente des précédents : ils ne dégradent pas la qualité du référentiel au moment de
l'import, ils se déclenchent **plus tard**, à la première synchronisation d'un produit migré —
l'un en effaçant des données sans erreur, l'autre en bloquant définitivement la synchro d'un
produit. Ils ne sont donc pas détectables par un contrôle post-import.

**P1 — à trancher avant un usage courant conjoint, pas bloquant pour un premier import isolé** :
§2.4 (fusion des deux mappings de catégorisation), §2.5 (mécanisme de champs d'audit partagé —
d'autant plus pertinent maintenant qu'on sait que `AUTRE CODE`/`FRS`/`No` ne sont pas encore
extraits par le script), §2.6 (fournisseur VSF partagé).

**P2 — peut attendre, ne bloque ni l'un ni l'autre chantier à court terme** : §2.7 (typage
produit, à documenter seulement), §2.8 (routage Camion sur les lignes ajoutées par le widget),
§2.10 (fusion avec L4).

Les décisions **propres à la migration stock** restent hors du périmètre de cette réconciliation :
celles qui sont prises sont dans [`decisions.md`](../../Jobs/Gestion%20Stock/decisions.md)
(valorisation, répartition des racks Dépôt 1/2, identité du partenaire VSF, sort des 43 eurocodes
suspects), celles qui restent ouvertes dans
[`questions-ouvertes.md`](../../Jobs/Gestion%20Stock/questions-ouvertes.md) (forme des entrepôts,
stock initial, statuts réservé/cassé). Déjà trackées, non dupliquées ici.

## 4. Questions ouvertes, réparties par type de décision

Distinction volontaire entre ce qui se tranche par du code/de l'analyse (pas besoin de RPBM) et
ce qui engage un choix métier/organisationnel (RPBM seul peut trancher).

### 4.A — Questions techniques (résolues ou arbitrables sans le client)

Ces points ont une réponse par défaut recommandée ci-dessous ; ils n'ont pas besoin d'attendre un
retour de RPBM pour avancer.

1. **Fiabiliser `EUROCODE` avant de peupler `x_studio_eurocode` (§2.13). Implémenté (29/07/2026)**
   dans `prepare_migration_files.py` : filtre de format déterministe, 43/3 289 rejets (1,3 %).
   La vérification live contre VSF envisagée en complément (échantillon de calibrage) est
   **écartée par décision RPBM** — risque de détection du portail sur un volume de requêtes
   inhabituel ; à reconsidérer plus tard si besoin, pas maintenant.
6. **Génération de `suppliers_mapping.csv` (§2.6). Implémenté (29/07/2026)** : 55 valeurs `FRS`
   distinctes extraites du CSV brut, avec action de rapprochement proposée par ligne. Pur exercice
   technique — reste néanmoins une question métier résiduelle (4.B.3, identité `VSF Centre`/
   `VSF Ouest`) et une question toujours ouverte dans `questions-ouvertes.md` (Q4, validation du
   rapprochement effectif de chaque `FRS` avec un `res.partner` Odoo).
2. **Séquencement d'installation (§2.12).** *Recommandation* : créer `x_studio_eurocode` (et les
   autres champs `product.template` de `FIELDS_TO_ENSURE`) avant l'import stock, en réutilisant
   le mécanisme `pre_init_hook` existant plutôt que d'en écrire un second. Reste un sous-choix
   d'implémentation (module complet vs script autonome) qui recoupe une question métier — voir
   4.B.7.
3. **`categ_id`/`categories_odoo_proposition.csv` → mapping calque X'Glass (§2.4).** Une fois la
   table de correspondance calque → catégorie validée par le métier (4.B.2), la traduire en code
   dans `createProduct` est un pur exercice technique, pas un nouvel arbitrage.
4. **Import stock = `product.template`, pas de variantes (§2.11).** Contrainte de code à
   respecter dans le futur script d'import ; ne nécessite aucune validation client, juste une
   revue de code au moment de l'écrire.
5. **`x_studio_reference_constructeur` vs `AUTRE CODE`/`EUROCODE INTERNE` (§2.5).** Une fois la
   question métier 4.B.5 tranchée (quelle donnée fait foi), le mécanisme de création du champ
   (réutiliser `FIELDS_TO_ENSURE`) est purement technique.

### 4.B — Questions métier (arbitrage RPBM nécessaire)

1. Pour un article créé par le widget après la migration (absent du CSV d'origine), quelle
   politique de coût (`standard_price`) : reprendre `prixVenteRPBM` (déjà calculé, prix VSF
   remisé) comme coût d'entrée, ou laisser la valorisation automatique Odoo le déterminer au
   premier mouvement de stock ? Dépend directement de la méthode de valorisation
   (manuelle/automatisée, FIFO/AVCO) encore ouverte côté migration.
2. Une fois l'arborescence de catégories créée par la migration, le widget doit-il classer
   automatiquement les nouveaux articles qu'il crée (via son mapping calque existant), ou laisser
   la catégorie vide/à valider manuellement le temps que le mapping calque ↔ catégorie soit
   lui-même validé avec le métier ?
3. ✅ **Tranchée le 2026-08-05** — `VSF Centre` et `VSF Ouest` (89 % des lignes `FRS` du fichier
   historique, confirmé §2.6) désignent le **même** partenaire que `rpbm_agent.vsf_partner_id`
   (id `5708`). Aucun second partenaire VSF n'est créé, ce qui écarte le risque de deux prix
   fournisseur concurrents jamais réconciliés (§2.15).
4. Les articles ajoutés à une commande via le widget doivent-ils systématiquement suivre la route
   logistique « Pose sur site via Camion » en préparation, ou seulement une partie des ventes
   RPBM (à préciser lesquelles) ?
5. Quand `EUROCODE`, `EUROCODE INTERNE` et `AUTRE CODE` divergent sur une même ligne (§2.1, §2.5 —
   466 cas sur 8 771 pour `EUROCODE`/`EUROCODE INTERNE` seuls), lequel fait foi ? Impossible à
   déduire du fichier seul, RPBM est la seule source pour trancher ligne par ligne ou par règle
   générale (ex. « `EUROCODE INTERNE` prime toujours quand il est renseigné »).
6. Qui doit maintenir, dans la durée, la correspondance entre le mapping calque X'Glass
   (`calques-mapping.md`) et l'arborescence de catégories Odoo (`categories_mapping.csv`) une fois
   les deux validés séparément — un document fusionné unique, ou deux documents maintenus en
   synchronisation manuelle ?
7. Installer `rpbm_agent` sur `rpbm-preprod` avant l'import stock (§2.12) active aussi le widget
   (bouton, JS, vues) pour tous les utilisateurs Odoo, pas seulement le champ Studio
   `x_studio_eurocode`. RPBM est-il d'accord pour que le widget devienne visible aux équipes à ce
   stade (avant que L1-L4 de la roadmap ne soient finalisés) ? Si non, un script autonome
   (même mécanisme `context={'studio': True}`, sans installer le module complet) est la solution
   technique de repli — pas besoin de RPBM pour ce choix d'implémentation, seulement pour la
   question de visibilité du widget.
8. *(30/07)* Les 43 références dont l'`EUROCODE` est hors format (§2.13) ne recevront pas de
   `x_studio_eurocode` et seront donc hors synchronisation VSF de façon permanente (§2.1) :
   reprise manuelle avant import, ou limite acceptée ? 1,3 % du catalogue, liste extractible de
   `products_to_import.csv` via la colonne `eurocode_format_valide`.

## 5. Fichiers cités

- [`rpbm_agent/controllers/vsf.py`](../../rpbm_agent/controllers/vsf.py)
  (`product_creation_values`, `product_sync_values` lignes 104-111, `product_supplierinfo_values`)
- [`rpbm_agent/controllers/main.py`](../../rpbm_agent/controllers/main.py)
  (`_find_existing_product`, `createProduct`)
- [`rpbm_agent/models/product_template.py`](../../rpbm_agent/models/product_template.py)
  (`sync_vsf_information`, `_sync_vsf_supplierinfo`, `_active_vsf_supplierinfo` — cités en
  §2.14/§2.15)
- [`rpbm_agent/hooks.py`](../../rpbm_agent/hooks.py) (`FIELDS_TO_ENSURE`, `pre_init_hook`)
- `D:\git\odoo_17\odoo17\addons\product\views\product_views.xml` (groupe `Internal Notes`,
  vérification du champ `description` en §2.14)
- [`rpbm_agent/docs/roadmap.md`](../../rpbm_agent/docs/roadmap.md) (§L4, §L1.5, §L1.3) et
  [`etat-des-lieux.md`](../../rpbm_agent/docs/etat-des-lieux.md)
- [`calques-mapping.md`](calques-mapping.md), [`prix-devis/README.md`](prix-devis/README.md)
- [`Jobs/Gestion Stock/README.md`](../../Jobs/Gestion%20Stock/README.md),
  [`infos.md`](../../Jobs/Gestion%20Stock/infos.md),
  [`decisions.md`](../../Jobs/Gestion%20Stock/decisions.md),
  [`Réponses_rpbm.md`](../../Jobs/Gestion%20Stock/Réponses_rpbm.md),
  [`routes_transferts_entrepots.md`](../../Jobs/Gestion%20Stock/routes_transferts_entrepots.md),
  [`categories_odoo_proposition.csv`](../../Jobs/Gestion%20Stock/categories_odoo_proposition.csv)
- [`Jobs/Gestion Stock/prepare_migration_files.py`](../../Jobs/Gestion%20Stock/prepare_migration_files.py)
  (`SOURCE_COLUMNS` lignes 16-28, `INVALID_CODES` ligne 14, `product_rows`, `category_mapping`)
- [`product_reconciliation.csv`](../../Jobs/Gestion%20Stock/product_reconciliation.csv),
  [`products_to_import.csv`](../../Jobs/Gestion%20Stock/products_to_import.csv) (échantillons
  `EUROCODE` réels cités en §2.1)
- [`Gestion Stock V4 - Stock Complet.csv`](../../Jobs/Gestion%20Stock/Gestion%20Stock%20V4%20-%20Stock%20Complet.csv)
  (fichier brut, en-têtes ligne 5 : colonnes `AUTRE CODE` (4), `FRS` (8), `EUROCODE INTERNE` (58),
  `LONGUEUR`/`HAUTEUR` (49/50) citées en §2.1/§2.5/§2.6)
- [`suppliers_mapping.csv`](../../Jobs/Gestion%20Stock/suppliers_mapping.csv) (généré le
  29/07/2026, cité en §2.6)
