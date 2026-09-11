# Migration stock RPBM vers Odoo

Date de cadrage : 2026-07-20  
Instance cible : Odoo preproduction RPBM  
Profil MCP autorise : `rpbm-preprod` uniquement

## Objectif

Preparer l'integration des articles et du stock actuellement suivis dans Google Sheets vers Odoo.

Le fichier de travail local est l'export CSV :

- `Gestion Stock V4 - Stock Complet.csv`
- derniere mise a jour indiquee dans le fichier : 29/01/2025

Le contexte metier est decrit dans :

- `procedure actuelle stock.md` (fichier source dans le dossier : nom avec accent sur "procedure")
- `infos.md`

Le fichier `procedure actuelle stock.md` decrit le fonctionnement historique. Le fichier `infos.md` ajoute maintenant le cadrage de migration : sources GRH, categories cibles, emplacements D1/D2, inventaire du 30/06/2026, parametrage stock/comptable et fichiers de travail a produire.

Sources GRH mentionnees dans `infos.md` :

| Tache | Sujet |
|---:|---|
| 1263 | RPBM - Gestion de stock |
| 1269 | RPBM - Valorisation des stock |
| 2079 | RPBM - Inventaire Stock Marchandises Juin 2026 |
| 251 | RPBM - Mise a Jour Statistiques Fichier Stock Rapid Pare-Brise Martinique |

## Regles de connexion Odoo

Toute lecture ou ecriture Odoo doit passer par la skill `paradigme-mcp`.

## Environnement Python du projet

L'environnement Python de reference est `pyenv 3.10.11`, deja fixe par le fichier `.python-version` a la racine du depot.

Le generateur de fichiers de migration de reference est maintenant `prepare_migration_files.py`, execute depuis ce dossier avec `pyenv exec python prepare_migration_files.py`. Le fichier `prepare_migration_files.ps1` est conserve comme ancien generateur et ne doit plus etre utilise pour les nouveaux exports.

Le profil explicite a utiliser est :

- profil : `rpbm-preprod`
- URL Odoo : `https://rpbm-pre-prod.odoo.com/`
- transport : `xmlrpc`
- source des identifiants : `~/.paradigme/.env`

Aucun secret ne doit etre copie dans ce dossier, dans le README, dans les notebooks ou dans les logs.

Etat au 2026-07-22 :

- le profil `rpbm-preprod` est present dans `~/.paradigme/paradigme_odoo_mcp.yaml`;
- les variables `RPBM_PREPROD_DB`, `RPBM_USERNAME` et `RPBM_PASSWORD` existent dans `~/.paradigme/.env`;
- le serveur MCP distant `https://mcp.odoo.paradigme.io/mcp` repond correctement;
- la lecture Odoo en `xmlrpc` avec `rpbm-preprod` est validee sur `product.template`, `product.category`, `stock.location` et `stock.warehouse`;
- aucune ecriture Odoo n'a ete effectuee.

Regle de securite de la phase actuelle : Odoo reste strictement en lecture seule. Les categories proposees sont documentees localement, mais aucune categorie ne doit etre creee, renommee ou supprimee dans l'instance tant qu'une demande d'ecriture explicite n'a pas ete confirmee.

Avant tout import, il reste a valider en lecture MCP :

- les champs de `product.product` et `stock.quant` necessaires au rapprochement final;
- les produits existants complets pour controler les doublons par `default_code`;
- les quantites et valorisations existantes avant tout ajustement initial.

## Etat Odoo preproduction

Lecture realisee le 22/07/2026 avec `paradigme-mcp` et le profil `rpbm-preprod` :

- 13 categories produits;
- 169 produits : la repartition par type doit etre relue avant import;
- 1 entrepot actif : `RPBM`;
- 438 emplacements internes, dont 434 sous `RPBM/Stock D1` et `RPBM/Stock D2`;
- politiques de valorisation mixtes selon les categories existantes : `average`/`real_time` et `standard`/`manual_periodic`.

La cible dispose donc deja d'une structure de stock D1/D2. Les emplacements source du CSV ne doivent pas etre recrees automatiquement avant rapprochement.

## Analyse du message gestionnaire

Le message confirme la cible métier et précise que les valeurs de la colonne `TYPE` ne doivent pas devenir automatiquement des catégories Odoo. La règle à retenir est une arborescence courte de 10 catégories métier :

`Pare-brise`, `Lunette`, `Glace latérale`, `Joint`, `Main d'oeuvre`, `Consommable`, `Film solaire`, `Autres`, `Services`, `Accessoires`.

Les regroupements confirmés sont :

- `Toit panoramique`, `VITRE PAVILLON`, `TOIT PANO`, `TOIT` vers le libellé article `Toit panoramique`, catégorie `Autres`;
- `JOINTS`, `ENJOLIVEURS` vers la catégorie `Joint`;
- `OPTIQUE`, `FAISCEAU`, `PHARE`, `ANTIBROUILLARD`, `FEU` vers la catégorie `Autres`;
- `CACHE RETRO`, `CACHE RETRO INT` vers le libellé article `Cache rétro`, catégorie `Autres`;
- `LEVE-VITRE`, `MECANISME LV`, `MECANISME` vers le libellé article `Lève-vitre`, catégorie `Autres`;
- `RETROVISEUR` doit être renommé `Rétroviseur EXT`; `RETROVISEUR INT` reste distinct comme libellé article.

