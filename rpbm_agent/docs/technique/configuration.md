# Configuration & déploiement

## Installation du module

Déposer `rpbm_agent/` dans le dossier `addons` de l'instance Odoo 17, puis installer via l'interface d'administration (`depends: crm, fleet, sale_crm`).

## Dépendances Python

| Fichier | Contenu |
|---|---|
| `__manifest__.py` → `external_dependencies.python` | `beautifulsoup4`, `python-dotenv` |
| `controllers/requirements.txt` | `beautifulsoup4`, `python-dotenv` (tous deux actifs) |

**Incohérence restante** : le code (`vsf.py`, `xglass.py`) importe aussi activement `requests`, qui n'est déclaré nulle part comme dépendance installée — il fonctionne uniquement parce qu'il est déjà présent dans l'environnement Python d'Odoo par ailleurs. À corriger dans une passe ultérieure (voir [état des lieux](../etat-des-lieux.md)).

`python-dotenv` / `.env` ne sont utiles qu'en **exécution standalone hors Odoo** (tests manuels des scripts `vsf.py`/`xglass.py`, notebooks) : en production, les identifiants viennent exclusivement de `ir.config_parameter` via `/rpbm_agent_auth`.

## Paramètres système requis

À créer dans `Réglages > Technique > Paramètres > Paramètres système` :

| Clé | Description |
|---|---|
| `XGLASS_USER` | Identifiant du portail X'Glass |
| `XGLASS_PASS` | Mot de passe du portail X'Glass |
| `VSF_LOGIN` | Identifiant du portail VSF |
| `VSF_PASSWORD` | Mot de passe du portail VSF |

Peuvent être créés manuellement ou par script (ex. `env['ir.config_parameter'].sudo().set_param(...)`).

## Champs Odoo Studio requis

Les champs `x_studio_*` consommés par le code sont créés automatiquement à l'installation par `pre_init_hook` (`rpbm_agent/hooks.py`) — voir le mécanisme ci-dessous. État détaillé par modèle (quels champs, lesquels sont nouveaux vs déjà existants sur une instance donnée, related, obsolètes) : [technique/champs/](champs/README.md).

### Mécanisme retenu : `pre_init_hook` + contexte Studio

Vérifié dans le code source d'Odoo Enterprise (`D:\git\odoo_17\enterprise\web_studio`, voir [directives projet](../../../CLAUDE.md#code-source-odoo-vérification-de-méthodes)) : `ir.model.fields` hérite de `studio.mixin` (`web_studio/models/ir_model.py:598`). Ce mixin surcharge `create()`/`write()` : si le contexte contient `studio=True` (et pas `install_mode`), il appelle automatiquement `create_studio_model_data()`, qui :
1. récupère (ou **crée**) le module `studio_customization` via `ir.module.module.get_studio_module()` — donc pas besoin qu'il préexiste ;
2. crée l'`ir.model.data` correspondant (`module='studio_customization'`, flag `studio=True`, `noupdate` forcé à `True` dès la première modification ultérieure du champ).

Il suffit donc de passer `studio=True` dans le contexte lors de la création — aucune manipulation manuelle d'`ir.model.data`. Implémenté dans [`hooks.py`](../../hooks.py) (`FIELDS_TO_ENSURE` + `pre_init_hook`, idempotent — ignore tout champ déjà présent).

Conséquence : le champ est créé exactement comme le ferait un humain dans Studio (même mixin, même `ir.model.data`), et une désinstallation de `rpbm_agent` ne le supprime pas (seuls les `ir.model.data` rattachés au module désinstallé sont nettoyés).

**Pourquoi `pre_init_hook` et pas `post_init_hook`** : ce module livre aussi des vues XML (`views/*.xml`, voir ci-dessous) qui référencent ces mêmes champs. Vérifié dans `odoo/modules/loading.py:189-247` : l'ordre réel est `pre_init_hook(env)` → chargement des modèles du module → chargement des données `data` (dont les vues) → `post_init_hook(env)` seulement en tout dernier. Avec un `post_init_hook`, les vues échoueraient à se charger (champ inconnu) puisqu'elles sont traitées avant lui. Vérifié également que `env` reçu par ces hooks a un contexte vide (`loading.py:426`, `api.Environment(cr, SUPERUSER_ID, {})`) — pas de risque que `install_mode` soit déjà présent et court-circuite le mécanisme Studio.

**Limites** : ce comportement Studio est fourni par `web_studio` (Enterprise) — sans ce module installé, `studio=True` n'a aucun effet particulier (le champ est quand même créé, juste sans traçage Studio) ; mécanisme interne non documenté publiquement par Odoo, sans garantie de stabilité inter-versions.

## Intégration dans les vues

Le widget et les champs `x_studio_vehicle_id`/`x_studio_categorie_xglass` sont ajoutés par les vues versionnées du module (`views/crm_lead_views.xml`, `views/sale_order_views.xml`, `views/fleet_vehicle_views.xml`, `views/product_product_views.xml`), chacune héritant de la vue formulaire de base du modèle concerné et ajoutant un nouvel onglet. Le comportement du widget s'adapte automatiquement selon `resModel` de l'enregistrement courant (`crm.lead`, `sale.order`, ou dialog générique pour tout autre modèle — voir [frontend](frontend.md)).

**Caveat de déploiement** : sur toute instance où le tag `<widget name="rpbm_agent_widget"/>` aurait déjà été ajouté à la main via Studio (probable en production, la documentation historique indiquant le widget déjà en usage), il faut le retirer de la vue Studio **avant** de déployer cette version du module, sous peine d'afficher le bouton en double. Vérification : `env['ir.ui.view'].search([('model','in',['crm.lead','sale.order'])]).filtered(lambda v: 'rpbm_agent_widget' in (v.arch_db or ''))`.

## Assets

```python
'assets': {
    'web.assets_backend': ['rpbm_agent/static/src/*'],
}
```
Un seul bundle, chargé en glob plat sur `static/src/*` (pas de séparation par sous-dossier `js/`/`xml/`).
