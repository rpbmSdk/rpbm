# Questions à trancher avant l'import du catalogue

Date : 2026-07-30 — destinataire : RPBM

> **Mise à jour du 2026-08-05 — les trois questions bloquantes sont tranchées.**
> Réponses RPBM consignées dans [Réponses_rpbm.md](Réponses_rpbm.md) :
> **Q3** coût *standard* + valorisation *manuelle* (AVCO écartée : Odoo réécrirait le `PRIX RV`
> importé à chaque réception) · **Q5** `R101`-`R336` → Dépôt 1, `R401`-`R937` / `J…` / `T…` →
> Dépôt 2, le reste ignoré sous `A controler` · **Q6** valeurs ambiguës ignorées ·
> **Q7** `VSF Centre` et `VSF Ouest` = `res.partner` id **5708** · **Q10** fret supposé inclus
> dans `PRIX RV`, à confirmer avant l'écriture des coûts.
> **Q2** est sans objet : les données d'audit passent en note interne sur le produit (chatter),
> pas dans des champs Studio dédiés.
>
> **Une question nouvelle et structurante s'est ouverte : [Q11](#q11--entrepôts-distincts-ou-zones-dun-même-entrepôt--structurante)** —
> 5 entrepôts distincts ou 1 entrepôt à 5 zones. Elle absorbe Q4 et conditionne P2 et P3. Elle
> signale aussi un défaut à corriger avant tout import : aujourd'hui, seules 8 % des unités en
> stock sont réservables par une commande client.
> Reste ouvert par ailleurs : Q1, Q8, Q9, qui ont toutes une option par défaut.

L'import du catalogue articles et des emplacements vers Odoo est prêt techniquement. Les scripts
sont écrits, testés à blanc sur la préproduction, et n'écrivent rien tant qu'on ne le demande pas
explicitement. **Ce qui manque, ce sont des décisions métier.**

Ce document liste les 10 questions restantes. Pour chacune : ce qui bloque, ce qu'on fait si vous
ne répondez pas, et ce que chaque réponse implique concrètement.

Les décisions déjà prises (catégories, entrepôts, coût = `PRIX RV`, prix fournisseur pour tous les
fournisseurs) sont conservées dans [questions_rpbm.md](questions_rpbm.md) et ne sont pas
re-posées ici.

**Trois questions sont bloquantes au sens strict** — Q3, Q7 et Q10 : sans réponse, l'étape
correspondante ne peut pas être lancée du tout. Les autres ont une option par défaut qui permet
d'avancer.

---

## Q1 — Le module `rpbm_agent` peut-il devenir visible aux équipes ?

*Bloque : P0 (prérequis).*

Le widget de recherche véhicule doit être installé sur Odoo **avant** l'import du catalogue, pour
qu'il crée une seule fois le champ technique qui relie chaque article à son eurocode. Mais
l'installer rend aussi visible son bouton et son écran à tous les utilisateurs Odoo, avant que ses
propres travaux ne soient terminés.

- **Par défaut** : on installe. Le champ est déjà présent en préproduction, l'impact est donc
  limité.
- **Si vous préférez attendre** : un script séparé peut créer uniquement le champ, sans activer le
  widget. C'est un peu plus de travail mais sans conséquence pour l'import.

---

## Q2 — Où conserver les informations d'historique du fichier Excel ?

*Bloque : P0 (prérequis), P5 (produits).*

Le fichier source contient des colonnes qui ne correspondent à rien dans Odoo mais qu'il serait
dommage de perdre : `AUTRE CODE`, `EUROCODE INTERNE`, le fournisseur d'origine, les emplacements
historiques, les notes d'inventaire.

- **Par défaut** : on crée quatre champs dédiés sur la fiche article, visibles mais non modifiables
  par les utilisateurs courants.
- **Attention** : ces informations ne peuvent **pas** aller dans le champ « Notes internes » de la
  fiche article. La synchronisation automatique avec VSF réécrit ce champ à chaque passage : les
  données y seraient effacées sans avertissement, article par article.
- **Si vous ne voulez pas de ces champs** : l'import se fait sans, et l'historique reste uniquement
  dans le fichier Excel.

---

## Q3 — Comment valoriser le stock ? 🚧 **Bloquante**

