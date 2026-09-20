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

Les paramètres `rpbm_agent.vsf_*` sont lus à chaque recherche VSF et création de produit (`controllers/vsf_config.py`), `rpbm_agent.labor_product_*` à chaque `/getPieces`. Une valeur absente conserve le comportement historique ; une valeur invalide produit une erreur explicite et n'est jamais appliquée silencieusement.

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

## Champs Odoo Studio requis

Les champs `x_studio_*` consommés par le code sont créés automatiquement à l'installation par `pre_init_hook` (`rpbm_agent/hooks.py`) — voir le mécanisme ci-dessous. État détaillé par modèle (quels champs, lesquels sont nouveaux vs déjà existants sur une instance donnée, related, obsolètes) : [technique/champs/](champs/README.md).

### Mécanisme retenu : `pre_init_hook` + contexte Studio

Vérifié dans le code source d'Odoo Enterprise (`D:\git\odoo_17\enterprise\web_studio`, voir [directives projet](../../../CLAUDE.md#code-source-odoo-vérification-de-méthodes)) : `ir.model.fields` hérite de `studio.mixin` (`web_studio/models/ir_model.py:598`). Ce mixin surcharge `create()`/`write()` : si le contexte contient `studio=True` (et pas `install_mode`), il appelle automatiquement `create_studio_model_data()`, qui :
1. récupère (ou **crée**) le module `studio_customization` via `ir.module.module.get_studio_module()` — donc pas besoin qu'il préexiste ;
2. crée l'`ir.model.data` correspondant (`module='studio_customization'`, flag `studio=True`, `noupdate` forcé à `True` dès la première modification ultérieure du champ).

Il suffit donc de passer `studio=True` dans le contexte lors de la création — aucune manipulation manuelle d'`ir.model.data`. Implémenté dans [`hooks.py`](../../hooks.py) (`FIELDS_TO_ENSURE` + `pre_init_hook`, idempotent — ignore tout champ déjà présent).

Depuis AG01-01, `FIELDS_TO_ENSURE` ne contient plus les huit doublons Fleet
`x_rpbm_vehicle_*` sur `crm.lead` et `sale.order`. Cette absence désactive leur
création future uniquement ; elle ne supprime ni ne renomme les champs qui
existent déjà dans une base.

Conséquence : le champ est créé exactement comme le ferait un humain dans Studio (même mixin, même `ir.model.data`), et une désinstallation de `rpbm_agent` ne le supprime pas (seuls les `ir.model.data` rattachés au module désinstallé sont nettoyés).

**Pourquoi `pre_init_hook` et pas `post_init_hook`** : ce module livre aussi des vues XML (`views/*.xml`, voir ci-dessous) qui référencent ces mêmes champs. Vérifié dans `odoo/modules/loading.py:189-247` : l'ordre réel est `pre_init_hook(env)` → chargement des modèles du module → chargement des données `data` (dont les vues) → `post_init_hook(env)` seulement en tout dernier. Avec un `post_init_hook`, les vues échoueraient à se charger (champ inconnu) puisqu'elles sont traitées avant lui. Vérifié également que `env` reçu par ces hooks a un contexte vide (`loading.py:426`, `api.Environment(cr, SUPERUSER_ID, {})`) — pas de risque que `install_mode` soit déjà présent et court-circuite le mécanisme Studio.

**Limites** : ce comportement Studio est fourni par `web_studio` (Enterprise) — sans ce module installé, `studio=True` n'a aucun effet particulier (le champ est quand même créé, juste sans traçage Studio) ; mécanisme interne non documenté publiquement par Odoo, sans garantie de stabilité inter-versions.

## Intégration dans les vues

Le widget et les champs `x_studio_vehicle_id`/`x_studio_categorie_xglass` sont ajoutés par les vues versionnées du module (`views/crm_lead_views.xml`, `views/sale_order_views.xml`, `views/sale_order_carrier_views.xml`, `views/fleet_vehicle_views.xml`, `views/product_product_views.xml`), chacune héritant de la vue formulaire de base du modèle concerné et ajoutant un nouvel onglet ou le champ logistique. Le comportement du widget s'adapte automatiquement selon `resModel` de l'enregistrement courant (`crm.lead`, `sale.order`, ou dialog générique pour tout autre modèle — voir [frontend](frontend.md)).

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