Une catégorie `Camera` ne doit pas être créée : les articles rares ou exceptionnels vont dans `Autres`, sans sous-catégorie dédiée — cette exception reste valable.

Décision client du 2026-07-23 (revient sur la phrase précédente) : hormis `Camera`, les autres regroupements (`Rétroviseur EXT`, `Rétroviseur INT`, `Cache rétro`, `Lève-vitre`, `Toit panoramique`, `Optique`, `Baie de pare-brise`) deviennent bien des **sous-catégories Odoo** (`product.category`) imbriquées sous `Autres`, et non plus de simples règles de normalisation de nom de produit.

Correspondance avec la préproduction lue le 22/07/2026 : `Accessoires` et `Main d'Oeuvre` existent déjà sous `All / Saleable` et doivent être réutilisées. Les huit autres catégories métier sont absentes ou non équivalentes; elles sont seulement proposées dans `categories_odoo_proposition.csv` à ce stade.

## Procedure actuelle resumee

La gestion operationnelle du stock est actuellement realisee dans Google Sheets.

Odoo sert de reference pour les ventes, mais les mouvements physiques, les emplacements, les statuts vendu/reserve/casse et les controles d'inventaire sont encore suivis dans les fichiers.

Les controles attendus sont :

- rapprochement Odoo vers fichier stock environ tous les deux jours;
- rapprochement fichier stock vers Odoo;
- deux inventaires globaux par an;
- sondages trimestriels avec deux methodes : `book to physical` et `physical to book`;
- suivi des ecarts : article vendu non sorti, article sorti sans vente, emplacement incorrect, casse, reserve, doublon.

La cible Odoo doit permettre de supprimer le double suivi et d'historiser les mouvements.

## Structure du CSV

Le CSV n'est pas directement exploitable avec la premiere ligne comme en-tete.

Constats :

- lignes 1 a 4 : informations de synthese;
- ligne 5 : en-tetes de donnees;
- ligne 6 et suivantes : lignes articles;
- nombre de lignes de donnees detectees : 10 066;
- lignes avec `EUROCODE` principal renseigne : 10 063;
- eurocodes uniques : 3 292;
- eurocodes apparaissant sur plusieurs lignes : 1 358;
- lignes avec quantite actuelle positive : 768;
- quantite positive totale lue : 767,001;
- emplacements distincts renseignes : 568.

Colonnes principales a exploiter :

| Colonne CSV | Sens | Cible Odoo proposee |
|---|---|---|
| `No` | identifiant de ligne Google Sheets | reference d'audit import |
| `AUTRE CODE` | code alternatif | champ d'audit `x_studio_*` dedie (jamais `description`) |
| `EUROCODE` | reference article principale | `product.template.default_code` |
| `TYPE` | famille article | `product.category` |
| `DESIGNATION` | libelle article | `product.template.name` |
| `FRS` | fournisseur ou origine | fournisseur a rapprocher, sinon note |
| `QTE Act` | quantite actuelle | quantite de stock initiale |
| `PRIX BRUT` | prix catalogue | `list_price` si valide |
| `PRIX ACHAT` | cout achat | `product.supplierinfo.price` (prix fournisseur) |
| `PRIX RV` | cout retenu | `standard_price` (decision RPBM du 2026-07-23) |
| `VALEUR` | valeur ligne | controle de valorisation |
| `NB Sort` | nombre de sorties | information historique, non import stock direct |
| `FRET` | mode avion/bateau/inventaire | information achat/logistique |
| `DATE FACT` | date facture | historique, non stock initial |
| `PLACE` | emplacement physique | `stock.location` ou champ d'audit |
| `DATE SORTIE` | sortie/vendu | exclusion du stock initial si renseignee |
| `INV 13/12/2024` | controle inventaire | indicateur de fiabilite |
| `INV Notes` | notes inventaire | note d'audit |
| `INV ETAT` | etat inventaire | controle ecart/casse |

## Prix fournisseurs et cout de stock

Lors de la migration du catalogue, chaque article devra recevoir un prix fournisseur a partir de `PRIX ACHAT`, avec rapprochement de `FRS` vers un fournisseur Odoo. Le prix fournisseur est une donnee distincte du prix de vente et du cout de valorisation.

La lecture des lignes positives montre les relations suivantes :

- `PRIX ACHAT` est un prix unitaire fournisseur;
- `VALEUR (Av Fret)` correspond probablement a un montant de ligne avant fret : 760 lignes positives sur 768 suivent `QTE Act x PRIX ACHAT`;
- `VALEUR` correspond probablement a un montant de ligne base sur `PRIX RV` : 761 lignes positives sur 768 suivent cette formule. Elle ne doit pas etre utilisee directement comme cout unitaire;
- `PRIX RV` est superieur au prix achat dans les echantillons et ressemble a un prix de revente. Sa signification exacte doit etre confirmee : prix de revient ou prix de revente.

