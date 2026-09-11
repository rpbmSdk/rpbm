# Questions ouvertes — migration stock RPBM

État au **2026-08-05**. Ce document ne contient **que ce qui reste à trancher**. Tout ce qui est
décidé est dans [decisions.md](decisions.md) et ne doit plus être reposé au client.

L'import du catalogue est prêt techniquement : les scripts sont écrits, testés à blanc, et
n'écrivent rien sans `--commit`. **Une seule question bloque encore le démarrage : Q1.**

| # | Question | Bloque | Réponse par défaut |
|---|---|---|---|
| **Q1** | 🚧 Entrepôts distincts ou zones d'un même entrepôt ? | P2, P3 | aucune — structurante |
| **Q2** | 🚧 Quelle source pour le stock initial ? | import stock | aucune — fichier manquant |
| Q3 | Règle de prix de vente (`list_price`) | P5 | `PRIX BRUT` |
| Q4 | Rapprochement des 55 valeurs `FRS` | P4 | mapping proposé tel quel |
| Q5 | Statuts `Réservé` et `Cassé` en cible | post-import | processus standard Odoo |
| Q6 | Droits et obligation de livraison | post-import | droits Odoo par défaut |
| Q7 | Sort des 49 emplacements sous `A controler` | — | reporté, sans échéance |
| Q8 | Usage précis du Camion et retours | dépend de Q1 | — |
| Q9 | Une vente d'un comptoir peut-elle réserver le stock de l'autre comptoir ? | rien — l'arbre cible accommode les deux | **non : pool par comptoir** |

Q1 et Q2 sont indépendantes : Q1 bloque le catalogue et les emplacements, Q2 bloque le stock. On
peut démarrer l'import du catalogue sans Q2.

---

## Q1 — Entrepôts distincts ou zones d'un même entrepôt ? 🚧

*Bloque P2 (entrepôts) et P3 (emplacements).*

> **Définition complète des deux architectures : [architectures-stock.md](architectures-stock.md).**
> Onze flux métier avec diagrammes, les routes et règles de chaque implémentation, la configuration
> des trois profils de site (Comptoir, Dépôt, Camion), et le tableau de ce que chaque sous-question
> ci-dessous fait basculer. La synthèse ci-après en reprend l'essentiel.

La décision du 2026-07-23 prévoyait **5 entrepôts Odoo distincts** (Galleria, Genipa, Dépôt 1,
Dépôt 2, Camion). L'alternative est **un entrepôt unique** dont ces 5 sites sont des zones de
stockage. Le choix est structurant et coûteux à défaire une fois que des mouvements existent.

### Ce que disent les données

| | |
|---|---:|
| Références au catalogue | 3 273 |
| Références avec du stock | **578 (18 %)** |
| Unités en stock | 767 |
| Moyenne quand il y a du stock | 1,33 unité |
| Références à **une seule** unité | 452, soit **78 %** de celles en stock |
| Références présentes sur les deux dépôts | 213 |

**Ce n'est pas un stock de distribution, c'est un stock de pièces quasi uniques.** 82 % du catalogue
est à zéro et se commande chez VSF à la demande. Trois conséquences :

1. **Aucun réapprovisionnement par anticipation n'a de sens.** On ne maintient pas un stock plancher
   sur 3 273 pare-brise qui partent à l'unité. Les règles de réassort seraient du paramétrage mort :
   le flux est piloté par la commande, pas par le stock.
2. **Les stratégies de sortie (FIFO, « au plus proche ») sont sans objet** : avec une seule unité
   dans 78 % des cas, il n'y a rien à arbitrer.
3. **Ce qu'il faut optimiser, c'est localiser et aller chercher la pièce**, pas la réapprovisionner.
   La machinerie de routes inter-entrepôts répond à un problème que RPBM n'a pas, au prix de
   documents supplémentaires sur un problème qu'il a.

### Ce que ça change à l'usage

| | 5 entrepôts | 1 entrepôt, 5 zones |
|---|---|---|
| Vente d'un article stocké ailleurs | route + transit : **2 à 3 documents** | réservation sur tout l'arbre : **1 bon de livraison** |
| Types d'opération et séquences | 5 jeux à maintenir | 1 seul |
| Transfert entre sites | imposé par le modèle à chaque vente | fait quand on déplace réellement du stock |
| Stock par site en reporting | natif | par filtre sur l'emplacement |
| Réception fournisseur par site | possible, avec adresse propre | destination pilotable par site, adresse imprimée centralisée |

