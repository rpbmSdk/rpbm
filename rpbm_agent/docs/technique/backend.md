# Backend

`controllers/main.py` expose un unique controller `AgentController`. Deux instances globales sont créées **au chargement du module Python** (pas par requête, pas par utilisateur) :

```python
vsfAgent = vsf.VSFAgent()
xglassAgent = xglass.XGLASS()
```

Depuis le lot E2 (`17.0.261006.2`), `/rpbm_agent_auth` ne réinstancie et n'authentifie que `xglassAgent`, via les paramètres système `ir.config_parameter`. `vsfAgent` n'est plus remplacé : il se connecte à la demande, dans chaque processus (voir [VSF, session à la demande](#vsf-session-à-la-demande-lot-e2)). Voir [état de session partagée](#état-de-session-partagée) plus bas, et [verrou de concurrence](../technique/configuration.md#concurrence--verrou-de-session) pour le mécanisme qui sérialise les sessions X'Glass entre utilisateurs.

## Référence des routes

Toutes les routes sont déclarées `type='json'`, `auth='user'` (JSON-RPC, utilisateur Odoo connecté requis, pas de contrôle de droits plus fin), sauf les routes VSF, que `_vsf_call` réserve aux utilisateurs internes depuis le lot E2 : le verrou, qui les fermait de fait aux autres utilisateurs, ne les protège plus.

Droits : les commerciaux (`sales_team.group_sale_salesman`) n'ont que la **lecture** sur `fleet.vehicle`, `fleet.vehicle.model` et `fleet.vehicle.model.brand` ([`security/ir.model.access.csv`](../../security/ir.model.access.csv)), sans groupe Parc automobile : le groupe Fleet « Officer » restreint la visibilité aux véhicules dont l'utilisateur est conducteur, ce qui masque les véhicules clients. Les créations/écritures du widget (`fleet.vehicle` dans `/createVehicule` et `/enrichVehicule`, `product.product` et `product.supplierinfo` dans `/createProduct`) passent par `sudo()` : elles ne sont possibles que via le widget, pas depuis les menus Parc automobile / Articles.

| Route | Paramètres | Résumé | Modèles/portails touchés |
|---|---|---|---|
| `/rpbm_agent_auth` | — | Prend le verrou, puis réinstancie et authentifie `xglassAgent` depuis `ir.config_parameter` (`XGLASS_USER`, `XGLASS_PASS`). **Plus de connexion VSF** depuis le lot E2 : `vsfAgent` n'est plus remplacé | X'Glass, `ir.config_parameter` |
| `/rpbm_agent_close` | — | Ferme la session X'Glass (`xglassAgent.close()`) **seulement si le verrou est libre ou tenu par l'appelant** (lot E2) : les routes VSF ne prolongeant plus le verrou, un autre utilisateur a pu reprendre le verrou expiré et charger X'Glass, et sa session n'est alors pas déconnectée. Le verrou est ensuite libéré comme avant. VSF n'est pas déconnecté explicitement (`VSFAgent` n'a pas de `close()`, non nécessaire) | X'Glass |
| `/searchImmatriculation` | `immatriculation: str` | Recherche véhicule(s) par plaque sur X'Glass | X'Glass |
| `/rpbm_agent/getVehiculeMeta` | `vehiculeId: str` | Sélectionne le véhicule côté portail (`selectVehicule`) et retourne `{meta: {vin, cnit, dateMec}, planche}` en un seul aller-retour | X'Glass |
| `/getOdooVehicule` | `immatriculation: str` | Recherche un véhicule Odoo existant par plaque ; retourne `{id, name, driver_id}` ou `False` | `fleet.vehicle` |
| `/createVehicule` | `immatriculation, partner_id, vehicule_info, vehicule_meta` | Crée (ou retourne l'existant) marque/modèle si besoin, puis le `fleet.vehicle` (`rpbm_detail_model`, `rpbm_first_registration_date`, `vin_sn`) ; retourne `{id, name}`. L'énergie X'Glass est convertie vers une clé native `fleet.FUEL_TYPES` (`XGLASS_ENERGY_TO_FUEL_TYPE`, énergie inconnue = champ vide). L'image X'Glass est facultative et n'est tentée que si l'appelant détient encore le verrou portail (depuis le lot E2, les routes VSF ne le prolongent plus : après un long travail VSF seul, le véhicule peut être créé sans image). | `fleet.vehicle`, `fleet.vehicle.model.brand`, `fleet.vehicle.model`, X'Glass (image facultative) |
| `/enrichVehicule` | `vehicle_id: int, vehicule_meta` | Complète uniquement `vin_sn` et `rpbm_first_registration_date` manquants d'un `fleet.vehicle` existant (un VIN de l'ancienne forme `var = …;` est remplacé) ; les droits insuffisants deviennent un avertissement | `fleet.vehicle` |
| `/getPlanche` | `vehiculeId: int` | Re-sélectionne le véhicule côté portail et retourne la "planche" ; utilisé par le widget uniquement pour restaurer le contexte après reconnexion | X'Glass |
| `/getPieces` | `plancheId: int, calqueId: int` | Récupère et aplatit les pièces X'Glass d'une catégorie, principales puis complémentaires, dans l'ordre du portail ; chaque pièce porte son groupe (`elementKey`), sa famille (`elementSitId`, `elementSitLibelle`) et `laborOperations` (opérations de main-d'œuvre T1/T2/T3 avec `productId` issu de `rpbm_agent.labor_product_t*`). Voir [lot D, build A](#getpieces-et-getpieceam-lot-d-build-a) | X'Glass, `ir.config_parameter` |
| `/getPieceAm` | `element_withPiecesAm, pieceId=None, elementSitId=None` | Récupère les pièces après-marché associées à une pièce (« Équivalence AM »), ou, sans `pieceId`, à une famille (encart « Autres marques AM »), via `XGLASS.findSelectionsPiecesAmView()`. Retourne toujours une liste (`null` ou absence = liste vide) ; corps non JSON = erreur utilisateur. Voir [lot D, build A](#getpieces-et-getpieceam-lot-d-build-a) | X'Glass |
| `/rpbm_labor_products` | — | Produits de main-d'œuvre courants par taux (`{T1, T2, T3}`, paramètres `rpbm_agent.labor_product_*`, `_labor_products`). Le devis l'appelle à l'ajout d'une main-d'œuvre enregistrée sur le dossier, pour ne pas réutiliser le produit résolu à l'enregistrement (correctif du 2026-10-07) | aucun |
| `/searchBaseEurocode` | `baseEurocode: str` | Recherche les articles VSF correspondant à une base eurocode. Une base sans résultat renvoie une liste vide, pas une erreur (lot correctif `17.0.261006.1`, voir [Recherche sans résultat](#recherche-sans-résultat-r24)). Sans verrou, par `_vsf_call` (lot E2) | VSF |
| `/getVsfArticleDetails` | `articleVsfInfo: dict, enrichSuggestions=True` | Lit la fiche de l'article sélectionné : images pleine taille, dimensions, caractéristiques et suggestions VSF (fiches des suggestions lues aussi si `enrichSuggestions`, en parallèle : au plus `MAX_PARALLEL_SUGGESTIONS` = 4 requêtes simultanées, ordre du carrousel conservé). Sans verrou, par `_vsf_call` (lot E2) | VSF |
| `/doesProductExists` | `articleVsfInfo: dict` | Recherche le produit d'un article VSF (`_find_existing_product`) : code VSF (`rpbm_eurocode`) d'abord, puis référence interne et nom exact unique pour les seuls produits sans eurocode ; jamais un produit qui porte l'eurocode d'un autre article | `product.product`, `product.template` |
| `/createProduct` | `articleVsfInfo: dict` | Retourne le produit existant (même recherche) ou crée le produit + son prix fournisseur VSF, avec verrou transactionnel par code et eurocode sur le template. Sans verrou de session (lot E2) : seule la lecture de la fiche VSF passe par `_vsf_call` ; les créations restent hors du rejeu, pour ne jamais être faites deux fois ; la recherche d'un produit existant, après le verrou par code, passe par un curseur neuf (voir [VSF, session à la demande](#vsf-session-à-la-demande-lot-e2)) | `product.product`, `product.template`, `product.supplierinfo` |

### Rattachement d'un article VSF à un produit (lot E1.1)

`_find_existing_product(env, product_code, eurocode, product_name)` (`main.py`) est la recherche commune de `/doesProductExists` et de `/createProduct`. `product_code` est la référence interne attendue (`_article_constructor_reference` : référence constructeur, ou code VSF si elle est absente), `eurocode` le code VSF de l'article et `product_name` son nom. Version `17.0.261005.4`, recette live réussie le 2026-10-05 : à l'étape 1 de SO-07, `6108AXSR` affiche « Article absent de la base Odoo » et le produit `6574AXSH` n'est plus proposé (VSF ne suggérant plus `6108AXSR`, le contrôle a porté sur sa ligne principale). Le test Odoo ci-dessous est non exécuté, abandonné sur décision de l'utilisateur (2026-10-06).

| Rang | Critère | Condition | Résultat retenu | `matched_by` |
|---|---|---|---|---|
| 1 | `product_tmpl_id.rpbm_eurocode` égal au code VSF | aucune | le premier (`limit=1`) | `eurocode` |
| 2 | `default_code` égal à la référence interne attendue | produit sans eurocode, **seulement si l'eurocode de l'article est fourni** ; sinon aucune restriction | le premier (`limit=1`) | `reference_interne` |
| 3 | `name` égal au nom de l'article (`=ilike`, insensible à la casse) | produit sans eurocode | seulement s'il y a exactement un produit (`limit=2`) | `nom` |

« Sans eurocode » se traduit par `('product_tmpl_id.rpbm_eurocode', 'in', [False, ''])` : champ à `NULL` ou chaîne vide (`= False` ne couvre que `NULL`). Un produit qui porte un eurocode ne peut donc être retenu que par le rang 1 : celui d'un autre article est exclu des rangs 2 et 3. Deux produits sans eurocode de même nom ne donnent aucun rattachement.

**Eurocode fourni ou non.** `/doesProductExists` et `/createProduct` tirent l'eurocode de `articleVsfInfo.code` (`/createProduct` refuse un article sans code). Un appel ancien de `/doesProductExists` avec `productCode` seul est converti en `{'code': productCode}` : l'eurocode est alors fourni et la restriction du rang 2 s'applique aussi. Elle ne tombe que sans eurocode (`articleVsfInfo` sans `code`, ou appel direct de la fonction) : la référence interne suffit alors.

**Origine.** L'ancien ordre (référence interne, eurocode, nom) laissait le nom suffire : la suggestion VSF `6108AXSR` « GEL CAPTEUR SILICONE », sans produit propre, était rattachée au produit `6574AXSH`, seul produit de ce nom et gel d'un autre article. `/createProduct` applique la même recherche : sans produit trouvé, il crée le produit avec `rpbm_eurocode` égal au code VSF ([9](../fonctionnel/workflow/09-creation-produit.md)).

**Contrôle.** `tests/test_find_existing_product.py` (`TransactionCase`, importé dans `tests/__init__.py`) compte six tests, avec des valeurs propres au test (`TEST6574AXSH`, `TEST6108AXSR`, « GEL CAPTEUR SILICONE (test E1.1) ») : le résultat ne dépend pas des produits de la base. Ils couvrent le nom d'un produit portant un autre eurocode (non retenu : le cas d'origine rejoué), l'eurocode avant la référence, la référence d'un produit sans eurocode (`NULL` ou chaîne vide), la référence d'un produit portant un autre eurocode (non retenue, mais retenue si l'eurocode n'est pas fourni), le nom unique d'un ancien produit et deux anciens produits de même nom (non retenus). Ils demandent une base PostgreSQL et le lanceur Odoo avec `--test-enable`. Le poste de développement n'a pas PostgreSQL et le build de staging met le module à jour sans `--test-enable` : le fichier est **non exécuté, abandonné sur décision de l'utilisateur (2026-10-06)** et reste dans le dépôt.

### `/getPieces` et `/getPieceAm` (lot D, build A)

Version `17.0.261005.1` : recette réussie le 2026-10-05 sur le build `ab31793`.

- **Libellé de famille.** Chaque pièce de `/getPieces` reçoit `elementSitLibelle`, égal au
  `libelle` de son `XGlassElement` (déjà calculé dans `controllers/xglass.py`, mais perdu à
  l'aplatissement). Clé ajoutée : rien n'est retiré de la réponse, ni l'ordre
  (`ELEMENTSIT_PRINCIPAUX` puis `ELEMENTSIT_COMPLEMENTAIRES`, ordre du portail). Le regroupement
  lui-même se fait dans le frontend (voir [frontend](frontend.md#groupes-de-pièces-et-encarts-autre-am-par-famille-r19-r20)).
- **Journalisation des familles.** Pour chaque élément reçu, `_logger.info` écrit : `elementKey`,
  `elementSitId`, libellé, `affichageAm`, `containsPiecesAm`, `elementVitre` et nombre de pièces ;
  il écrit aussi les clés de premier niveau de `elementSitMapData` que le widget ne traite pas
  (le portail connaît d'autres groupes, par exemple hors calque ou recherche par référence : leur
  présence dans les réponses réelles n'est pas vérifiée). Ces lignes vont au journal serveur
  seulement : aucune écriture en base, aucun corps de réponse enregistré, et pour les clés
  inconnues seulement leur nom et leur taille. Elles remplacent un vidage de la réponse complète,
  jugé contraire au protocole de recette « sans écriture ». Une ligne par élément
  (`getPieces <planche> <calque> : <groupe> elementSitId=… libellé=… affichageAm=… containsPiecesAm=…
  elementVitre=… pièces=…`), plus une ligne pour les clés ignorées. Elles servent à décider plus tard si l'encart « Autres marques AM » doit être limité aux familles qui
  l'annoncent.
- **Pas de filtre sur les drapeaux.** Le serveur et le widget n'appliquent aucune règle
  `affichageAm and containsPiecesAm` : l'encart est proposé pour toutes les familles (décision du
  2026-10-02 « toujours présent, replié »). Observé en trace pour la famille principale du
  pare-brise : les deux drapeaux sont vrais ; les familles complémentaires n'ont pas été tracées.
- **`/getPieceAm` renvoie toujours une liste.** `XGLASS.findSelectionsPiecesAmView()`
  (`controllers/xglass.py`) ne renvoie plus la réponse HTTP mais directement
  `(r.json() or {}).get('selectionsPiecesAmView') or []` ; un corps non JSON (`ValueError`)
  devient une `XGlassError` « Réponse X'Glass illisible (pièces AM) », que `main.py::getPieceAm`
  convertit par `_raise_portal_error` en erreur utilisateur typée (`UserError`, ou
  `AgentSessionExpiredError` si la session a expiré). Un seul appelant dans le dépôt
  (`main.py`). Observé (recette R11, 2026-10-02) : sans contexte véhicule, X'Glass répond
  `{"errorCode": "10", "selectionsPiecesAmView": null}` ; l'ancien code renvoyait alors `None`
  au widget (encart `None` après reconnexion). Désormais la liste est vide.
  Hypothèse de lecture, non observée : un corps `null` entier aurait levé une `AttributeError`.
  Effet de bord à surveiller : une réponse dégradée devient une liste vide, que le widget met en
  cache par véhicule et famille jusqu'à la fermeture de la dialog ou à la reconnexion
  (« Aucune autre référence après-marché. » peut alors masquer le défaut ; la reconnexion à chaud
  rejoue la recherche d'immatriculation pour l'éviter, voir [configuration](configuration.md#reconnexion-à-chaud)).

### Dérivation du véhicule et champs Studio

Le widget n'écrit que les champs natifs `rpbm_*` de l'opportunité (ou leurs miroirs sur le devis).
Marque, modèle, VIN, énergie, détail et date de mise en circulation sont dérivés du véhicule Fleet
lié par le `compute` de `crm.lead` ; la recopie vers les champs Studio historiques (et le retour
d'une saisie Studio vers le natif) est faite par le mixin de `models/legacy_fields.py`, sans route
dédiée. Voir [configuration](configuration.md#champs-natifs-et-champs-studio-historiques).

## X'Glass (`controllers/xglass.py`)

- **Portail** : `https://portail-xglass.com`, authentification Spring Security classique (`j_spring_security_check`, `j_username`/`j_password`), session par cookies (`requests.Session`).
- **Contrainte connue** : *"un seul utilisateur actif par identifiant"* — le portail refuse une seconde session simultanée pour le même identifiant. `auth()` réessaie donc exactement une fois sans se déconnecter entre les deux tentatives (la première tentative refusée évince la session restée ouverte) — détail dans [configuration](configuration.md#authentification-des-portails).
- **Contrainte non documentée ailleurs** (retrouvée dans `controllers/xglass.ipynb`, cellule 27) : une recherche par immatriculation (`searchImmat`) n'est acceptée par le portail que si la page `initRechercheVehicule.html` a été chargée au préalable dans la session — d'où `setInitRecherche()` appelé automatiquement par `searchImmat()` si nécessaire.

### États de session

```mermaid
stateDiagram-v2
    [*] --> NonConnecte
    NonConnecte --> Connecte: auth() réussi
    NonConnecte --> NonConnecte: échec du 1er essai → 2e tentative (sans logout)
    NonConnecte --> [*]: échec du 2e essai → XGlassAuthError
    Connecte --> RechercheInitialisee: setInitRecherche()\n(déclenché automatiquement par searchImmat)
    RechercheInitialisee --> RechercheInitialisee: searchImmat / selectVehicule /\naffichagePieces / findSelectionsPiecesAmView
    Connecte --> NonConnecte: close() (logout)
    RechercheInitialisee --> NonConnecte: close() (logout)
```

### Classes de données

Toutes construites depuis le JSON/HTML du portail (`**kwargs` → attributs), aucune n'est un modèle Odoo :

| Classe | Rôle |
|---|---|
| `XGlassMarque`, `XGlassModele` | Marque et modèle véhicule (X'Glass) |
| `XGlassVehicule` | Véhicule retourné par la recherche immatriculation ; calcule `energieLibelle` via `xglass_lbl.getLabel()` et construit `imgUrl` |
| `XGlassCalque` | Catégorie de pièces (la planche elle-même est renvoyée en JSON brut par `selectVehicule()`) |
| `XGlassPieceOe`, `XGlassPieceOeCaracteristique(Type)` | Pièce d'origine et ses caractéristiques |
| `XGlassPieceTemps*` (4 classes) | Temps/opérations de main d'œuvre associés à une pièce |
| `XGlassPiece` | Regroupe une `XGlassPieceOe` et ses temps |
| `XGlassElement` | Regroupement de pièces (`ELEMENTSIT_PRINCIPAUX`/`ELEMENTSIT_COMPLEMENTAIRES`) |

Exemple de payload `XGlassVehicule` (issu de `controllers/xglass.ipynb`) :
```json
{
  "id": 431060,
  "libelleCourt": "SUZUKI BALENO II - 5P 2016-04-> 1.2i 90",
  "energieLibelle": "Essence",
  "puissanceKw": 66,
  "puissanceCom": 90,
  "portesNbr": 5,
  "cylindreeCm3": 1242,
  "modele": { "gamme": "BALENO", "id": 4267 },
  "imgUrl": "https://portail-xglass.com/images/images_modele/40377.jpg"
}
```
Métadonnées associées (`getVehiculeMeta`) :
```json
{ "cnit": "M10CPFVP000R017", "dateMec": "02/2016", "vin": "VF7SA9HPKFW589387" }
```

### `xglass_lbl.py`

Fichier statique : un dict `LIBS` (~1440 entrées) recopiant les libellés d'internationalisation du frontend X'Glass, exposé via `getLabel(label)`. Dans le code actuel, **seules les clés `lbl.energie.*`** sont consommées (traduction du type de carburant) — le reste du dictionnaire n'est pas exploité.

## VSF (`controllers/vsf.py`)

- **Portail** : `https://client.myvsf.fr`, authentification formulaire classique avec jeton CSRF caché (`<input name="_token">`) + session cookie.
- `VSFAgent` n'a **pas de méthode `close()`** (contrairement à `XGLASS`).
- `searchEurocodeArticlesClient()` : récupère d'abord la liste d'IDs d'articles + un jeton CSRF meta depuis la page HTML de résultats, puis interroge l'endpoint AJAX `/catalogue/articles-client` (JSON), et fusionne ce JSON avec les informations extraites directement des lignes `<tr class="product-line">` de la page HTML. Dans la première cellule, chaque lien `data-fslightbox` plein format est apparié à sa miniature pour produire `images[{thumbnailUrl, fullUrl}]` ; les signatures `sm` et `xlg` restent celles servies par VSF. L'`url` de fiche, lue dans la deuxième cellule, passe par `_absolute_url` dès cette extraction (`extractProductInfo`, build `17.0.261005.2`), comme `getArticleDetails` le faisait déjà à la sélection : le lien « Fiche technique » d'une ligne non sélectionnée a ainsi une URL VSF complète, que le `href` de la page soit relatif ou absolu. Le matching reste manuel sur `code`. Sans liste d'articles, une page « aucun résultat » de VSF renvoie `[]` sans requête `articles-client` (voir [Recherche sans résultat](#recherche-sans-résultat-r24)).
- `getArticleDetails()` lit une fiche article authentifiée : caractéristiques libellé/valeur, dimensions converties en millimètres, images `p=xlg` réellement signées par VSF, et cartes du carrousel `#article-reference-complementaires-carousel`. Il conserve les paires d'images de la recherche ; sans elles, il ne lit que `#carousel-article-photos` quand ce conteneur existe, excluant `#carousel-modele-photos` (repli page entière pour l'ancien HTML et les fixtures). Il ne synthétise jamais une URL pleine taille depuis une miniature, car la signature dépend du format demandé.
- `VSFArticle.__init__` calcule `prixVenteRPBM = prixVente * (1 - remiseRPBM)` à partir de `rpbm_agent.vsf_discount` (défaut de compatibilité `0.2`). `VSFArticle` n'expose aucun champ `id` — seul `code` sert de clé (voir implication côté frontend dans l'[état des lieux](../etat-des-lieux.md)).

Exemple de payload `VSFArticle` :
```json
{
  "code": "EA01RGPR5RQ",
  "name": "CUSTODE ARRIÈRE DROIT TEINTÉ VERT FONCÉ GREAT WALL HOVER  08-",
  "prixHT": 102.56,
  "prixVente": 113.95,
  "prixVenteRPBM": 91.16,
  "remise": "10%",
  "stock": 5,
  "type_piece": "LA",
  "url": "https://client.myvsf.fr/catalogue/article/EA01RGPR5RQ"
}
```

### VSF, session à la demande (lot E2)

Lot E2 « VSF d'abord, X'Glass à la demande » (`17.0.261006.2`, commits `afa51df` code et `a562fa7` docs, recette live réussie le 2026-10-06, [SO-10](../jeu-de-test.md#so-10--vsf-dabord-xglass-à-la-demande-lot-e2)). Sur un devis, la recherche VSF ne dépend plus de l'authentification X'Glass ni de son verrou : `/rpbm_agent_auth` ne connecte plus que X'Glass, et le serveur ouvre la session VSF au premier appel.

**Pourquoi c'est possible.** Trace T1 (2026-10-06, deux connexions sur le compte partagé) : A se connecte et cherche `6108A` (21 lignes) ; B se connecte avec le même compte ; A cherche de nouveau, puis B cherche ; B se déconnecte (`POST /deconnexion`) ; A cherche encore. **Chaque recherche aboutit** : VSF accepte plusieurs sessions simultanées sur un même compte, et la déconnexion d'une session n'invalide pas les autres. Nos connexions ne déconnectent donc pas les vendeurs connectés à VSF dans leur navigateur. Cela lève le préalable 1 d'E2 et écarte l'hypothèse « compte utilisé ailleurs » de R23 (voir [état de session partagée](#état-de-session-partagée)).

**`VSFAgent`** (`controllers/vsf.py`, testable sans Odoo) :
- `__init__` pose `logged_in = False`, un verrou de thread `_login_lock` et un compteur `_login_generation = 0` ;
- `_login(login, password, expired=None)`, sous le verrou : l'agent ne se connecte que s'il n'est pas connecté, ou si la génération signalée expirée (`expired`) est la génération courante. Si un autre thread s'est déjà reconnecté, la génération courante est plus récente et il n'y a pas de seconde connexion. Une connexion refusée laisse `logged_in` à faux ;
- `with_session(login, password, fn)` : se connecte au besoin, exécute `fn(self)`, et sur une `VSFAuthError` (session expirée) se reconnecte puis rejoue `fn` **une seule fois** ; un second `VSFAuthError` se propage ;
- les threads qui lisent les suggestions (`MAX_PARALLEL_SUGGESTIONS`) ne se connectent jamais : leur `VSFAuthError` remonte au `with_session` extérieur, qui rejoue la lecture entière.

Une seule session VSF par processus Odoo, ouverte à la demande ; si VSF n'acceptait un jour qu'une session par compte, plusieurs processus se déconnecteraient mutuellement (mise à niveau possible : cookie partagé en base, hors lot).

**`_vsf_call(fn)`** (`controllers/main.py`), commun aux routes VSF :
- refuse un utilisateur non interne (`request.env.user._is_internal()`, sinon `AccessError` « Le portail VSF est réservé aux utilisateurs internes. ») : les routes sont en `auth='user'` et `/createProduct` crée en `sudo()`, et le verrou, qui disparaît pour VSF, faisait office de barrière ;
- lit `VSF_LOGIN` et `VSF_PASSWORD` dans `ir.config_parameter` ;
- relit le traçage portail (`_configure_trace(params)`, extrait de `/rpbm_agent_auth`) **seulement quand l'agent n'est pas connecté**, car cet appel remet à zéro la numérotation des requêtes tracées ;
- appelle `vsfAgent.with_session(...)`.

Les trois routes VSF perdent `@_touch_agent_lock` et passent par `_vsf_call`. Pour `/createProduct`, seule la lecture `getArticleDetails` est dans `_vsf_call` ; l'image, publique, est lue juste après.

**`/createProduct` et deux vendeurs.** Le verrou consultatif par code (`pg_advisory_xact_lock`) sérialise les créations, mais la transaction de la requête est en REPEATABLE READ : son instantané précède le verrou et ne voit pas le produit qu'une requête concurrente a créé avant de le relâcher. Après le verrou, la recherche d'existence (`_find_existing_product`) passe donc par un curseur neuf (`request.env.registry.cursor()`), qui voit les produits commités  ; sans cela, deux vendeurs créant le même article en même temps pouvaient produire un doublon.

**Erreurs.** `_raise_portal_error` ne convertit plus que `XGlassAuthError` en `AgentSessionExpiredError`. Une `VSFAuthError` qui arrive jusque-là (la reconnexion côté serveur a échoué) donne une `UserError` « Connexion au portail VSF impossible. Vérifiez les identifiants configurés. » : une erreur VSF ne déclenche jamais la reconnexion X'Glass du client.

**Conséquences connues.**
- Les routes VSF ne prolongent plus le verrou X'Glass (expiration glissante de 15 minutes). Après un long travail VSF seul, l'appel X'Glass suivant se reconnecte de façon transparente (reconnexion à chaud), et `/createVehicule` peut créer le véhicule sans image (`has_active_agent_lock`).
- Le verrou ne protège plus que X'Glass : plusieurs vendeurs peuvent utiliser VSF en même temps.
- `/rpbm_agent_close` ne déconnecte plus un autre utilisateur : après 15 minutes de travail VSF seul, le verrou a pu être repris par un autre vendeur qui a chargé X'Glass ; la session X'Glass n'est fermée que si le verrou est libre ou tenu par l'appelant.
- Après un arrêt du processus (voir [état de session partagée](#état-de-session-partagée)), la première requête VSF se reconnecte seule, sans erreur visible pour l'utilisateur.

**Contrôle.** `test_portal_auth.py` : `test_vsf_connexion_a_la_demande_une_seule_fois`, `test_vsf_session_expiree_reconnexion_puis_succes`, `test_vsf_second_echec_de_session_remonte`, `test_vsf_connexion_refusee_laisse_deconnecte` et `test_vsf_deux_threads_de_la_meme_generation_une_seule_reconnexion`.

### Recherche sans résultat (R24)

Lot correctif `17.0.261006.1` (commit `44b86e0`), recette live réussie le 2026-10-06 sans écriture : `9999Z` affiche « Aucun article VSF pour « 9999Z ». », sans notification d'erreur ([SO-09](../jeu-de-test.md#so-09--base-sans-résultat-lot-correctif-du-2026-10-06-r24), étape 1 ; les autres étapes, facultatives, n'ont pas été jouées).

**Trace réelle** (2026-10-06, une connexion VSF) de `GET /catalogue/vitrage?search=<valeur>` :

| Valeur | HTTP | Liste d'articles | Résultat |
|---|---|---|---|
| `6108A` | 200 | présente | 21 articles |
| `6108a` | 200 | présente | 21 articles (VSF ignore la casse) |
| `9999Z` | 200 | absente | page « Aucun résultat ne correspond à votre recherche. » |
| `A+B &C D` | 200 | absente | même page |
| `61-08A` | 200 | absente | même page |

VSF répond donc à une base sans article par une page 200 authentifiée, normale, **sans** `#articles-list-container` : ce n'est ni une panne ni une session expirée.

- **Avant le lot.** `searchEurocodeArticlesClient()` levait `VSFError` (« Conteneur articles introuvable sur la page de résultats VSF (session expirée ?) ») dès que la liste manquait, et `/searchBaseEurocode` convertissait toute `VSFError` en « Recherche impossible : le portail VSF est inaccessible. » : toute base sans résultat, même au bon format, passait pour une panne (recette R13 à R17, 2026-10-05).
- **Désormais.** Sans `#articles-list-container`, la méthode renvoie `[]` si le `#catalog-container` de la page contient l'image `/img/no-result.png` ou le texte « Aucun résultat ne correspond à votre recherche » ; elle ne fait alors aucune requête `articles-client`. La route renvoie `[]` au widget, qui affiche « Aucun article VSF pour « *base* ». » ([frontend](frontend.md#recherche-sans-résultat-r24)).
- **Page inattendue.** Sans liste d'articles ni marqueur « aucun résultat », la méthode lève `VSFError("Page de résultats VSF inattendue, ni liste d'articles ni message « aucun résultat ».")` : le message ne parle plus de session. `main.py` est inchangé, **voulu** (décision du 2026-10-06) : la route convertit toujours une `VSFError` en « Recherche impossible : le portail VSF est inaccessible. », parce qu'une page VSF de structure inattendue reste, pour l'utilisateur, un incident du portail ; le message exact n'est que dans le journal serveur.
- **Session expirée.** Elle n'est pas confondue avec « aucun résultat » : elle se détecte avant tout parsing, par l'URL de connexion (`ensure_logged()` lève `VSFAuthError`). Au lot `17.0.261006.1`, cette erreur remontait au widget en `AgentSessionExpiredError` ; depuis le lot E2, `with_session` se reconnecte et rejoue côté serveur (voir [VSF, session à la demande](#vsf-session-à-la-demande-lot-e2)).
- **Rejeu.** Au lot `17.0.261006.1`, après une `AgentSessionExpiredError`, le widget se reconnectait et rejouait la requête une fois (`callPortal`) : une saisie pouvait produire deux requêtes `/searchBaseEurocode`, sans double déclenchement ; c'est ce rejeu qui échouait avec le message trompeur. Depuis le lot E2, ce rejeu a lieu dans le serveur pour VSF : le navigateur ne voit qu'une requête.
- **Casse.** VSF ignore la casse (`6108a` donne les mêmes 21 articles que `6108A`) ; le widget ne la normalise pas.
- **Contrôle.** `test_portal_auth.py` : `test_vsf_recherche_sans_resultat_sans_post` (image, texte ou les deux : `[]` et aucun POST) et `test_vsf_recherche_page_inattendue` (une page sans liste ni message, ou avec un conteneur de catalogue sans marqueur, lève une `VSFError` qui ne parle pas de session).

## État de session partagée

`vsfAgent` et `xglassAgent` sont des instances **au niveau du module Python**, donc partagées par toutes les requêtes et tous les utilisateurs Odoo servis par **le même processus**. Elles portent un état mutable (`self.session` de `requests`, `self.selectedVehiculePage`, `self.initRecherche` ; pour VSF, `logged_in` et le compteur de génération de connexion).

**Mode d'exécution (trace T2, 2026-10-06, journaux Odoo.sh de pre-prod, lecture seule).**
- Pre-prod tourne en `--workers=0` : un seul processus threadé, un thread par requête, des requêtes simultanées, plus 2 threads de cron. Il n'y a pas de pool de workers : l'ancienne formule « partagées par tous les workers » était fausse.
- Production : 1 worker (Settings › Database Workers du projet Odoo.sh).
- Le processus s'arrête environ 2 minutes après la dernière requête et redémarre à la suivante, ainsi qu'à chaque mise à jour du build. Les globales, donc les sessions portail, sont alors perdues.
- Les erreurs `SERIALIZATION_FAILURE` / `bad query … FOR UPDATE` sur la ligne du verrou viennent de requêtes simultanées dans ce processus (des threads), pas de plusieurs workers.
- **R23 est expliqué** : les deux expirations de session VSF du 2026-10-05 (09:58:54 et 10:07:20 UTC dans les journaux serveur) tombent sur la première requête VSF après un redémarrage du processus, dont l'agent n'était pas connecté. Ce n'était pas un compte VSF « utilisé ailleurs » : la trace T1 montre que VSF accepte plusieurs sessions simultanées (voir [VSF, session à la demande](#vsf-session-à-la-demande-lot-e2)). Depuis le lot E2, ce cas n'a plus d'effet pour VSF : la connexion se fait à la demande, côté serveur. Il subsiste pour X'Glass, qui se reconnecte par la reconnexion à chaud du widget (hors lot).

**X'Glass.** Combiné à la contrainte « un seul utilisateur actif par identifiant » du portail X'Glass, deux utilisateurs Odoo utilisant X'Glass en même temps partageraient la même session portail sans coordination — empêché par un verrou applicatif (`ir.config_parameter` `rpbm_agent.session_lock`, `main.py::acquire_agent_lock`/`touch_agent_lock`/`release_agent_lock`) qui sérialise des sessions X'Glass complètes entre utilisateurs, de `/rpbm_agent_auth` à `/rpbm_agent_close`, avec expiration glissante de 15 min en filet de sécurité — voir [configuration](configuration.md#concurrence--verrou-de-session) pour le détail, et l'[état des lieux](../etat-des-lieux.md) pour l'historique du problème. `/rpbm_agent_auth` réinstancie `xglassAgent` à chaque appel (après avoir fermé le précédent), ce qui donne une ardoise propre par session.

**VSF.** Aucun verrou : plusieurs vendeurs peuvent chercher sur VSF en même temps (décision du 2026-10-06, [VD-05](../validations-metier.md#historique-des-décisions)). Le serveur se connecte à la demande et se reconnecte seul, une fois, quand la session expire.

Une expiration détectée dans X'Glass (`XGlassAuthError`) ou le verrou local est convertie en `AgentSessionExpiredError`, sous-classe de `UserError`. Son nom est le marqueur JSON-RPC consommé par le widget ; il ne dépend pas du message affiché. Depuis le lot E2, VSF n'en fait plus partie : une `VSFAuthError` est traitée dans le serveur (reconnexion et un seul rejeu) et, si la reconnexion échoue, devient une `UserError` « Connexion au portail VSF impossible. Vérifiez les identifiants configurés. ». Les autres erreurs portail restent des `UserError` fonctionnels. `/rpbm_agent_auth` reste l'unique route de (re)connexion X'Glass.
