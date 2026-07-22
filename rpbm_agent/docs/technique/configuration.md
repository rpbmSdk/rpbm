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