### Le traitement comptable est identique dans les deux cas

Vérifié dans le code d'Odoo 17, c'est le point contre-intuitif :

- les comptes de valorisation sont portés par la **catégorie d'articles**, jamais par l'entrepôt ni
  par l'emplacement (`stock.warehouse` n'a aucun champ comptable ; les deux champs de
  `stock.location` précisent *« This has no effect for internal locations »*) ;
- un mouvement entre deux emplacements internes ne génère **jamais** d'écriture ;
- les transferts entre entrepôts d'une même société non plus : le transit porte la société, donc il
  est valorisé — le code le dit en toutes lettres ;
- avec la valorisation manuelle retenue (D8), aucune écriture n'est générée de toute façon.

**Le choix est logistique et organisationnel, pas comptable. Il ne faut donc pas l'arbitrer sur des
motifs comptables.**

### Ce qui ne dépend pas de la réponse

Deux besoins souvent invoqués en faveur des 5 entrepôts se traitent nativement sans eux :

- **Segmenter les ventes par site** : le compte analytique (`sale.order.analytic_account_id`, qui
  descend automatiquement sur les lignes de facture) et l'équipe commerciale
  (`sale.order.team_id`, propagée depuis `crm.lead`, donc quasi gratuite puisque le parcours passe
  déjà par le CRM via `rpbm_agent`). Le site de vente est une information commerciale, pas une
  information de stock.
