# Configuration & déploiement

## Installation du module

Déposer `rpbm_agent/` dans le dossier `addons` de l'instance Odoo 17, puis installer via l'interface d'administration (`depends: base_setup, crm, delivery, fleet, product, sale_crm`). Le module exige `delivery` pour le champ natif `sale.order.carrier_id` et `base_setup` pour l'écran Réglages. Le routage stock (`stock_delivery`) est porté par l'architecture stock, pas par ce module.

## Dépendances Python

| Fichier | Contenu |
|---|---|
| `__manifest__.py` → `external_dependencies.python` | `beautifulsoup4`, `requests` |
| `controllers/requirements.txt` | `beautifulsoup4`, `python-dotenv`, `requests` (dont les scripts standalone) |

`python-dotenv` / `.env` (racine du module) ne servent qu'aux **scripts standalone hors Odoo** ([`debug_portals.py`](../../debug_portals.py), [`push_credentials.py`](../../push_credentials.py), notebooks) ; les controllers ne chargent jamais `.env`. En production, les identifiants viennent exclusivement de `ir.config_parameter` via `/rpbm_agent_auth`.

### Frontière des configurations locales

Le dépôt sélectionne la cible Odoo par son nom de profil dans `.paradigme.yaml` (`odoo.profile`). La résolution est ensuite faite sans valeur par défaut :

- les métadonnées du profil (URL, transport et références de variables) viennent de `~/.paradigme/paradigme_odoo_mcp.yaml` ;
- les secrets Odoo référencés (`database_env`, `username_env`, `password_env`) viennent de `~/.paradigme/.env` ;
- les quatre secrets des portails (`XGLASS_USER`, `XGLASS_PASS`, `VSF_LOGIN`, `VSF_PASSWORD`) viennent uniquement de `rpbm_agent/.env`.

[`push_credentials.py`](../../push_credentials.py) ne lit donc pas `.env.local`, les variables d'environnement du processus ou une cible saisie en secours. Il échoue explicitement si une partie du profil ou un secret requis manque. Cette séparation évite qu'une configuration de développement détourne une écriture vers une autre instance Odoo.

## Paramètres système requis

À créer dans `Réglages > Technique > Paramètres > Paramètres système` :

| Clé | Description |
|---|---|
| `XGLASS_USER` | Identifiant du portail X'Glass |
| `XGLASS_PASS` | Mot de passe du portail X'Glass |
| `VSF_LOGIN` | Identifiant du portail VSF |
| `VSF_PASSWORD` | Mot de passe du portail VSF |
| `rpbm_agent.vsf_partner_id` | Identifiant du partenaire fournisseur VSF ; défaut de compatibilité : `5708` |
| `rpbm_agent.vsf_discount` | Remise RPBM décimale entre `0` et `1` ; défaut de compatibilité : `0.2` |
| `rpbm_agent.labor_product_t1` / `_t2` / `_t3` | Identifiants des `product.product` de service facturés pour les opérations X'Glass T1/T2/T3 ; défauts `24` / `23` / `113` (ids constatés sur `rpbm-preprod`) |

Les paramètres `rpbm_agent.vsf_*` sont lus à chaque recherche VSF et création de produit (`controllers/vsf_config.py`), `rpbm_agent.labor_product_*` à chaque `/getPieces` et à chaque ajout de main-d'œuvre enregistrée sur le devis sans X'Glass (`/rpbm_labor_products`) : un changement de ces paramètres s'applique donc aussi à la main-d'œuvre enregistrée sur l'opportunité. Une valeur absente conserve le comportement historique ; une valeur invalide produit une erreur explicite et n'est jamais appliquée silencieusement.

### Mise à jour rapide des identifiants portails

Les utilisateurs du groupe technique `base.group_system` peuvent modifier les quatre identifiants depuis `Réglages > Paramètres généraux > Intégrations > Accès catalogues X'Glass / VSF`. Les champs sont reliés directement aux mêmes clés `ir.config_parameter` que celles consommées par `/rpbm_agent_auth` ; l'enregistrement prend donc effet à la prochaine authentification de l'assistant, sans exécution du script [`push_credentials.py`](../../push_credentials.py).