Decision client du 2026-07-23 : le cout Odoo (`standard_price`) est base sur la colonne `PRIX RV`, et non sur `PRIX ACHAT`. La signification exacte de `PRIX RV` (prix de revient ou prix de revente) n'a plus besoin d'etre tranchee pour l'import, puisque la colonne est retenue comme cout quel que soit son nom.

Regle provisoire (mise a jour) :

1. creer les prix fournisseurs avec `PRIX ACHAT` (reste la source pour le prix fournisseur, distinct du cout de stock);
2. utiliser `PRIX RV` comme cout unitaire Odoo (`standard_price`);
3. utiliser `VALEUR (Av Fret)` comme controle de valorisation ou pour recalculer un cout unitaire lorsque la quantite est connue;
4. si le fret doit entrer dans le cout, definir une allocation par article avant l'import (question a reconfirmer maintenant que le cout retenu est `PRIX RV`, la comparaison initiale portait sur `PRIX ACHAT`).

Decision a obtenir : le fournisseur correspondant a chaque valeur `FRS`, la methode FIFO/AVCO, et les formules de prix de vente (`list_price`) deja utilisees dans Odoo (le client renvoie sur l'existant Odoo plutot que sur une colonne du fichier source pour le prix de vente).

Precision sur le perimetre du prix de vente : la synchronisation VSF reecrit `list_price` avec le
prix public VSF (`product_sync_values()`). Pour les ~2 893 eurocodes fournis par VSF, toute valeur
`list_price` posee a l'import sera donc ecrasee des la premiere synchronisation. La question des
formules de prix de vente ne porte reellement que sur les ~400 references non-VSF. Rappel : la
cascade de prix des devis n'utilise de toute facon pas `list_price` mais des champs Studio sur
`crm.lead` (voir [`prix_devis/README.md`](prix_devis/README.md)).

Le prix fournisseur, lui, doit etre cree avec une `date_start` (cf. contraintes de synchronisation
de l'import catalogue) pour que l'historisation VSF fonctionne au lieu de se bloquer.

Attention : l'export CSV ne conserve pas les couleurs Google Sheets. Les statuts visuels rouge/orange/jaune utilises pour vendu/reserve/casse doivent etre recuperes autrement si ces informations ne sont pas materialisees dans une colonne.

## Inventaire de reference

`infos.md` introduit un inventaire plus recent que le CSV exporte le 29/01/2025.

Inventaire au 30/06/2026 :

| Indicateur | Montant |
|---|---:|
| Stock theorique | 106 745,23 EUR |
| Stock reel | 100 297,05 EUR |
| Ecart | 6 448,18 EUR |

Impact sur la strategie :

- le CSV V4 reste utile pour le referentiel articles, les prix, les categories et les emplacements historiques;
- le stock initial a importer doit s'appuyer sur le stock reel inventorie au 30/06/2026, ou sur un fichier corrige issu de cet inventaire;
- l'ecart de 6 448,18 EUR doit etre arbitre avant import comptable;
- les lignes marquees `Pas la`, `ERREUR`, vendu, reserve ou casse doivent etre exclues du stock disponible tant qu'elles ne sont pas resolues.

## Categories cibles

`infos.md` propose une cible plus precise que le premier nettoyage par `TYPE`.

Categories Odoo cibles :

| Categorie cible | Contenu rattache |
|---|---|
| Pare-brise | Pare-brise |
| Lunette | Lunettes |
| Glace laterale | Glaces laterales, custodes, deflecteurs |
| Joint | Joints, enjoliveurs |
| Main d'oeuvre | Temps MO 1, Temps MO 2 |
| Consommable | Kit colle, gel capteur, agrafes kit, cale pare-brise, produit connexe |
| Film solaire | Film solaire, film securitaire |
| Autres | Optique, retroviseur, toit panoramique, baie de pare-brise, cache retro, leve-vitre |
| Services | Frais d'identification, retraitement des dechets, nettoyage bris de glace, frais de deplacement, pose simple |
| Accessoires | Balai essuie-glace |

Note du 2026-07-23 : ce tableau presente `Autres` comme une categorie plate ; c'est desormais obsolete, voir la decision de sous-categorisation dans « Analyse du message gestionnaire » ci-dessus (`Optique`, `Retroviseur EXT`, `Retroviseur INT`, `Toit panoramique`, `Cache retro`, `Leve-vitre`, `Baie de pare-brise` sont de vraies sous-categories Odoo sous `Autres`).

Typologie Odoo :

- articles stockables : vitrages, joints, optiques, retros, toits, accessoires stockes;
- consommables : a arbitrer entre suivi stock reel, consommable simplifie ou achat/consommation sans suivi strict;
- services : non stockables.

## Nettoyage identifie

Les valeurs de `TYPE` doivent etre normalisees avant creation de categories.

Regroupements proposes :

| Type normalise | Valeurs source typiques |
|---|---|
| `PARE BRISE` | `PARE BRISE`, `PARE-BRISE`, variantes de casse ou espaces |
| `JOINTS` | `JOINTS`, `jOINTS`, `ENJOLIVEURS` |
| `GLACES LATERALES` | `GLACES LATERALES` |
| `LUNETTES` | `LUNETTES` |
| `TOIT PANORAMIQUE` | `TOIT`, `TOIT PANO`, `VITRE PAVILLON` |
| `RETROVISEUR EXT` | `RETROVISEUR` |
| `LEVE-VITRE` | `LEVE VITRE`, `MECANISME LV`, `MECANISME` |
| `OPTIQUE` | `OPTIQUES`, `FAISCEAU`, `ANTIBROUILLARD`, `FEU`, `PHARE`, `PHARES` |
| `AUTRES` | valeur vide, `CACHE RETRO`, `CAMERA`, cas non classes |

Repartition constatee apres normalisation sur les lignes avec eurocode :

| Type normalise | Lignes |
|---|---:|
| `PARE BRISE` | 5 295 |
| `JOINTS` | 2 162 |
| `GLACES LATERALES` | 1 534 |
| `LUNETTES` | 981 |
| `OPTIQUE` | 29 |
| `LEVE-VITRE` | 20 |
| `AUTRES` | 19 |
| `TOIT PANORAMIQUE` | 16 |
| `RETROVISEUR EXT` | 5 |
| `RETROVISEUR INT` | 1 |
| `BAIE DE PARE BRISE` | 1 |

Ces types sources doivent etre rattaches aux categories cibles ci-dessus, pas crees tels quels dans Odoo.

## Strategie de migration

La migration doit etre traitee en deux imports separes.

### 1. Import catalogue articles

Objectif : creer ou mettre a jour les produits Odoo sans mouvement de stock.

Cle de rapprochement :

- `EUROCODE` vers `default_code`;
- une seule fiche produit par eurocode;
- les lignes dupliquees par eurocode representent des quantites, des historiques de mouvement ou des emplacements, pas forcement des produits distincts.

Regles proposees :

- ignorer les lignes sans eurocode ou avec eurocode `0`;
- si `DESIGNATION` est vide, utiliser l'eurocode comme nom temporaire;
- convertir les prix avec virgule decimale;
- importer en produit stockable;
- rattacher la categorie issue de `TYPE` normalise;
- conserver `AUTRE CODE`, `FRS`, `FRET`, `No` et notes d'inventaire dans des champs d'audit dedies (`x_studio_*`), jamais dans le champ `description` (« Notes internes ») : voir la contrainte ci-dessous;
- renseigner `x_studio_eurocode` avec la reference eurocode lorsque `eurocode_format_valide` est vrai, laisser vide sinon;
- ne creer qu'une seule ligne `product.supplierinfo` active par couple produit/fournisseur, toujours avec une `date_start` renseignee (date de l'import);
- ne pas creer de categorie Odoo pour chaque valeur rare ou typo du fichier source;
- traiter `CAMERA` et les cas rares dans `Autres`, sauf decision metier contraire.

Avant creation, controler dans Odoo :

- les produits existants par `default_code`;
- les categories existantes;
- les champs disponibles selon la version Odoo;
- la politique de valorisation stock et la categorie comptable cible.

#### Contraintes imposees par la synchronisation VSF du module `rpbm_agent`

Depuis le 2026-07-30 (commits `0d24ff3` et `7e053a4`), `product.template` expose une
re-synchronisation VSF (`sync_vsf_information()`, `rpbm_agent/models/product_template.py`).
Elle ne cree plus seulement des produits : elle **reecrit** des champs de fiches existantes et
historise le prix fournisseur. Trois consequences directes pour l'import catalogue.

**1. Le champ `description` est ecrase, les donnees d'audit ne doivent pas y aller.**
`product_sync_values()` (`rpbm_agent/controllers/vsf.py:104-111`) reecrit `description` avec la
note HTML VSF. Or `product.template.description` est exactement le champ « Notes internes »
d'Odoo 17 (`addons/product/views/product_views.xml`, groupe `Internal Notes`). Le repli
« sinon dans une note interne » de la regle precedente detruisait donc silencieusement
`AUTRE CODE`, `FRS`, `FRET`, `No` et les notes d'inventaire des la premiere synchronisation.
Le mecanisme de creation des champs d'audit doit reutiliser `FIELDS_TO_ENSURE` de
`rpbm_agent/hooks.py` plutot que d'en dupliquer un.

**2. `x_studio_eurocode` est la cle de re-synchronisation, pas un champ d'audit.**
C'est la seule cle d'entree de la synchro (`product_template.py:113-115` : absent → `UserError`).
Un produit migre sans ce champ n'est pas seulement dupliquable par le widget : il est
**non synchronisable a vie**. La regle de format documentee plus bas (43 references sur 3 289
rejetees) a donc desormais un cout metier, et non plus seulement une valeur de precaution —
arbitrage client demande dans [`questions_rpbm.md`](questions_rpbm.md).

**3. Une seule ligne fournisseur VSF active, sinon la synchro se bloque.**
`_active_vsf_supplierinfo()` (`product_template.py:56-68`) leve une `UserError` des qu'il trouve
plus d'une ligne active pour `rpbm_agent.vsf_partner_id`, et une ligne sans `date_start` est
consideree active pour toujours. Une ligne VSF importee sans `date_start`, plus une ligne creee
par le widget, et la synchronisation de ce produit est definitivement bloquee. Avec `date_start`
renseignee, l'historisation J-1/J du module fait le bon travail seule a la premiere synchro :
le prix issu du CSV 2025 est cloture, le prix VSF du jour cree. Noter l'ecart de semantique
assume par cet historique : la migration ecrit `PRIX ACHAT` (2025), la synchro ecrit
`prixVenteRPBM` (= `prixVente x 0,8`) — ce ne sont pas la meme grandeur.

Ces contraintes ne concernent que le catalogue. `rpbm_agent` n'ecrit aucun stock Odoo (le module
ne depend pas de `stock` et ne touche jamais `stock.quant`), et la synchro n'ecrit ni
`standard_price` ni `categ_id` : elle ne repare donc pas les deux lacunes du widget documentees
dans [`../../docs/cartographie/reconciliation-stock-rpbm-agent.md`](../../docs/cartographie/reconciliation-stock-rpbm-agent.md).