*Bloque : P1 (catégories) et P7 (coûts).*

Trois décisions liées, sur lesquelles nous ne pouvons pas nous substituer à votre comptabilité :

1. **Méthode de coût** : FIFO (premier entré, premier sorti) ou coût moyen pondéré ?
2. **Valorisation manuelle ou automatisée ?** En automatique, chaque mouvement de stock génère une
   écriture comptable. C'est plus rigoureux, mais cela suppose que le paramétrage comptable soit
   juste dès le départ.
3. **Comptes comptables** à utiliser pour la valorisation, l'entrée et la sortie de stock.

**Pourquoi c'est bloquant** : écrire les coûts d'achat sur 3 220 articles déclenche, en mode
automatisé, autant de mouvements de valorisation. Le faire avant d'avoir arrêté la méthode
obligerait à tout reprendre, avec des écritures comptables déjà passées.

En attendant, les catégories sont créées avec les valeurs par défaut d'Odoo et aucun coût n'est
écrit.

---

## Q4 — Que faire des emplacements déjà en place dans Odoo ?

*Bloque : P2 (entrepôts).*

Vous avez validé la création de 5 entrepôts distincts : Galleria, Genipa, Dépôt 1, Dépôt 2, Camion.

Mais Odoo contient déjà un entrepôt unique `RPBM` avec **434 emplacements** rangés sous
`Stock D1` et `Stock D2`. Transformer D1 et D2 en entrepôts autonomes n'est pas une création :
c'est une restructuration de l'existant, avec un risque de perdre le rattachement des articles qui
s'y trouvent.

- **Par défaut** : on crée les 5 nouveaux entrepôts **à côté** de l'existant, sans y toucher. Les
  deux structures coexistent le temps de la validation.
- **Question ouverte** : que deviennent ensuite les 434 emplacements existants — déplacés sous les
  nouveaux entrepôts, ou conservés en l'état et abandonnés progressivement ?

---

## Q5 — Quels racks appartiennent au Dépôt 1, et lesquels au Dépôt 2 ?

*Bloque : P3 (emplacements).*

⚠️ **Cette question vous a été posée sur des chiffres faux, nous en sommes désolés.** La
formulation précédente parlait de « 7 blocs de racks, de R101 à R728 ».

Le comptage réel du fichier donne **10 blocs**, et environ 110 emplacements de plus :

| Bloc | Plage réelle | Nombre |
|---|---|---:|
| R1xx | 101 à 136 | 36 |
| R2xx | 201 à 236 | 36 |
| R3xx | 301 à 336 | 36 |
| R4xx | 401 à 436 | 36 |
| R5xx | 501 à 538 | 38 |
| R6xx | 601 à 642 | 39 |
| R7xx | 701 à **739** | 39 |
| **R8xx** | 801 à 837 | 37 |
| **R9xx** | 900 à 937 | 38 |
| `R35` | isolé | 1 |

La numérotation n'est donc **pas une plage continue** : dire « de R101 à RXX pour le Dépôt 1 » ne
s'applique pas. Merci d'indiquer, **bloc par bloc**, lequel va au Dépôt 1 et lequel au Dépôt 2. Même
question pour les emplacements commençant par `J` et par `T`.

- **Par défaut** : les 538 emplacements sont créés dans Odoo sous un emplacement d'attente nommé
  `A contrôler`. Rien n'est perdu, rien n'est inventé, et il suffira de relancer l'import une fois
  votre réponse connue pour qu'ils soient déplacés au bon endroit — sans doublon.

---

## Q6 — Que sont `Centre`, `Tringle` et `CASSE` ?

*Bloque : P3 (emplacements).*

- **`Centre`** — c'est la plus grosse valeur du fichier avec **1 320 lignes**, et nous ne savons
  pas ce que c'est : un entrepôt, une zone à l'intérieur d'un entrepôt, ou autre chose ? De quel
  entrepôt dépend-elle ?
- **`Tringle`** — même question, volume plus faible.
- **`CASSE`** — nous partons du principe qu'il s'agit d'articles cassés qui **ne doivent pas
  compter dans le stock vendable**. Confirmez-vous ? Et ces articles doivent-ils rester valorisés
  comptablement, ou être sortis du stock ?

