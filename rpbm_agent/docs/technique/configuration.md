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

Le module n'installe **aucun modèle, aucune vue, aucune donnée** (`__manifest__.py` ne déclare pas de clé `data`). Tous les champs `x_studio_*` consommés par le code doivent être créés manuellement via Odoo Studio sur chaque instance avant utilisation — voir le détail par modèle dans le [parcours utilisateur](../fonctionnel/parcours-utilisateur.md#prérequis-avant-utilisation).

Conséquence pratique : ces champs ne sont ni versionnés, ni reproductibles automatiquement d'une instance à l'autre (dev/staging/prod) sans procédure manuelle ou script d'installation dédié.

### État constaté sur `rpbm-preprod` (2026-07-22)

Vérifié directement en base (`ir.model.fields`/`ir.model.data`) via MCP — sur 11 champs consommés par le code, seuls 5 existent :

| Modèle | Champ | Type | Présent ? |
|---|---|---|---|
| `fleet.vehicle` | `x_studio_detail_model` | char | ❌ |
| `fleet.vehicle` | `x_studio_date_mec` | date | ❌ |
| `crm.lead` | `x_studio_field_NVioD` | char | ✅ |
| `crm.lead` | `x_studio_vehicle_id` | many2one → `fleet.vehicle` | ❌ |
| `crm.lead` | `x_studio_categorie_xglass` | char | ❌ |
| `crm.lead` | `x_studio_field_ORIyy` ("Base Eurocode") | char | ✅ (existant, nom technique différent de celui attendu par le code — voir [structure Eurocode](../fonctionnel/parcours-utilisateur.md#structure-des-champs-eurocode-sur-crmlead)) |
| `sale.order` | `x_studio_immatriculation_` | char (related) | ✅ |
| `sale.order` | `x_studio_vehicle_id` | many2one → `fleet.vehicle` | ❌ |
| `sale.order` | `x_studio_categorie_xglass` | char | ❌ |
| `sale.order` | `x_studio_base_eurocode` | char (related) | ✅ |
| `product.product` | `x_studio_reference_constructeur` | char | ❌ (`createProduct` est donc cassé aujourd'hui) |

`x_studio_autre_infos`/`x_studio_note` (documentés dans le Readme historique) ne sont référencés dans aucun code actuel — pas nécessaires à recréer.

### Mécanisme retenu pour un script de pré-installation

Vérifié en base **et** dans le code source d'Odoo Enterprise (`D:\git\odoo_17\enterprise\web_studio`, voir [directives projet](../../../CLAUDE.md#code-source-odoo-vérification-de-méthodes)) : `ir.model.fields` hérite de `studio.mixin` (`web_studio/models/ir_model.py:598`). Ce mixin surcharge `create()`/`write()` : si le contexte contient `studio=True` (et pas `install_mode`), il appelle automatiquement `create_studio_model_data()`, qui :
1. récupère (ou **crée**) le module `studio_customization` via `ir.module.module.get_studio_module()` — donc pas besoin qu'il préexiste ;
2. crée l'`ir.model.data` correspondant (`module='studio_customization'`, flag `studio=True`, `noupdate` forcé à `True` dès la première modification ultérieure du champ).

Il suffit donc de passer `studio=True` dans le contexte lors de la création — aucune manipulation manuelle d'`ir.model.data` :

```python
def post_init_hook(env):
    Fields = env['ir.model.fields'].sudo().with_context(studio=True)
    for model, name, desc, ttype, relation in FIELDS_TO_ENSURE:
        if Fields.search_count([('model', '=', model), ('name', '=', name)]):
            continue  # déjà créé (manuellement ou par une passe précédente)
        vals = {'name': name, 'model_id': env['ir.model']._get_id(model),
                'field_description': desc, 'ttype': ttype, 'state': 'manual'}
        if relation:
            vals['relation'] = relation
        Fields.create(vals)
```

Conséquence : le champ est créé exactement comme le ferait un humain dans Studio (même mixin, même `ir.model.data`), et une désinstallation de `rpbm_agent` ne le supprime pas (seuls les `ir.model.data` rattachés au module désinstallé sont nettoyés).

Vérifié également que `env` dans `post_init_hook` a un contexte vide (`odoo/modules/loading.py:426`, `env = api.Environment(cr, SUPERUSER_ID, {})`) — pas de risque que `install_mode` soit déjà présent et court-circuite le mixin.

**Limites** : ce comportement est fourni par `web_studio` (Enterprise) — sans ce module installé, `studio=True` n'a aucun effet particulier (le champ est quand même créé, juste sans traçage Studio, ce qui reste inoffensif pour l'objectif recherché ici) ; mécanisme interne non documenté publiquement par Odoo, sans garantie de stabilité inter-versions ; ne recrée que le champ, pas son emplacement dans les vues (le tag `<widget name="rpbm_agent_widget"/>` reste à poser manuellement par instance).

## Intégration dans les vues

Le widget s'ajoute à une vue formulaire avec :
```xml
<widget name="rpbm_agent_widget" />
```
Cette balise doit être ajoutée via Odoo Studio (aucune vue XML du module ne la déclare). Le comportement du widget s'adapte automatiquement selon `resModel` de l'enregistrement courant (`crm.lead`, `sale.order`, ou dialog générique pour tout autre modèle — voir [frontend](frontend.md)).

## Assets

```python
'assets': {
    'web.assets_backend': ['rpbm_agent/static/src/*'],
}
```
Un seul bundle, chargé en glob plat sur `static/src/*` (pas de séparation par sous-dossier `js/`/`xml/`).