### 2. Import stock initial

Objectif : creer une situation de stock initiale fiable dans Odoo, pas rejouer tout l'historique Google Sheets.

Regles proposees :

- ne pas importer les lignes avec `DATE SORTIE` renseignee comme stock disponible;
- importer uniquement les lignes avec quantite positive apres validation metier et rapprochement avec l'inventaire reel du 30/06/2026;
- rapprocher les lignes marquees `pas la`, `ERREUR`, casse ou reserve avant import;
- utiliser l'inventaire physique du 30/06/2026 comme source de verite prioritaire;
- ne pas se fier uniquement au CSV du 29/01/2025, car les utilisateurs indiquent que le stock n'est plus tenu correctement depuis 2023;
- preparer une table de stock initial par `EUROCODE` + `PLACE` + quantite.

La creation du stock initial dans Odoo devra passer par un mecanisme d'inventaire ou d'ajustement de stock valide en preproduction, pas par une creation directe non controlee de quants.

## Strategie emplacements

Le champ `PLACE` contient des valeurs heterogenes :

- emplacements rack : exemples `R203`, `R912`, `J8C`;
- entrepots source : `GALLERIA`, `GENIPA`;
- emplacements physiques : valeurs `JXX`, ainsi que d'autres codes de racks ou zones;
- valeurs a qualifier : `Centre`, `D2`, `CASSE`, `Tringle`;
- variantes d'accents ou de casse : `GALLERIA` / `Galleria`, `GENIPA` / `Genipa`.