Les mots de passe sont affichés avec le contrôle de saisie masquée. Les identifiants restent des secrets propres à l'instance cible : ne pas les versionner, les recopier dans une vue XML ou les journaliser. Le script reste disponible pour une initialisation ou une rotation automatisée hors interface.

Peuvent être créés manuellement, ou poussés via [`push_credentials.py`](../../push_credentials.py) (racine du module) : le script lit les 4 identifiants depuis `.env` (racine du module, déjà ignoré par git — mêmes clés que celles utilisées pour l'exécution standalone de `vsf.py`/`xglass.py`) et les écrit sur le profil Odoo sélectionné via XML-RPC standard (`ir.config_parameter.set_param`). Les paramètres `ODOO_URL`/`ODOO_DB`/`ODOO_LOGIN`/`ODOO_PASSWORD` de `.env.local` ne sont pas utilisés. Le compte Odoo référencé par le profil doit être administrateur (`base.group_system`), seul groupe ayant accès à `ir.config_parameter`.

Un 5ᵉ paramètre système, `rpbm_agent.session_lock`, est créé et géré automatiquement par le module (verrou de concurrence, voir [ci-dessous](#concurrence--verrou-de-session)) — ne pas le modifier manuellement.

Deux paramètres optionnels pilotent le traçage HTTP des portails (voir [Débogage des portails](#débogage-des-portails)) :

| Clé | Description |
|---|---|
| `rpbm_agent.trace` | `1` pour journaliser chaque requête portail (défaut : inactif) |
| `rpbm_agent.trace_dir` | Dossier serveur où écrire le corps des réponses (optionnel) |

## Champs natifs et champs Studio historiques

Le module ne crée que des champs natifs, préfixés `rpbm_`, déclarés dans `models/*.py` (voir
[technique/champs/](champs/README.md)). Il ne crée plus aucun champ Studio : l'ancien
`pre_init_hook` et ses champs « Studio-like » ont été retirés en `17.0.260921.1`.

### Synchronisation avec les champs Studio historiques

`models/legacy_fields.py` est le seul fichier du module qui cite un nom `x_studio_*`. Il contient la
table de correspondance natif → Studio (14 champs sur `crm.lead`, 1 sur `sale.order.line`), les
convertisseurs (énergie, date `MM/YYYY`, pièce concernée, lieu, stock, référentiels Studio
marque/modèle ↔ Fleet par nom normalisé) et le mixin `rpbm.legacy.sync.mixin` : chaque écriture
d'un champ natif est recopiée dans le champ Studio s'il existe, et une saisie Studio seule met à
jour le natif. Tout accès est gardé par `name in model._fields` : sur une base sans ces champs, le
mixin ne fait rien et le module fonctionne à l'identique. Les automatisations et calculs Studio
(cascade de prix sur « Pièce concernée », « Tarif x glass ») continuent donc de tourner pendant la
transition.

### Migration `17.0.260921.1`

Au premier passage sur une base existante, `migrations/17.0.260921.1/post-native-fields.py` :
1. recopie les champs créés par l'ancien hook vers les natifs (`fleet.vehicle`, `product.*`,
   véhicule et catégorie de l'opportunité) ;
2. remplit les natifs de `crm.lead` depuis les champs Studio historiques (SQL pour les valeurs
   simples, ORM pour marque/modèle avec création des marques et modèles Fleet manquants), et
   `sale.order.line.rpbm_xglass_price` depuis `x_studio_prix_x_glass` ;
3. rafraîchit les miroirs stockés de `sale.order` et `stock.picking` ;
4. supprime les champs que le module avait lui-même créés (11 champs Studio-like du hook, 16 alias
   `x_rpbm_vehicle_*`) uniquement s'ils ne sont plus référencés par aucune vue, automatisation,
   action serveur, filtre ni export ; sinon ils sont conservés et listés dans le journal.

Les champs Studio historiques des utilisateurs ne sont jamais supprimés par le module.

## Intégration dans les vues

Le widget et les champs natifs `rpbm_*` sont ajoutés par les vues versionnées du module :

| Fichier | Vues standard héritées | Ajouts |
|---|---|---|
| `views/crm_lead_views.xml` | formulaire, recherche et liste des opportunités | onglet « Véhicule (X'Glass) » ; recherche et regroupements véhicule ; colonnes immatriculation, eurocode, marque, modèle — voir [crm-lead](champs/crm-lead.md#vue) |
| `views/sale_order_views.xml` | formulaire, liste et recherche des devis | onglet ; colonnes immatriculation, marque, modèle ; recherche et regroupements — voir [sale-order](champs/sale-order.md#vue) |
| `views/sale_order_carrier_views.xml` | formulaire des devis | transporteur `carrier_id` |
| `views/sale_order_report_views.xml` | rapports QWeb Studio des devis | mode de remise (AG01-04) |
| `views/account_move_views.xml` | recherche des factures, liste des factures client | recherche et regroupements véhicule ; colonnes — voir [account-move](champs/account-move.md#vue) |
| `views/fleet_vehicle_views.xml` | formulaire véhicule | onglet « X'Glass » |
| `views/product_product_views.xml`, `views/product_template_views.xml` | formulaires et recherche des articles | eurocode, dimensions, onglet « VSF », filtre « Eurocode » |

Règles d'ancrage des formulaires, listes et recherches :

- **une vue du module n'ancre que sur un nœud standard.** Si une cible créée par Studio disparaît, le formulaire ne s'ouvre plus et l'éditeur Studio casse. Tout ajout dans une section Studio (bouton et champs natifs dans « Informations Véhicule », l'en-tête du devis ou le bloc facture ; libellés « (ancien) » des champs historiques) passe par le script `studio_views.py` (voir [`Jobs/rpbm_agent_stock`](../../../Jobs/rpbm_agent_stock/README.md)), à rejouer après la mise à jour du module. Les rapports QWeb, qui héritent de vues Studio par leur identifiant externe, sont l'exception historique d'AG01-04 ;
- **jamais de `<separator/>` dans une recherche** : les personnalisations Studio des recherches opportunités et factures visent des séparateurs par position (`separator[6]`, `separator[5]`) ;
- **jamais de champ nommé `phone` ni `invoice_partner_display_name` dans une liste** : les listes Studio des opportunités et des factures visent la deuxième occurrence de ces champs (`[2]`).

Le champ combiné « Véhicule » des recherches cherche en une saisie dans l'immatriculation, le VIN (sauf sur la facture), la marque et le modèle.

Le comportement du widget s'adapte selon `resModel` de l'enregistrement courant (`crm.lead` ou `sale.order`) ; aucun autre modèle n'a de dialog — voir [frontend](frontend.md).

### `carrier_id` et préremplissage logistique

`sale.order.carrier_id` est le champ natif de `delivery`. La vue du module est
versionnée avec une priorité supérieure aux personnalisations Studio afin que le
champ reste disponible après une reconstruction de branche. Le module ne crée
pas les transporteurs : leur création et leurs routes restent sous la
responsabilité de [`Jobs/rpbm_agent_stock/setup_stock_architecture.py`](../../../Jobs/rpbm_agent_stock/setup_stock_architecture.py).

À la création d'un nouveau devis, le modèle lit
`crm.lead.x_studio_lieu_intervention` et recherche un transporteur actif de la
bonne société ou global. Une absence, une ambiguïté ou un défaut de droits est
journalisé et laisse le champ vide ; aucun fallback Galleria n'est appliqué. Le
changement d'opportunité préremplit uniquement un nouveau brouillon vide et ne
remplace jamais un choix existant. Toute confirmation de `sale.order` exige
ensuite un `carrier_id`, afin d'éviter le routage implicite Odoo.

En préproduction, la vue complémentaire temporaire
`sale.order.form.rpbm.transporteur.visible` doit être désactivée après
vérification de la vue versionnée du module, sans supprimer la vue ni aucun
champ. Toute autre vue active contenant `carrier_id` doit être contrôlée avant
la mise à jour pour éviter un affichage en double.

**Double bouton assumé (décision du 2026-09-28)** : le widget est présent à la fois dans l'onglet du module et dans la section Studio où `studio_views.py` l'ajoute ; les deux ouvrent la même dialog. Un widget ajouté **à la main** via Studio en dehors du script ferait en revanche un troisième bouton : le retirer. Contrôle : `env['ir.ui.view'].search([('model','in',['crm.lead','sale.order'])]).filtered(lambda v: 'rpbm_agent_widget' in (v.arch_db or ''))` ne doit renvoyer que les vues du module et les vues Studio patchées par le script.

## Gestion d'erreurs

`vsf.py`/`xglass.py` exposent chacun une paire d'exceptions typées (`VSFError`/`VSFAuthError`, `XGlassError`/`XGlassAuthError`) plutôt que d'avaler silencieusement les échecs ou de lever des `Exception` nues :
- Toutes les requêtes portail passent par des wrappers `get()`/`post()` avec timeout (20 s) et conversion des erreurs réseau (`requests.exceptions.RequestException`) en `VSFError`/`XGlassError`.
- `auth()` vérifie réellement le succès de la connexion (URL finale après redirections) au lieu de retourner une réponse jamais inspectée, et lève `XGlassAuthError`/`VSFAuthError` en cas d'échec — voir [Authentification des portails](#authentification-des-portails) pour le détail des deux mécanismes.
- Les recherches (`searchImmatriculation`, `searchBaseEurocode`, `getPieceAm`) distinguent "recherche légitimement sans résultat" (`[]`, comportement inchangé) d'une vraie erreur portail, qui remonte en `odoo.exceptions.UserError` — visible nativement par l'utilisateur via l'infrastructure JSON-RPC standard d'Odoo. Pour VSF, la page « aucun résultat » est reconnue comme une recherche sans résultat depuis le lot `17.0.261006.1` ([backend](backend.md#recherche-sans-résultat-r24)) ; auparavant elle remontait en « portail VSF inaccessible ».
- Côté widget, `runAsync()` (`utils.js`) affiche désormais une notification (service Odoo `notification`, type `danger`) en plus du `console.error` existant.

## Authentification des portails

Comportements vérifiés contre les portails réels (transcriptions HTTP obtenues via `debug_portals.py`, voir ci-dessous) — ne pas « corriger » ces mécanismes sans rejouer une trace :

**X'Glass** (Spring Security)
- Le POST de login exige un `JSESSIONID` déjà posé : sans GET préalable il échoue avec `errorCode=10`. `auth()` fait donc un GET `/mainMenu.html` avant chaque tentative.
- Une seule session par identifiant : tant qu'une session est ouverte ailleurs, le login est refusé par une redirection vers `login.html?error=password.mismatch` — **message trompeur**, identique à celui d'un mauvais mot de passe. La tentative suivante évince la session restée ouverte et aboutit : `auth()` réessaie donc exactement une fois, puis lève `XGlassAuthError`.
- Spring rejoue après login la dernière requête refusée. Le GET préalable doit viser une page inoffensive : appeler `close()` (GET `/logout.html`) entre deux tentatives — ce que faisait l'implémentation précédente — déconnectait aussitôt le login réussi et imposait une 3ᵉ tentative pour aboutir.
- `/rpbm_agent_auth` ferme l'agent **précédent** (qui porte encore ses cookies, donc son logout aboutit) avant d'en instancier un nouveau, ce qui libère la session portail d'un widget fermé sans passer par `/rpbm_agent_close`.
- Le certificat TLS de `portail-xglass.com` est valide (Let's Encrypt) : aucun `verify=False` n'est nécessaire. L'ancien `verify=False` sur le login désactivait durablement la vérification pour tout le pool de connexions de la session (urllib3 mémorise `cert_reqs` par hôte), d'où les `InsecureRequestWarning` avec trace complète sur *toutes* les requêtes X'Glass suivantes.

**VSF** (Laravel)
- Succès = redirection vers l'accueil ; échec = retour sur `/identification`. Le test porte donc sur l'URL finale.
- Ne pas tester la présence d'un champ `_token` : les pages authentifiées en contiennent un aussi (formulaire de déconnexion), ce qui faisait échouer une connexion pourtant réussie.
- **Plusieurs sessions simultanées sur un même compte** (trace T1, 2026-10-06, deux connexions) : A se connecte et cherche `6108A` (21 lignes), B se connecte avec le même compte, A cherche toujours, B cherche, B se déconnecte (`POST /deconnexion` avec `_token`), A cherche toujours. Contrairement à X'Glass, VSF accepte donc plusieurs sessions, et nos connexions ne déconnectent pas les vendeurs connectés à VSF dans leur navigateur. C'est ce qui permet de ne plus poser de verrou sur VSF (lot E2) ; voir [backend](backend.md#vsf-session-à-la-demande-lot-e2).
- Une recherche sans résultat n'est ni une erreur ni une session expirée : `GET /catalogue/vitrage?search=<valeur>` répond 200, authentifié, avec la page « Aucun résultat ne correspond à votre recherche. » et sans `#articles-list-container` (trace du 2026-10-06 : `9999Z`, `61-08A`, `A+B &C D` ; `6108a` donne les mêmes 21 articles que `6108A`, VSF ignore la casse). Une session expirée se reconnaît à l'URL de connexion, jamais à l'absence de liste ; voir [backend](backend.md#recherche-sans-résultat-r24).

## Débogage des portails

- `controllers/portal_trace.py` — traçage HTTP branché sur les sessions `requests` des deux agents : une ligne de log par requête (méthode, URL, statut, redirection, cookies posés, durée, taille), mots de passe et jetons masqués. Inactif par défaut ; activé sur une instance via `rpbm_agent.trace` (+ `rpbm_agent.trace_dir` pour écrire le corps des réponses), relu à chaque `/rpbm_agent_auth` et, depuis le lot E2, à la connexion VSF à la demande (`_configure_trace`, seulement quand l'agent VSF n'est pas encore connecté : l'appel remet à zéro la numérotation des requêtes tracées).
- [`debug_portals.py`](../../debug_portals.py) (racine du module) — rejoue authentification et scraping **hors Odoo**, avec les identifiants de `.env` :
  ```
  python debug_portals.py                          # auth des deux portails
  python debug_portals.py --immat DS808DZ          # + recherche véhicule
  python debug_portals.py --portal vsf --eurocode 6539R
  python debug_portals.py --dump trace/            # + dump du HTML reçu
  ```
  Attention : X'Glass n'autorisant qu'une session par identifiant, lancer ce script pendant qu'un utilisateur se sert du widget invalide sa session.
- [`test_portal_auth.py`](../../test_portal_auth.py) — vérifie la logique d'authentification et de parsing sans réseau (portails simulés d'après les traces ci-dessus) : `python test_portal_auth.py`. Les mêmes tests sont exposés au lanceur Odoo (`--test-enable`) par `tests/test_portal_parsing.py`.

## Concurrence — verrou de session

Le portail X'Glass n'autorise qu'**une seule session active par identifiant**, et RPBM ne dispose que d'un seul identifiant X'Glass (pas de pool de comptes) — deux utilisateurs Odoo ne peuvent donc jamais utiliser X'Glass en même temps sans que l'un invalide la session de l'autre côté portail, et ce pour toute la durée d'une interaction (pas seulement l'instant du login).

**Le verrou ne protège que X'Glass** (lot E2, décision du 2026-10-06, [VD-05](../validations-metier.md#historique-des-décisions)). VSF accepte plusieurs sessions simultanées sur le même compte (trace T1, voir [Authentification des portails](#authentification-des-portails)) : ses routes (`/searchBaseEurocode`, `/getVsfArticleDetails`, `/createProduct`) n'acquièrent ni ne prolongent le verrou, si bien que plusieurs vendeurs peuvent chercher sur VSF en même temps, et qu'un devis s'ouvre sans prendre le verrou.

Solution retenue : un verrou applicatif réutilisant `ir.config_parameter` (`rpbm_agent.session_lock`, JSON `{uid, touched_at}`), avec compare-and-set atomique via `SELECT ... FOR UPDATE` (`main.py::_lock_row`) — pas de nouveau modèle/`ir.model.access.csv` pour un verrou global unique. `/rpbm_agent_auth` acquiert le verrou (rejette avec `UserError` "actuellement utilisé par X" si déjà tenu par un autre utilisateur et non expiré) ; `/rpbm_agent_close` le libère ; les routes de navigation et de recherche X'Glass le rafraîchissent (décorateur `@_touch_agent_lock`), les routes VSF non. `/createVehicule` reste volontairement hors de ce décorateur : l'enregistrement Odoo peut être créé après une fermeture de session, seule son image X'Glass facultative est alors ignorée. Expiration glissante de 15 minutes en filet de sécurité (session abandonnée sans passer par Confirmer/Annuler — crash navigateur, perte réseau).

Conséquences du lot E2, connues et acceptées : le travail VSF seul ne prolonge plus le verrou, si bien que l'appel X'Glass qui suit un long travail VSF se reconnecte de façon transparente (reconnexion à chaud) et que `/createVehicule` peut créer le véhicule sans image (`has_active_agent_lock`) . Fermer le dialog pendant « Charger X'Glass » ne laisse pas le verrou pris : le dialog détruit envoie `/rpbm_agent_close` à la réponse de `/rpbm_agent_auth`, y compris pour une reconnexion sur le devis.

Alternative non retenue (business, pas technique) : un pool de plusieurs identifiants X'Glass permettrait une vraie concurrence sans file d'attente, mais dépend d'une démarche contractuelle auprès du portail — non disponible actuellement. Pour VSF, le besoin a disparu avec la trace T1.

## Reconnexion à chaud

L'expiration du verrou ou d'une session X'Glass authentifiée est remontée au widget sous le type
JSON-RPC `AgentSessionExpiredError` (depuis le lot E2, une expiration VSF n'en fait plus partie : le
serveur se reconnecte à VSF et rejoue une fois, voir [backend](backend.md#vsf-session-à-la-demande-lot-e2)).
Un arrêt du processus Odoo (environ 2 minutes sans requête, ou mise à jour du build) fait perdre
les sessions portail : la requête suivante provoque cette expiration pour X'Glass. Le widget peut alors appeler à nouveau
`/rpbm_agent_auth` : le verrou est repris par le même utilisateur, les agents sont recréés,
puis la dernière recherche par immatriculation aboutie et la sélection du véhicule sont
rejouées côté X'Glass (`/searchImmatriculation` puis `/getPlanche`). Une erreur réseau, une
erreur de parsing ou des identifiants refusés ne sont pas considérés comme récupérables
automatiquement.

Faits établis par deux traces réelles du 2026-10-02 (GS600HH : véhicule 471612, planche 26881,
calque 59, famille 3464, pièce OE 3510699), à ne pas modifier sans nouvelle trace :

- **Sélection sans recherche.** Dans une session neuve, `POST selectVehicule.html` sans
  recherche préalable mène à `displayPlanche.html`, qui redirige vers `mainMenu.html?errorCode=`.
  La sélection est refusée sans erreur : `/getPlanche` renvoie `{}`.
- **Pièces AM sans contexte véhicule.** Dans ce cas, `findSelectionsPiecesAmView` répond :
  - par pièce OE : une entrée non filtrée (`6108AGABCHMU`, « Volant à droite »), sans
    validité ni remarque, au lieu de `[]` ;
  - par famille : `{"errorCode": "10", "selectionsPiecesAmView": null}`.

  Ce sont les trois symptômes relevés en recette R11.
- **Page des pièces refusée.** `affichagePieces.html` est lui-même refusé (302 vers
  `mainMenu.html?errorCode=10`) : rejouer la page des pièces ne suffit pas.
- **`initRechercheVehicule.html` seul.** Il fait aboutir la sélection et redonne les mêmes
  listes AM. La planche n'a toutefois plus ni VIN, ni immatriculation, ni CNIT, ni date de MEC
  (`critereAAAIsNull = 'true'`).
- **Séquence retenue.** `/searchImmatriculation` (`initRechercheVehicule` + `searchImmat`) puis
  `/getPlanche` redonne une planche identique à la référence et des listes AM identiques
  (identifiants, `debutValidite`, `remarque`). `affichagePieces` n'est pas nécessaire.
- **Immatriculation rejouée.** Le widget rejoue celle de la dernière recherche aboutie, et non
  la valeur courante du champ.
- **Cache vidé.** Le cache « Autres marques AM » est vidé après une reconnexion réussie.

## Assets

```python
'assets': {
    'web.assets_backend': ['rpbm_agent/static/src/*'],
}
```
Un seul bundle, chargé en glob plat sur `static/src/*` (pas de séparation par sous-dossier `js/`/`xml/`).