- **Choisir la destination à la préparation** (comptoir ou camion) : deux routes
  `sale_selectable`, sélectionnables à la ligne de commande via `sale.order.line.route_id`. La route
  de ligne prend le pas sur celles de l'article et de sa catégorie. Natif, déterministe, aucun
  développement.

  *Précision du 2026-08-05* : `route_id` est un champ **de ligne**, donc oubliable dossier par
  dossier. Le **mode d'expédition** lève ce risque — `delivery.carrier.route_ids`
  (domaine `shipping_selectable`) s'applique en repli quand la ligne n'a pas de route
  (`stock_delivery/models/sale_order.py:51-55`), et se choisit **une seule fois pour toute la
  commande**. Le module `stock_delivery` est déjà installé sur la préproduction. Détail et limites
  dans [architectures-stock.md](architectures-stock.md#b5-bis--le-mode-dexpédition-sélectionne-bien-une-route).

### Le cas du Camion

Le camion pose chez le client : la marchandise sort bien du stock à partir de lui. Cela ne dicte pas
d'en faire un entrepôt. Le schéma natif est la **livraison en 2 étapes** (`pick_ship`) —
*Préparation* Stock → Camion (mouvement interne, aucune écriture), puis *Expédition* Camion → Client
(l'événement comptable, à la pose). Le Camion est alors l'emplacement de sortie
(`wh_output_stock_loc_id`). L'étape intermédiaire n'est pas de la bureaucratie : un pare-brise chargé
le matin et cassé en route est une perte de stock qu'il faut pouvoir mettre au rebut **depuis le
camion**.

### Questions à poser

1. ~~**Galleria et Genipa reçoivent-ils des livraisons fournisseur en direct**, chacun à sa propre
   adresse, ou tout arrive-t-il à un point central ?~~ — **répondu le 2026-08-06 : oui**, un
   fournisseur peut devoir livrer au comptoir, de façon **occasionnelle**. Le bon de commande
   imprimé n'étant **pas** envoyé au fournisseur (portail ou téléphone), la recommandation ne
   change pas : entrepôt unique, plus deux types d'opération de réception dédiés. Arbitrage complet
   dans [architectures-stock.md § I](architectures-stock.md#i--arbitrage-du-2026-08-06).
2. **Faut-il des numérotations de documents distinctes par site** (bons de livraison, réceptions) ?
3. **Que doit-on pouvoir lire par site** : valeur du stock, quantités, mouvements ? Un filtre par
   emplacement suffit-il ?
4. **Le chargement du camion doit-il laisser une trace** dans Odoo (préparation validée le matin),
   ou seule la pose chez le client doit-elle être enregistrée ?
5. **Quelle est la répartition entre poses au comptoir/atelier et poses sur site ?** Elle décide de
   la route posée par défaut.
6. **Le rattachement d'une vente à un site se fait-il par vendeur ou par commande ?** Décide si la
   valeur analytique par défaut se pose sur l'utilisateur ou se choisit à la main.
7. **Galleria et Genipa tiennent-ils un stock de consommables à rotation rapide** (joints, produits
   d'atelier) ? Cette famille-là justifierait des règles de réassort par zone — la conclusion
   « aucun réapprovisionnement par anticipation » ne vaut que pour le catalogue vitrage.

**Recommandation** : un entrepôt unique avec les 5 sites en zones, **sauf si la réponse à la question
1 ou 2 est oui**.

> *Révision du 2026-08-06 — la question 1 est répondue « oui » et la recommandation est maintenue.*
> Le seul apport des 5 entrepôts était une adresse de réception propre **imprimée sur le bon de
> commande** ; RPBM n'envoie pas ce document. Ce que F4 exige est une **destination** de réception
> par comptoir, obtenue par deux types d'opération dédiés sur l'entrepôt unique. Le chemin de sortie
> — si un fournisseur réclamait un jour le document imprimé — est décrit et vérifié :
> [architectures-stock.md § D bis](architectures-stock.md#d-bis--architecture-3--hybride-comptoirs-imbriqués),
> et ne coûte pas les 3 documents par vente. **Q1 reste ouverte** : les questions 2 à 7 n'ont pas
> de réponse. C'est la configuration qui produit un seul document par vente, supprime la phase
P2, et fait disparaître la coexistence problématique avec l'entrepôt `RPBM` existant — les 489
emplacements migrés se rattachent directement à l'arborescence en place. Promouvoir plus tard une
zone en entrepôt reste possible ; démonter 5 entrepôts porteurs de mouvements l'est beaucoup moins.

**Réserve** : le raisonnement s'appuie sur le fichier source de janvier 2025 et sur l'état de la
préproduction. Si les volumes réels ont sensiblement changé, la question 7 est celle qui peut faire
bouger la conclusion.

### Défaut à corriger dans les deux cas

L'entrepôt `RPBM` a son emplacement de stock principal (`lot_stock_id`) positionné sur
`RPBM/Stock D1`. Or `GALLERIA`, `GENIPA` et `Stock D2` en sont des **frères**, pas des enfants. Une
commande client ne peut donc réserver que ce qui se trouve sous `Stock D1` : **67 unités sur 799**,
soit 8 %. Le reste apparaît indisponible alors qu'il existe. À corriger avant tout import, quelle que
soit la configuration retenue. Ce n'est pas une question — c'est un correctif à planifier.

---

## Q2 — Quelle source fait foi pour le stock initial ? 🚧

*Bloque l'import du stock. N'empêche pas l'import du catalogue.*

[stock_initial_to_import.csv](stock_initial_to_import.csv) est volontairement **vide** : le CSV de
janvier 2025 n'est pas une source fiable, les utilisateurs indiquant que le stock n'est plus tenu
correctement depuis 2023.

1. **Quelle source retenir** : l'inventaire réel du 30/06/2026, le stock théorique corrigé, ou le
   CSV V4 corrigé ?
2. **Comment arbitrer l'écart d'inventaire** : stock théorique 106 745,23 € vs stock réel
   100 297,05 €, soit **6 448,18 €** ?
3. **Fournir le fichier corrigé de l'inventaire du 30/06/2026** — sans lui, rien ne peut être
   préparé.
4. **Traitement des lignes marquées `Pas là`, `ERREUR`, vendu, réservé ou cassé** : exclusion pure
   ou investigation au cas par cas avant import ?

Contrainte technique déjà arrêtée : la création du stock initial passera par un ajustement
d'inventaire validé en préproduction, jamais par une création directe de `stock.quant`.

---

## Q3 — Quelle règle pour le prix de vente ?

*Bloque P5 (produits). Défaut : `PRIX BRUT`.*

Le client renvoie sur « les formules déjà utilisées dans Odoo » plutôt que sur une colonne du fichier
source. Ces formules n'ont pas encore été relevées sur l'instance.

Le périmètre réel est plus étroit qu'il n'y paraît : la synchronisation VSF réécrit `list_price` avec
le prix public VSF (`product_sync_values()`). Pour les ~2 893 eurocodes fournis par VSF, toute valeur
posée à l'import sera **écrasée dès la première synchronisation**. La question ne porte réellement
que sur les **~400 références non-VSF**.

Rappel : la cascade de prix des devis n'utilise de toute façon pas `list_price` mais des champs
Studio sur `crm.lead` (voir [prix_devis/README.md](prix_devis/README.md)).

---

## Q4 — Rapprochement des fournisseurs source

*Bloque P4. Défaut : le mapping proposé tel quel.*

55 valeurs `FRS` distinctes dans le fichier source, ramenées à **30 partenaires** après fusion des
doublons de casse (`BLUE AUTO` / `Blue Autos` / `BLUE AUTOS`, `AUTOS GM` / `AUTO GM` / `Auto GM`,
`A+ GLASS` / `A+ Glass`, `SOCAUMAR` / `Socaumar`). L'orthographe retenue est la plus fréquente dans
la source. 16 valeurs sont exclues : toutes les variantes VSF (D10) et celles qui ne désignent pas un
fournisseur (`-`, `??`, `INVENTAIRE`, `CLIENT`, `Palette a identifier`, `Centre`, `OCCASION`,
`CENTRALE CASSE`).

Le rapprochement effectif avec les partenaires Odoo existants **n'a pas été validé par le client**.
Le détail est dans [suppliers_mapping.csv](suppliers_mapping.csv), à relire ligne à ligne.

---

## Q5 — Statuts `Réservé` et `Cassé` dans le processus cible

*Ne bloque pas l'import. À trancher avant la mise en service.*

- **`Réservé`** : réservation via commande client, emplacement interne dédié, statut personnalisé, ou
  simplement le processus standard devis → commande → livraison ?
- **`Cassé`** : sortie par rebut, conservation dans l'emplacement `Casse` (D14), ou stock non
  disponible ? Valorisé ou dévalorisé comptablement ?

Point d'attention : l'export CSV ne conserve pas les couleurs Google Sheets. Les statuts visuels
rouge/orange/jaune utilisés pour vendu/réservé/cassé doivent être récupérés autrement s'ils ne sont
pas matérialisés dans une colonne.

---

## Q6 — Droits et obligation de livraison

*Ne bloque pas l'import.*

- Qui peut ajuster un stock, valider un inventaire ?
- Comment rendre l'étape de livraison obligatoire sur les articles stockables **sans** bloquer les
  factures composées uniquement de main-d'œuvre ?

---

## Q7 — Sort des 49 emplacements sous `A controler`

*Reporté par décision du 2026-08-05 (D13), sans échéance.*

Cellules multi-racks, libellés non codifiés, statuts, entrepôts sans emplacement précis — dont
`Centre`, la plus grosse valeur du fichier avec 1 320 lignes, dont la nature reste inconnue. La liste
complète est imprimée par la phase `locations`. Le rejeu de la phase les déplacera sans créer de
doublon une fois la réponse connue.

---

## Q8 — Usage précis du Camion et retours

*Dépend de Q1.*

- Qui prépare le chargement et à quelle fréquence : manuel chaque matin, ou règle automatique ?
- Que devient un article chargé mais **finalement non posé** chez le client — retour vers quel
  emplacement ?
- Un projet ou un suivi des interventions existe-t-il déjà à RPBM, sur lequel brancher les tâches de
  pose sur site (D16) ?

---

## Q9 — Une vente d'un comptoir peut-elle réserver le stock de l'autre comptoir ?

*Ouverte le 2026-08-06. Ne bloque pas l'import : l'arbre cible décrit plus bas accommode les deux
réponses. Ce qui doit être fait au bon moment, c'est **la forme de l'arbre**, au moment du
correctif du `lot_stock_id` — pas la réponse elle-même.*

### Le problème

L'entrepôt unique réserve sur **tout l'arbre** placé sous la source de la règle de livraison. C'est
ce qui produit le « un seul document par vente » qui fait sa force. C'est aussi ce qui fait qu'une
vente à **Galleria** peut réserver une pièce physiquement présente à **Genipa** : la pièce est
trouvée, la commande est servie, et **le déplacement d'un site à l'autre n'est matérialisé par
aucun document**. Le bon de livraison porte l'emplacement source ligne par ligne — l'information
est là, rien ne l'impose.

Ce n'est pas un défaut de configuration à corriger : c'est un arbitrage. **Odoo n'offre aucun moyen
d'exclure un emplacement de la réservation** — `stock.quant._gather` filtre en `child_of`
(`stock/models/stock_quant.py:813-819`) et `stock.location` n'a aucun champ de ce type. Les deux
seuls leviers sont la **forme de l'arbre** et le `location_src_id` de la règle.

### Les deux réponses possibles

| | A — Pool unique | **B — Pool par comptoir** *(défaut retenu le 2026-08-06)* |
|---|---|---|
| Source de la règle comptoir | `RPBM/Stock` | `RPBM/Stock/Galleria`, plus une règle amont `RPBM/Stock/Dépôts` → comptoir |
| Documents pour F1 (dépôt → pose au comptoir) | **1** | **2** : transfert interne, puis livraison |
| Documents pour F3 (le flux dominant, 82 % du catalogue) | 2 | **3** : réception, transfert, livraison |
| Documents pour F9 (vente sur le stock du comptoir) | 1 | 1 — **inchangé** |
| Vente Galleria d'une pièce présente à Genipa | servie, mais **le transfert inter-sites n'est pas documenté** | **la pièce n'est pas vue** : `mts_else_mto` déclenche un achat VSF d'une pièce déjà possédée |
| Vente Galleria d'une pièce présente **au dépôt** | servie directement | servie **via la règle amont** — les dépôts restent accessibles aux deux comptoirs |
| Transfert dépôt → comptoir | implicite, porté par la ligne du bon de livraison | tracé par un document |
| Charge de saisie | minimale | un document de plus sur le flux **nominal** |

Aucune n'est gratuite. Avec 578 références en stock et 1,33 unité de moyenne, « racheter une pièce
qu'on possède à l'autre comptoir » n'est pas un cas d'école ; à l'inverse, un stock qui se déplace
sans trace entre deux sites recevant du public n'est pas neutre non plus.

### Le défaut retenu : B — pool par comptoir *(2026-08-06)*

**Une vente comptoir ne réserve pas le stock de l'autre comptoir.** C'est le défaut du projet
jusqu'à décision contraire du client.

**Ce que cela ne veut pas dire.** Le comptoir **garde accès aux dépôts** : la chaîne à deux règles
puise d'abord dans le comptoir, puis dans les dépôts, puis déclenche l'achat. Seul le stock de
**l'autre comptoir** est hors d'atteinte. C'est le seul découpage que l'arbre permette d'exprimer,
et il correspond exactement à l'intention.

**Ce que cela coûte, sans arrondi** : un document de plus sur F1 (le cas nominal) **et** sur F3
(82 % du catalogue). F9, le flux le plus fréquent en volume, n'est pas touché. L'écart avec les
5 entrepôts se resserre sur F1 — 2 documents contre 3, au lieu de 1 contre 3 — sans que la
recommandation change, les autres coûts des 5 entrepôts restant entiers.

**Ce que cela apporte** : le déplacement dépôt → comptoir devient un document, alors que la
description métier de F1 le mentionne déjà comme une étape physique distincte ; et faire livrer un
fournisseur directement au comptoir économise désormais deux documents au lieu d'un, ce qui
renforce l'intérêt du traitement A.

**À vérifier en préproduction** : ce qu'Odoo fait quand l'acheteur bascule « Livrer à » sur un
achat déjà rattaché à une chaîne `Dépôts → comptoir` planifiée. Ce comportement n'a pas été testé.

### Ce qui est déjà tranché et ne fait pas partie de la question

**Le camion sort de `Stock`.** Le placer en frère et non en enfant suffit à ce qu'aucune vente au
comptoir ne réserve une pièce chargée dans un véhicule en tournée. Cela ne coûte rien : la route
camion nomme explicitement sa source et sa destination. C'est une recommandation technique, pas un
arbitrage client.

### Ce qu'il faut décider maintenant, et ce qui peut attendre

Le correctif du `lot_stock_id` impose de toute façon de reconstruire l'arborescence. En y
interposant un niveau **`Dépôts`** au-dessus de Dépôt 1 et Dépôt 2, **l'arbre supporte les deux
réponses** — A et B ne diffèrent alors que par le `location_src_id` de deux règles, soit un champ,
réversible à tout moment.

Avec le défaut B, ce niveau `Dépôts` n'est plus une précaution mais un **prérequis** : c'est la
source de la règle amont vers les comptoirs.

**Donc : construire l'arbre ainsi maintenant, et retenir B par défaut.** Ce qui doit être fait
avant l'import, c'est la forme de l'arbre — la réponse elle-même reste révisable d'un champ. La
question demeure posée au client, mais elle ne bloque plus.

### Question à poser

> Quand une pièce vendue à Galleria se trouve en réalité à Genipa, que fait RPBM aujourd'hui :
> quelqu'un va la chercher, ou on en commande une autre ? Et souhaitez-vous que ce déplacement
> laisse une trace dans Odoo ?

Détail technique et arbre cible :
[architectures-stock.md § I.7](architectures-stock.md#i7-le-périmètre-de-réservation--une-décision-de-plus-à-poser-au-client).