La distinction entre entrepot et emplacement doit etre validee avant import. Le gestionnaire a precise que `GALLERIA` et `GENIPA` sont des entrepots, tandis que les valeurs `JXX` sont des emplacements. Il reste a obtenir la liste exhaustive des entrepots et emplacements, puis le rattachement de chaque emplacement a son entrepot parent.

Decision client du 2026-07-23, precisee le 2026-08-05 : `Galleria` et `Genipa` sont les entrepots principaux. Il existe en plus des entrepots deportes `Depot 1` et `Depot 2`, avec la repartition suivante :

- `R101` a `R336` -> Depot 1;
- `R401` a `R937` -> Depot 2;
- `J...` / `T...` -> Depot 2.

Les bornes tombent exactement sur la frontiere reelle des blocs (`R3xx` s'arrete a 336, `R4xx` commence a 401). Implemente dans `prepare_migration_files.place_warehouse()`, verifiable par `python prepare_migration_files.py --check`.

Decision client du 2026-07-23 (architecture entrepots) : `Galleria`, `Genipa`, `Depot 1`, `Depot 2` et `Camion` seront **5 entrepots Odoo distincts** (`stock.warehouse`), et non des emplacements imbriques sous l'entrepot unique `RPBM` actuellement en place. Ceci contredit la structure minimale proposee plus bas dans ce document (`RPBM / Stock / D1`, `D2`), qui doit etre revue : `D1`/`D2` existent deja en preproduction comme emplacements sous l'entrepot `RPBM` (434 emplacements), leur promotion en entrepots autonomes demande une restructuration de l'existant, pas une simple creation, et devra etre traitee avec prudence (pas d'ecriture directe non controlee).

La regle de creation des emplacements validee est un emplacement Odoo par reference distincte de la colonne `Place` (pas de regroupement par plage).

Structure reelle des racks : la numerotation `R` n'est pas une plage continue mais organisee en **9 blocs** par allee (`R1xx` 101-136, `R2xx` 201-236, `R3xx` 301-336, `R4xx` 401-436, `R5xx` 501-538, `R6xx` 601-642, `R7xx` 701-739, `R8xx` 801-837, `R9xx` 900-937, releves dans `locations_mapping.csv`). Les versions anterieures de ce document annoncaient 7 blocs s'arretant a `R728` : c'etait faux.