- **Par défaut** : `Centre` et `Tringle` vont sous `A contrôler` comme les autres ; `CASSE` est
  créé en emplacement de rebut, exclu du stock vendable.

---

## Q7 — `VSF Centre` et `VSF Ouest` : un seul fournisseur ou plusieurs ? 🚧 **Bloquante**

*Bloque : P4 (fournisseurs) et P6 (tarifs).*

VSF représente **89 % des lignes** du fichier (8 943 lignes), sous plusieurs libellés : `VSF
Centre`, `VSF Ouest`, `VSF Sud`, `VSF Sud-Ouest`, et quelques variantes d'orthographe.

Dans Odoo, il n'existe **qu'un seul fournisseur VSF** : `VSF - VITRO SERVICE FRANCE`. Et le module
de recherche véhicule est configuré pour travailler avec celui-là précisément.

**Pourquoi c'est bloquant** : si nous créons un second fournisseur « VSF Centre », les articles se
retrouveront avec deux prix VSF concurrents. Le module ne saura plus lequel mettre à jour et
**cessera de fonctionner** sur ces articles — définitivement, jusqu'à intervention manuelle.

- **Réponse attendue** : tous les libellés VSF désignent-ils bien le même fournisseur (auquel cas
  on rattache tout au fournisseur existant), ou `VSF Ouest` est-il un compte réellement distinct
  avec ses propres conditions ?
- **Par défaut** : on rattache tout au fournisseur existant. C'est l'hypothèse retenue dans les
  scripts, mais elle mérite une confirmation explicite vu l'ampleur.

---

## Q8 — Consommables : suivis en stock ou non ?

*Bloque : P5 (produits).*

Pour les consommables d'atelier (kit colle, gel capteur, agrafes, cales pare-brise), trois régimes
possibles :

1. **Stock réel strict** : chaque unité entrée et sortie est comptée.
2. **Consommable non valorisé** : acheté et consommé, sans suivi de quantité.
3. **Achat simplifié** : pas de suivi unitaire du tout.

- **Par défaut** : tous les articles issus du fichier sont importés en article stockable. Le
  fichier source ne contient de toute façon presque pas de consommables — la question porte surtout
  sur ce que vous saisirez **après** la migration.

---

## Q9 — 43 références au format douteux : les reprendre ou les laisser ?

*Bloque : P5 (produits).*

Sur 3 272 références, **43 (1,3 %)** ont un « eurocode » qui n'en est visiblement pas un :

| Exemple réel | Problème |
|---|---|
| `52185922 (CODE CONSTRUCTEUR)` | annotation entre parenthèses |
| `A1769064900 (REF XGLASS)` | la donnée se désigne elle-même comme autre chose |
| `8374LGNH5FDW-PERDU` | suffixe de statut |
| `K137 / 355558132 / 356408132` | trois codes concaténés |
| `17/03 : COTTET Eric` | une date et un nom de client |
| `eurocode corrigé` | texte libre |

Ces articles **seront bien importés** — ils gardent leur référence telle quelle. Mais ils ne
recevront pas le code qui permet la mise à jour automatique depuis VSF : le module ne saurait pas
les retrouver. Ils resteront donc **hors synchronisation VSF de façon permanente**, jusqu'à ce que
quelqu'un corrige la référence à la main.

- **Par défaut** : on les importe tels quels et on accepte cette limite. 1,3 % du catalogue.
- **Alternative** : nous vous fournissons la liste des 43 pour correction avant l'import. C'est
  environ une demi-journée de travail de votre côté.

---

## Q10 — Le fret entre-t-il dans le coût des articles ? 🚧 **Bloquante**

*Bloque : P7 (coûts).*

Le fichier contient une colonne `FRET` et une colonne `VALEUR (Av Fret)`. Le coût retenu pour Odoo
est `PRIX RV` (votre décision du 23/07).

**Question** : `PRIX RV` inclut-il déjà le fret, ou faut-il le rajouter ? Et si oui, selon quelle
règle de répartition par article ?

Cette question avait été posée quand le coût envisagé était `PRIX ACHAT` ; elle doit être
reconfirmée maintenant que c'est `PRIX RV`.