**Caveat de déploiement** : sur toute instance où le tag `<widget name="rpbm_agent_widget"/>` aurait déjà été ajouté à la main via Studio (probable en production, la documentation historique indiquant le widget déjà en usage), il faut le retirer de la vue Studio **avant** de déployer cette version du module, sous peine d'afficher le bouton en double. Vérification : `env['ir.ui.view'].search([('model','in',['crm.lead','sale.order'])]).filtered(lambda v: 'rpbm_agent_widget' in (v.arch_db or ''))`.

## Gestion d'erreurs

`vsf.py`/`xglass.py` exposent chacun une paire d'exceptions typées (`VSFError`/`VSFAuthError`, `XGlassError`/`XGlassAuthError`) plutôt que d'avaler silencieusement les échecs ou de lever des `Exception` nues :
- Toutes les requêtes portail passent par des wrappers `get()`/`post()` avec timeout (20 s) et conversion des erreurs réseau (`requests.exceptions.RequestException`) en `VSFError`/`XGlassError`.
- `auth()` vérifie réellement le succès de la connexion (URL finale après redirections) au lieu de retourner une réponse jamais inspectée, et lève `XGlassAuthError`/`VSFAuthError` en cas d'échec — voir [Authentification des portails](#authentification-des-portails) pour le détail des deux mécanismes.
- Les recherches (`searchImmatriculation`, `searchBaseEurocode`, `getPieceAm`) distinguent "recherche légitimement sans résultat" (`[]`, comportement inchangé) d'une vraie erreur portail, qui remonte en `odoo.exceptions.UserError` — visible nativement par l'utilisateur via l'infrastructure JSON-RPC standard d'Odoo.
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

## Débogage des portails

- `controllers/portal_trace.py` — traçage HTTP branché sur les sessions `requests` des deux agents : une ligne de log par requête (méthode, URL, statut, redirection, cookies posés, durée, taille), mots de passe et jetons masqués. Inactif par défaut ; activé sur une instance via `rpbm_agent.trace` (+ `rpbm_agent.trace_dir` pour écrire le corps des réponses), relu à chaque `/rpbm_agent_auth`.
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

Le portail X'Glass n'autorise qu'**une seule session active par identifiant**, et RPBM ne dispose que d'un seul identifiant partagé X'Glass et d'un seul VSF (pas de pool de comptes) — deux utilisateurs Odoo ne peuvent donc jamais utiliser le widget en même temps sans que l'un invalide la session de l'autre côté portail, et ce pour toute la durée d'une interaction (pas seulement l'instant du login).

Solution retenue : un verrou applicatif réutilisant `ir.config_parameter` (`rpbm_agent.session_lock`, JSON `{uid, touched_at}`), avec compare-and-set atomique via `SELECT ... FOR UPDATE` (`main.py::_lock_row`) — pas de nouveau modèle/`ir.model.access.csv` pour un verrou global unique. `/rpbm_agent_auth` acquiert le verrou (rejette avec `UserError` "actuellement utilisé par X" si déjà tenu par un autre utilisateur et non expiré) ; `/rpbm_agent_close` le libère ; les routes de navigation et de recherche portail le rafraîchissent (décorateur `@_touch_agent_lock`). `/createVehicule` reste volontairement hors de ce décorateur : l'enregistrement Odoo peut être créé après une fermeture de session, seule son image X'Glass facultative est alors ignorée. Expiration glissante de 15 minutes en filet de sécurité (session abandonnée sans passer par Confirmer/Annuler — crash navigateur, perte réseau).

Alternative non retenue (business, pas technique) : un pool de plusieurs identifiants X'Glass/VSF permettrait une vraie concurrence sans file d'attente, mais dépend d'une démarche contractuelle auprès des portails — non disponible actuellement.

## Reconnexion à chaud

L'expiration du verrou ou d'une session authentifiée est remontée au widget sous le type
JSON-RPC `AgentSessionExpiredError`. Le widget peut alors appeler à nouveau
`/rpbm_agent_auth` : le verrou est repris par le même utilisateur, les agents sont recréés et
le véhicule déjà sélectionné est réactivé côté X'Glass. Une erreur réseau, une erreur de
parsing ou des identifiants refusés ne sont pas considérés comme récupérables automatiquement.

## Assets

```python
'assets': {
    'web.assets_backend': ['rpbm_agent/static/src/*'],
}
```
Un seul bundle, chargé en glob plat sur `static/src/*` (pas de séparation par sous-dossier `js/`/`xml/`).