Traitement des valeurs non couvertes par la repartition (decision du 2026-08-05) : elles sont **ignorees**, c'est-a-dire creees sous `A controler` pour rattachement manuel ulterieur. Cela concerne les cellules multi-racks (`R108 - R109`, `R303 / R324`...), les libelles non codifies (`Tringle`, `Rack Plafond`, `JDESSUS`, `Palette Savon`...), les statuts (`PERDU`, `NON TROUVE`, `Vendu ?`...) et les valeurs designant un entrepot sans emplacement precis (`GALLERIA`, `Depot 2`...). La phase `locations` en imprime la liste complete.

Questions encore ouvertes :

1. Usage exact de l'entrepot `Camion` (quels mouvements y transitent).
2. Routes de transfert inter-entrepots Depot 1/2 -> Galleria/Genipa lors d'une vente (reapprovisionnement).
3. Modalites de la restructuration des emplacements `D1`/`D2` deja existants en preproduction vers de nouveaux entrepots autonomes.
4. Sort definitif des 49 emplacements laisses sous `A controler`.

Il faut ensuite definir une table de correspondance avant import :

| Source `PLACE` | Cible Odoo proposee |
|---|---|
| `Rxxx`, `Jxx`, `Txxx` | emplacement physique, entrepot parent a confirmer |
| `GALLERIA` / `Galleria` | entrepot source |
| `GENIPA` / `Genipa` | entrepot source |
| `Centre` | nature et entrepot parent a confirmer |
| `D2` | nature et rattachement a confirmer |
| `CASSE` | emplacement rebut/casse, pas stock vendable |

Question ouverte : le CSV ne permet pas de separer proprement D1/D2 pour toutes les places. La regle de rattachement depot -> rack doit etre confirmee avec les utilisateurs.

Structure Odoo minimale proposee par `infos.md` (obsolete, voir decision du 2026-07-23 ci-dessus) :

```text
RPBM / Stock
  D1 - Depot Lezarde
    R101
    R102
    ...
  D2 - Depot 2
    Rxxx
    ...
```

Cette structure traitait D1/D2 comme des emplacements sous un entrepot unique. Elle est remplacee par 5 entrepots Odoo distincts (`Galleria`, `Genipa`, `Depot 1`, `Depot 2`, `Camion`), chacun avec sa propre arborescence d'emplacements internes.

Regles :

- D1 correspond au depot Lezarde;
- D2 correspond au second depot de stockage;
- les informations d'acces physique, cles et reseau Wi-Fi ne doivent pas etre importees dans Odoo;
- les emplacements inconnus ou non resolus doivent aller dans une anomalie ou un emplacement temporaire `A controler`;
- l'emplacement `CASSE` ne doit pas contribuer au stock vendable.

## Parametrage stock et comptable

Le parametrage comptable doit etre valide avant tout import de stock valorise.

Decisions a obtenir :

| Sujet | Decision attendue |
|---|---|
| Methode de cout | FIFO ou AVCO |
| Valorisation | manuelle ou automatisee |
| Compte de valorisation | compte a creer ou confirmer |
| Compte d'entree stock | compte a creer ou confirmer |
| Compte de sortie stock | compte a creer ou confirmer |
| Couts logistiques | regle d'application aux bons de transfert |

Point d'attention : avec une valorisation automatique, les mouvements de stock peuvent generer des ecritures comptables. La preproduction doit etre controlee avant toute reprise en production.

## Controle qualite avant import

Fichiers de preparation a produire avant ecriture Odoo :

- `categories_mapping.csv` : correspondance `TYPE` source vers categorie Odoo;
- `locations_mapping.csv` : correspondance `PLACE` source vers emplacement Odoo;
- `suppliers_mapping.csv` : correspondance `FRS` source vers fournisseur Odoo (a creer ou reutiliser);
- `products_to_import.csv` : une ligne par eurocode;
- `stock_initial_to_import.csv` : une ligne par eurocode + emplacement;
- `locations_to_create.csv` : emplacements normalises manquants;
- `data_quality_report.md` : anomalies et arbitrages.

Fichiers generes le 22/07/2026 :

- `categories_mapping.csv` : 31 valeurs `TYPE` source mappees;
- `categories_odoo_proposition.csv` : 10 categories métier, action Odoo proposee et libelles d'articles rattaches;
- `locations_mapping.csv` : 568 valeurs `PLACE` source, avec statut de rapprochement;
- `products_to_import.csv` : 3 272 references candidates, hors references `-`, `---` et `?`. Depuis le 30/07/2026 le dedoublonnage porte sur l'`EUROCODE` **normalise** et non sur la chaine exacte : la source contient 17 paires de variantes de casse ou d'espacement du meme article (`2454ASMC` / `2454asmc`, `6084BGNRZ-O` / `6084BGNRZ - O`) qui auraient produit deux fiches Odoo pour une seule reference physique. Le fichier porte aussi le cout `PRIX RV` (colonne `cost_price`) et les codes d'audit `AUTRE CODE` / `EUROCODE INTERNE`;
- `product_reconciliation.csv` : comparaison des references candidates avec le catalogue Odoo par `default_code`;
- `suppliers_mapping.csv` (ajoute le 29/07/2026) : 55 valeurs `FRS` source distinctes, avec action de rapprochement Odoo proposee (reutiliser le partenaire VSF configure sur `rpbm_agent`, ou creer/rapprocher un `res.partner` pour les 54 autres fournisseurs). Decision RPBM du 29/07/2026 : le prix fournisseur (`product.supplierinfo` sur `PRIX ACHAT`) doit etre cree pour **tous** les fournisseurs, pas seulement VSF - le partenaire Odoo manquant doit etre cree si besoin.
- `stock_initial_to_import.csv` : modele vide, car le CSV 2025 n'est pas la source de verite du stock initial 2026;
- `data_quality_report.md` : rapport de controle genere a partir du CSV et de la lecture Odoo;
- `prepare_migration_files.py` : script Python reproductible de preparation locale;
- `prepare_migration_files.ps1` : ancien generateur PowerShell, conserve pour reference uniquement.
- `analyse_gestion_stock.ipynb` : notebook Jupyter d'analyse locale du CSV, sans connexion Odoo.
- `questions_rpbm.md` : liste consolidee des questions et validations a obtenir de RPBM, par theme.

