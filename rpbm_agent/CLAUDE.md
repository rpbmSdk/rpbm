# Directives — module rpbm_agent

Documentation complète du module : voir [`docs/README.md`](docs/README.md) (fonctionnel, technique avec diagrammes Mermaid, état des lieux).

Avant toute modification, consulter [`docs/etat-des-lieux.md`](docs/etat-des-lieux.md) — liste les incohérences connues (duplications, code mort, valeurs hardcodées) pour éviter de les reproduire ou de les aggraver.

## Secrets en développement local

Pour exécuter `controllers/vsf.py` / `controllers/xglass.py` en standalone (hors Odoo, ex. notebooks), les secrets de connexion aux portails XGlass et VSF sont lus depuis `controllers/.env` (non suivi par git, chargé via `python-dotenv`) :

- `XGLASS_USER`, `XGLASS_PASS` — identifiants du portail X'Glass
- `VSF_LOGIN`, `VSF_PASSWORD` — identifiants du portail VSF

Ne jamais afficher, logger ou recopier le contenu de ce fichier. En production (exécution via Odoo), ces mêmes identifiants sont configurés en tant que `ir.config_parameter` — voir [`docs/technique/configuration.md`](docs/technique/configuration.md).