- **Pas de réponse par défaut possible** : écrire un coût sans savoir s'il est complet fausse la
  valorisation du stock dès le premier mouvement, avec un impact comptable.

---

## Q11 — Entrepôts distincts ou zones d'un même entrepôt ? 🚧 **Structurante**

*Bloque : P2 (entrepôts) et P3 (emplacements). Remplace et élargit Q4.*

La décision du 23/07 prévoit **5 entrepôts Odoo distincts** (Galleria, Genipa, Dépôt 1, Dépôt 2,
Camion). L'alternative est **un entrepôt unique** dont ces 5 sites sont des zones de stockage
(emplacements). Le choix est structurant et coûteux à défaire une fois que des mouvements existent.

### Le raisonnement, à partir des données

La forme du stock commande la réponse. Mesuré sur le fichier source :

| | |
|---|---:|
| Références au catalogue | 3 273 |
| Références avec du stock | **578 (18 %)** |
| Unités en stock | 767 |
| Moyenne quand il y a du stock | 1,33 unité |
| Références à **une seule** unité | 452, soit **78 %** de celles en stock |
| Références présentes sur les deux dépôts | 213 |

**Ce n'est pas un stock de distribution, c'est un stock de pièces quasi uniques.** 82 % du
catalogue est à zéro et se commande chez VSF à la demande. Trois conséquences directes :

1. **Aucune logique de réapprovisionnement par anticipation n'a de sens.** On ne maintient pas un
   stock plancher sur 3 273 pare-brise qui partent à l'unité. Les règles de réassort
   (`stock.warehouse.orderpoint`, qui acceptent pourtant bien un `location_id`, donc utilisables
   par zone) seraient du paramétrage mort. Le flux est piloté par la commande, pas par le stock.
2. **Les stratégies de sortie (FIFO, « au plus proche ») sont largement sans objet** : avec une
   seule unité dans 78 % des cas, il n'y a rien à arbitrer, il y a un seul endroit où aller la
   chercher.
3. **Ce qu'il faut optimiser, ce n'est pas le réapprovisionnement, c'est le fait de localiser et
   d'aller chercher la pièce.** Toute la machinerie de routes inter-entrepôts répond à un problème
   que RPBM n'a pas, au prix de documents supplémentaires sur un problème qu'il a.

C'est ce constat qui oriente la recommandation, davantage que les considérations théoriques
d'architecture.

### Défaut à corriger dans les deux cas

L'entrepôt `RPBM` actuel a son emplacement de stock principal (`lot_stock_id`) positionné sur
`RPBM/Stock D1`. Or `GALLERIA`, `GENIPA` et `Stock D2` sont des **frères** de `Stock D1`, pas des
enfants. Une commande client ne peut donc réserver que ce qui se trouve sous `Stock D1` :
**67 unités sur les 799 en stock**, soit 8 %. Le reste apparaît indisponible alors qu'il existe.

À corriger avant tout import, quelle que soit la configuration retenue.

### Ce que ça change à l'usage

| | 5 entrepôts | 1 entrepôt, 5 zones |
|---|---|---|
| Vente d'un article stocké ailleurs | route de réapprovisionnement + transit : **2 à 3 documents** | réservation sur tout l'arbre : **1 bon de livraison** |
| Types d'opération et séquences | 5 jeux à maintenir | 1 seul |
| Transfert entre sites | imposé par le modèle à chaque vente | fait quand on déplace réellement du stock |
| Stock par site en reporting | natif | par filtre sur l'emplacement |
| Réception fournisseur par site | possible, avec adresse propre | centralisée |

### Traitement comptable : **aucune différence entre les deux configurations**

C'est le point contre-intuitif, et il est vérifié dans le code d'Odoo 17 :

1. **Les comptes de valorisation ne sont portés ni par l'entrepôt ni par l'emplacement.** Ils sont
   définis sur la **catégorie d'articles** (`property_stock_account_input/output/valuation`), par
   société. `stock.warehouse` n'a aucun champ comptable. `stock.location` en a deux
   (`valuation_in_account_id`, `valuation_out_account_id`) mais leur aide précise explicitement
   *« This has no effect for internal locations »* — ils ne servent que pour des emplacements
   virtuels.
