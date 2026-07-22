# Directives projet

## Débogage sur l'instance de staging

Le MCP `chrome-devtools` peut être utilisé pour se connecter à l'instance de staging Odoo et déboguer directement dans le navigateur (inspection DOM, console, réseau, etc.).

- URL de l'instance de staging : https://rpbm-pre-prod.odoo.com/web

## Accès aux données Odoo (lecture/écriture via MCP)

Les connecteurs MCP globaux `claude.ai RPBM` (et les 4 autres instances multi-tenant : GRH, JSGRH, FNDM, Stanadigme) sont **désactivés pour ce projet** (règle `deny` dans `.claude/settings.local.json`).

Pour récupérer des valeurs ou exécuter des méthodes sur l'instance Odoo de ce projet, utiliser **exclusivement** la skill `paradigme-mcp` avec le profil `rpbm-preprod` (défini dans `~/.paradigme/paradigme_odoo_mcp.yaml`).

## Code source Odoo (vérification de méthodes)

Le dépôt `D:\git\odoo_17` contient le code source complet d'Odoo 17 (version utilisée par cette instance) :
- `D:\git\odoo_17\odoo17` : Odoo Community (core)
- `D:\git\odoo_17\enterprise` : modules Enterprise (dont `web_studio`)

À utiliser pour vérifier le comportement réel d'une méthode/mécanisme Odoo (signatures, hooks, effets de bord) plutôt que de se fier à la mémoire ou à la documentation officielle, qui peuvent être imprécises sur des détails d'implémentation. Exemple concret : `enterprise/web_studio/models/studio_mixin.py` et `ir_model.py` (`create_studio_model_data`, `get_studio_module`) montrent que passer `context={'studio': True}` lors de la création d'un `ir.model.fields` (ou `ir.ui.view`, `ir.actions.*`, etc.) suffit à le faire reconnaître comme un champ Studio : le mixin crée automatiquement l'`ir.model.data` rattaché au module `studio_customization` (qu'il crée lui-même s'il n'existe pas encore, voir `ir_module_module.get_studio_module()`).

## Pratiques de développement

### Commits

Les commits de ce dépôt sont effectués avec Claude Haiku 4.5 — ce modèle plus léger suffit pour les tâches de staging/commit (analyse d'intention, composition de message) et laisse le contexte plus large disponible pour le travail analytique lourd sur le code source (exploration, refactoring, débogage).