Ajoutes le 30/07/2026, pour le passage a l'execution :

- [`plan-import-articles.md`](plan-import-articles.md) : plan phase par phase de l'import du catalogue et des emplacements (P0 a P8), avec conditions d'entree, commandes, controles et procedure de reprise;
- [`questions-import-articles.md`](questions-import-articles.md) : les 10 questions metier restantes, redigees pour etre envoyees a RPBM, avec ce que chacune bloque et l'option par defaut;
- `import_odoo.py` : script d'import XML-RPC, une sous-commande par phase. **N'ecrit rien sans `--commit`.** Identifiants externes systematiques (import rejouable), lots de 200 lignes, et une sous-commande `selfcheck` qui verifie la logique hors ligne.
- `routes_transferts_entrepots.md` : recherche documentaire Odoo (routes, reapprovisionnement inter-entrepots, cross-dock, routes specifiques de ligne de commande, suivi de service via Project) et proposition pour le reapprovisionnement Galleria/Genipa et les operations du camion de pose sur site. Revision du 2026-07-23 : la piste Field Service est ecartee (RPBM reste sur le circuit devis/commande classique), remplacee par un article de service (tache Project) combine a une route dediee sur les lignes stockables de la commande.

Le rapprochement `product_reconciliation.csv` du 20/07/2026 correspondait a l'ancien parsing PowerShell et doit etre regenere pour les 3 289 candidats produits par le script Python. Les 58 autres produits Odoo n'ont pas de reference interne exploitable.

Le notebook Jupyter valide le parsing du fichier CSV avec son en-tete multilignes et retrouve 10 066 lignes, 3 292 `EUROCODE` uniques et 568 emplacements. L'ancien script PowerShell produit actuellement des volumes differents; cet ecart doit etre resolu avant de regenerer les fichiers d'import.

### Fiabilite du champ EUROCODE (29/07/2026)

`prepare_migration_files.py` lit desormais aussi les colonnes brutes `FRS` (fournisseur), en plus des colonnes deja extraites. Un controle de format simple (alphanumerique + tiret, 4 a 15 caracteres) est applique a chaque `EUROCODE` : 43 references sur 3 289 echouent ce controle (annotations entre parentheses, suffixes `-PERDU`, texte libre comme des noms de client) et sont marquees `eurocode_format_valide=false` dans `products_to_import.csv`, avec une note dediee. Ces references restent utilisables comme reference interne mais ne doivent pas etre ecrites dans le champ Studio `x_studio_eurocode` du module `rpbm_agent` sans verification manuelle.

Une verification live des eurocodes contre le portail VSF a ete envisagee (recherche de chaque code via le meme mecanisme que `rpbm_agent/debug_portals.py`) mais **ecartee pour l'instant, decision RPBM du 29/07/2026** : risque de se faire reperer par le portail sur un volume de requetes inhabituel. Point a documenter si la question est reconsideree plus tard - voir `docs/cartographie/reconciliation-stock-rpbm-agent.md` (§2.13).

Colonnes recommandees pour `categories_mapping.csv` :

```text
source_type,target_category,target_subcategory,product_type,stockable,notes
```

Decision client du 2026-07-23 : ce choix est revenu. `target_subcategory` est desormais renseigne pour les regroupements identifies sous `Autres` (`Optique`, `Retroviseur EXT`, `Retroviseur INT`, `Toit panoramique`, `Cache retro`, `Leve-vitre`, `Baie de pare-brise`) : ce sont maintenant de vraies sous-categories Odoo (`product.category`) imbriquees sous `Autres`, et non plus de simples libelles de produit normalises. Seule exception maintenue : `CAMERA` reste dans `Autres` sans sous-categorie dediee (article rare, exception explicite du gestionnaire). Le detail complet reste dans `categories_odoo_proposition.csv` et dans la colonne `notes`.

Colonnes recommandees pour `locations_mapping.csv` :

```text
source_place,warehouse,location_parent,location_name,location_complete_name,notes
```

Colonnes recommandees pour `initial_stock_import.csv` :

```text
product_reference,product_name,category,location,quantity,cost,public_price,status,inventory_status,notes
```

Statuts de preparation a prevoir :