2. **Un mouvement interne ne génère jamais d'écriture.** Une écriture n'est produite que lorsque la
   marchandise entre dans la société ou en sort (`_is_in` / `_is_out`). Un emplacement interne est
   « valorisé » ; passer d'un emplacement valorisé à un autre ne change pas la valeur du stock de
   la société, donc rien n'est comptabilisé.
3. **Les transferts entre entrepôts d'une même société non plus.** Ils transitent par
   l'`Internal Transit Location`, qui porte la société — donc valorisée elle aussi. Le code le dit
   en toutes lettres : *« in case of routes making the link between several warehouse of the same
   company, the transit location belongs to this company, so we don't need to create accounting
   entries »*. Seul le transit **inter-sociétés** (sans société) déclencherait des écritures, et
   RPBM n'a qu'une société.
4. **Avec la valorisation manuelle retenue en Q3, aucune écriture n'est générée de toute façon**,
   dans l'une comme dans l'autre configuration.

**Conséquence** : le choix entre 5 entrepôts et 1 entrepôt est un choix **d'organisation logistique
et de charge de saisie**, pas un choix comptable. Il ne faut donc pas l'arbitrer sur des motifs
comptables — ils sont neutres.

### Le cas du Camion

Le camion effectue les poses **chez le client** : la marchandise quitte bien le stock à partir de
lui. Cela ne dicte pas pour autant d'en faire un entrepôt. Le schéma natif d'Odoo pour ce cas est
la **livraison en 2 étapes** (`pick_ship`) :

- *Préparation* : Stock → Camion — mouvement interne, la marchandise reste à vous, aucune écriture ;
- *Expédition* : Camion → Client — **c'est là qu'a lieu l'événement comptable**, à la pose.

Le Camion est alors l'emplacement de sortie de l'entrepôt (`wh_output_stock_loc_id`). Ce qui compte
comptablement est le second mouvement, identique que le Camion soit un entrepôt ou un emplacement.

L'étape intermédiaire n'est pas de la bureaucratie : un pare-brise chargé le matin et cassé en
route est une perte de stock qu'il faut pouvoir tracer et mettre au rebut **depuis le camion**.
C'est ce qui justifie les deux étapes pour les poses sur site, alors qu'une vente au comptoir n'en
a pas besoin.

### Différencier les ventes Galleria / Genipa

Le site de vente est une information **commerciale**, pas une information de stock — et le stock ne
« vit » de toute façon pas à Galleria ou Genipa, il est majoritairement en dépôt. Il ne faut donc
pas créer des entrepôts pour obtenir cette segmentation. Deux axes natifs, **indépendants de la
réponse à Q11**, donc décidables et implémentables tout de suite :

- **Le compte analytique** — `sale.order.analytic_account_id` existe nativement en Odoo 17, et sa
  valeur descend automatiquement sur les lignes de facture (`_set_analytic_distribution`,
  `sale_stock`/`sale`). Un plan analytique « Site » avec les comptes `Galleria`, `Genipa` (et
  `Camion` si les poses sur site doivent être isolées) donne le chiffre d'affaires, la marge et les
  charges par site **dans la comptabilité**, sans toucher à la structure de stock. C'est la façon
  canonique de segmenter une activité par site sous Odoo.
- **L'équipe commerciale** — `sale.order.team_id`, qui se propage depuis `crm.lead`. Le parcours
  passant déjà par le CRM via `rpbm_agent`, c'est presque gratuit : une équipe par site et les
  tableaux de bord ventes se segmentent seuls.

Les deux se cumulent : l'équipe pour le pilotage commercial, l'analytique pour la comptabilité.

### Organiser les transferts dépôts → Galleria / Genipa / Camion

Puisqu'il n'y a rien à réapprovisionner par anticipation (voir le raisonnement ci-dessus), les
transferts sont **réactifs, déclenchés par la commande**. Deux schémas, selon qu'il faille ou non
une trace de l'aller-chercher :

**A — Un seul document.** La livraison puise directement dans l'emplacement du dépôt. La ligne
indique `R412 / D2`, le préparateur y va et valide. Pas de transfert interne. Adapté à la vente au
comptoir, où la même personne fait tout.

**B — Livraison en deux étapes** (`pick_ship`), quand il faut une trace : *Préparation*
Dépôt → Camion, puis *Expédition* Camion → Client.

Ces deux schémas coexistent dans une même configuration : le choix se fait **à la ligne de
commande**, pas au niveau de l'entrepôt (voir la section suivante).

Deux compléments qui font gagner du temps sans automatisation lourde :

- **Transferts par lot** (`stock_picking_batch`, module standard en 17) : si quelqu'un fait le tour
  de D1 et D2 le matin pour la journée, les préparations du jour se regroupent en un seul lot —
  une seule sortie physique, un seul document à valider. C'est là qu'est le gain, pas dans des
  routes automatiques.
- **Règles de rangement** (`stock.putaway.rule`) : routent automatiquement une réception VSF vers
  le bon rack, par catégorie ou par article, ce qui évite de choisir l'emplacement à chaque
  réception.

### Sélectionner la destination à la préparation (comptoir ou camion)

C'est le point qui demande une méthode, et non un simple paramétrage. À la prise de commande, le
client choisit une pose sur site ou un passage au comptoir ; la préparation doit acheminer la
marchandise au bon endroit.

**Mécanisme retenu : deux routes sélectionnables à la ligne de commande.**

| Route | Étapes | Documents |
|---|---|---|
| « Retrait / pose au comptoir » | Stock → Client | 1 |
| « Pose sur site (Camion) » | Stock → Camion, puis Camion → Client | 2 |

Les deux routes portent `sale_selectable = True` (`sale_stock/models/stock.py:12`),
ce qui les rend proposables dans le champ `route_id` de la ligne de commande
(`sale.order.line.route_id`, domaine `[('sale_selectable', '=', True)]`). La route posée sur la
ligne **prend le pas** sur celles de l'article et de sa catégorie
(`product_routes = line.route_id or (product.route_ids + product.categ_id.total_route_ids)`), et
elle est transmise au réapprovisionnement via `'route_ids': self.route_id`. Le comportement est
donc déterministe, natif, et ne demande aucun développement.

**Pourquoi pas autre chose :**

- *Règles de rangement* : elles ne s'appliquent qu'aux entrées. Sans objet ici.
- *Entrepôt sur la commande* (`warehouse_id`) : imposerait de faire du Camion un entrepôt, ce que
  la présente question écarte.
- *Type d'opération* : ne pilote pas le réapprovisionnement, seulement la présentation.
- *Changement manuel de l'emplacement sur la préparation* : fonctionne, mais ne conserve aucune
  trace de l'intention commerciale et repose sur la mémoire du préparateur.

**Le point de vigilance, à traiter avant la mise en service** : `route_id` est un champ **de
ligne**, pas de commande. Un dossier comporte plusieurs lignes (pare-brise, joint, main-d'œuvre) et
les renseigner une par une est une source d'erreur — si la route est oubliée, la marchandise reste
au comptoir et le technicien part sans la pièce. Trois façons de le couvrir, par ordre de coût :

1. **Choix à la ligne, avec une valeur par défaut bien choisie.** La route majoritaire est posée
   par défaut ; on ne renseigne que l'exception. Coût nul, mais suppose de connaître la répartition
   réelle entre poses au comptoir et poses sur site.
2. **Un champ « Mode de pose » sur la commande + une automatisation** qui recopie la route sur les
   lignes stockables. Cohérent avec les automatisations Studio déjà en place chez RPBM.
3. **Pose de la route par le widget `rpbm_agent`**, au moment où il ajoute l'article à la commande
   (`addArticleToSaleOrder`). C'est l'endroit le plus juste — la donnée est saisie une fois, là où
   l'article entre — mais cela demande une évolution du module.

Commencer par (1), mesurer si l'oubli se produit réellement, et n'automatiser qu'ensuite.

**Questions :**

1. **Galleria et Genipa reçoivent-ils des livraisons fournisseur en direct**, chacun à sa propre
   adresse, ou tout arrive-t-il à un point central ?
2. **Avez-vous besoin de numérotations de documents distinctes par site** (bons de livraison,
   réceptions), ou une numérotation unique convient-elle ?
3. **Que doit-on pouvoir lire par site** : la valeur du stock, les quantités, les mouvements ? Un
   filtre par emplacement suffit-il, ou faut-il des états séparés ?
4. **Le chargement du camion doit-il laisser une trace** dans Odoo (préparation validée le matin),
   ou seule la pose chez le client doit-elle être enregistrée ?
5. **Quelle est la répartition entre poses au comptoir/atelier et poses sur site ?** Elle décide de
   la route posée par défaut sur les lignes de commande — on ne renseigne alors que l'exception.
6. **Le rattachement d'une vente à un site se fait-il par vendeur** (chacun est affecté à Galleria
   ou Genipa) **ou par commande** (un vendeur peut vendre pour les deux) ? Cela décide si la valeur
   analytique par défaut se pose sur l'utilisateur ou se choisit à la main.