```text
available
reserved
sold
broken
missing
error
to_check
```

Controles minimaux :

- doublons d'eurocode avec designations differentes;
- eurocodes vides ou invalides;
- prix non numeriques;
- types non mappes;
- places non mappees;
- lignes en stock mais marquees `pas la` au dernier inventaire;
- lignes sans sortie mais quantite nulle;
- lignes avec sortie mais quantite positive;
- articles presents physiquement mais absents du catalogue Odoo;
- produits Odoo existants avec meme `default_code` mais nom/categorie differents.

## Plan d'execution recommande

1. Corriger l'acces MCP distant ou lancer un serveur MCP local valide.
2. Lire la structure Odoo preprod avec `rpbm-preprod`.
3. Exporter les produits, categories et emplacements Odoo existants.
4. Produire les fichiers intermediaires nettoyes depuis le CSV.
5. Produire `categories_mapping.csv`, `locations_mapping.csv` et `initial_stock_import.csv`.
6. Faire valider les mappings de categories et emplacements par RPBM.
7. Faire valider la source de stock initial : inventaire reel 30/06/2026, stock theorique corrige ou fichier V4 corrige.
8. Faire arbitrer l'ecart d'inventaire de 6 448,18 EUR.
9. Importer en preproduction le catalogue produits.
10. Controler les doublons et les categories en preproduction.
11. Importer le stock initial via ajustement d'inventaire.
12. Controler les quantites par famille, valeur, depot et emplacement.
13. Documenter les ecarts et refaire un test complet si necessaire.
14. Seulement apres validation, preparer la procedure de reprise en production.

## Position sur le notebook existant

Le notebook `import_product.ipynb` contient une premiere exploration :

- lecture du CSV en ignorant les 4 premieres lignes;
- extraction des colonnes 6 a 12;
- nettoyage des types;
- creation potentielle de categories et produits.

Ce notebook ne doit pas etre execute tel quel pour la migration finale, car il utilise un ancien connecteur `agent` et contient une logique d'ecriture directe.

Il peut servir de reference pour les mappings de types, mais la procedure cible doit etre reecrite autour du MCP Paradigme avec le profil `rpbm-preprod`, avec separation stricte entre :

- preparation de donnees;
- lectures Odoo;
- validation metier;
- ecritures Odoo confirmees.

## Risques principaux

- Donnees source non fiables depuis 2023.
- Export CSV incomplet pour les statuts visuels, car les couleurs Google Sheets ne sont pas conservees.
- Nombreux doublons d'eurocode a interpreter comme quantites ou historique.
- Emplacements heterogenes et pas toujours rattachables directement a D1/D2.
- Ecart d'inventaire au 30/06/2026 de 6 448,18 EUR a arbitrer.
- Stock initial a forte valeur comptable : validation comptable necessaire avant import.
- Risque de creer des produits en doublon si le rapprochement Odoo par `default_code` n'est pas fait avant ecriture.
- Perte silencieuse des donnees d'audit si elles sont ecrites dans `description` : la synchronisation VSF du module `rpbm_agent` reecrit ce champ sans avertissement.
- Blocage definitif de la synchronisation VSF (`UserError`) sur les produits portant plus d'une ligne `product.supplierinfo` active pour le partenaire VSF, notamment si l'import cree une ligne sans `date_start`.
- Catalogue migre non synchronisable si `x_studio_eurocode` n'est pas renseigne a l'import.
- Deux prix VSF concurrents jamais reconcilies si `VSF Centre`/`VSF Ouest` sont importes comme partenaires distincts de `rpbm_agent.vsf_partner_id` (id `5708`).

## Prochaines actions

- Rapprocher `products_to_import.csv` avec les `default_code` Odoo et separer `create`, `update` et `to_check`.
- Examiner `product_reconciliation.csv`, en particulier les candidats de creation et les produits Odoo sans reference.
- Faire valider les 31 mappings de categories et le rattachement des 568 lieux source.
- Obtenir le fichier corrige de l'inventaire reel du 30/06/2026 pour remplir `stock_initial_to_import.csv`.
- Faire arbitrer l'ecart d'inventaire de 6 448,18 EUR et le parametrage de valorisation.
- Tester l'import du catalogue en preproduction avec confirmation explicite avant toute ecriture.
- Reconfirmer avec RPBM la repartition des blocs de racks `R1xx`-`R7xx` entre Depot 1 et Depot 2 (la formulation initiale "de R101 a RXX" ne correspond pas aux donnees reelles, voir section Strategie emplacements).
- Definir avec RPBM les modalites de restructuration des emplacements `D1`/`D2` deja existants en preproduction vers des entrepots autonomes.
- Valider les propositions de `routes_transferts_entrepots.md` (reapprovisionnement Galleria/Genipa, routage des lignes stockables via `Camion`) avant toute configuration de routes en preproduction.
- Trancher les points de coordination avec le module `rpbm_agent` (cle produit `default_code`, categorie et cout a la creation d'un article par le widget) listes dans `docs/cartographie/reconciliation-stock-rpbm-agent.md` (racine du depot) avant que les deux chantiers n'ecrivent en production simultanement.