7. **Galleria et Genipa tiennent-ils un stock de consommables à rotation rapide** (joints, produits
   d'atelier) ? Cette famille-là, contrairement au reste du catalogue, justifierait des règles de
   réassort par zone — la conclusion « aucun réapprovisionnement par anticipation » ne vaut que
   pour le catalogue vitrage.

**Recommandation** : un entrepôt unique avec les 5 sites en zones, sauf si la réponse à la question 1
ou 2 est oui. C'est la configuration qui produit un seul document par vente, supprime la phase P2 de
l'import, et fait disparaître la coexistence problématique décrite en Q4 — les 489 emplacements
migrés se rattachent directement à l'arborescence existante. Promouvoir plus tard une zone en
entrepôt reste possible ; démonter 5 entrepôts porteurs de mouvements l'est beaucoup moins.

La segmentation des ventes par site et la sélection de la destination à la préparation ne dépendent
d'aucun entrepôt supplémentaire : l'une passe par l'analytique, l'autre par une route à la ligne de
commande. Cela retire deux des arguments que l'on pourrait invoquer en faveur des 5 entrepôts. Il ne
reste réellement que la réception fournisseur en direct par site et les numérotations distinctes.

**Réserve sur les données** : le raisonnement s'appuie sur le fichier source de janvier 2025 et sur
l'état de la préproduction. Si les volumes réels ont sensiblement changé depuis, la question 7 est
celle qui peut faire bouger la conclusion.

---

## Récapitulatif

| # | Question | Bloque | Statut au 2026-08-05 |
|---|---|---|---|
| Q1 | Installer le module maintenant ? | P0 | Ouvert — défaut : oui (prérequis de P5) |
| Q2 | Champs d'historique | P0, P5 | **Sans objet** — note interne sur le produit |
| Q3 | Méthode de valorisation | P1, P7 | **Tranchée** — `standard` + `manual_periodic` |
| Q4 | Emplacements Odoo existants | P2 | Ouvert — défaut : coexistence |
| Q5 | Répartition des racks D1/D2 | P3 | **Tranchée** — R101-R336 / R401-R937, J…, T… |
| Q6 | `Centre`, `Tringle`, `CASSE` | P3 | **Tranchée** — ignorés sous `A controler` |
| Q7 | Identité du fournisseur VSF | P4, P6 | **Tranchée** — `res.partner` id 5708 |
| Q8 | Régime des consommables | P5 | Ouvert — défaut : stockable |
| Q9 | 43 références douteuses | P5 | Ouvert — défaut : importer, hors synchro |
| Q10 | Fret dans le coût | P7 | **Tranchée** — inclus dans `PRIX RV` (à confirmer) |
| Q11 | 🚧 Entrepôts distincts ou zones | P2, P3 | **Ouverte** — structurante, remplace Q4 |

**Q11 est la seule question réellement bloquante restante**, et elle l'est parce qu'elle est
difficile à défaire : elle décide de la forme des entrepôts et des emplacements. Q1, Q8 et Q9 ont
une option par défaut qui permet d'avancer. Q4 est absorbée par Q11.

**Prérequis technique qui subsiste** : `rpbm_agent` doit être installé avant la phase `products`,
sans quoi elle refuse de tourner — c'est son `pre_init_hook` qui crée `x_studio_eurocode`, la clé
sans laquelle les fiches migrées resteraient invisibles au widget et non synchronisables.
