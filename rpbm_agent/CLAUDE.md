# Directives — module rpbm_agent

Documentation complète du module : voir [`docs/README.md`](docs/README.md) (fonctionnel, technique avec diagrammes Mermaid, état des lieux).

Avant toute modification, consulter [`docs/etat-des-lieux.md`](docs/etat-des-lieux.md) — liste les incohérences connues (duplications, code mort, valeurs hardcodées) pour éviter de les reproduire ou de les aggraver.

## Débogage des portails X'Glass / VSF

Ne jamais raisonner de mémoire sur le comportement des portails : rejouer une trace HTTP réelle avec [`debug_portals.py`](debug_portals.py) (`python debug_portals.py --immat DS808DZ --dump trace/`), qui trace chaque requête via `controllers/portal_trace.py`. Les mécanismes déjà vérifiés de cette manière (session unique X'Glass, rejeu de requête Spring, détection de succès VSF) sont documentés dans [`docs/technique/configuration.md`](docs/technique/configuration.md#authentification-des-portails) — les modifier sans nouvelle trace fait régresser l'authentification. `python test_portal_auth.py` vérifie cette logique sans réseau.

## Secrets en développement local

Pour exécuter `controllers/vsf.py` / `controllers/xglass.py` en standalone (hors Odoo, ex. notebooks), les secrets de connexion aux portails XGlass et VSF sont lus depuis `.env` (racine du module, non suivi par git, chargé via `python-dotenv` — `dotenv.load_dotenv()` sans argument recherche `.env` en remontant les dossiers parents depuis `controllers/`, donc le trouve à la racine) :

- `XGLASS_USER`, `XGLASS_PASS` — identifiants du portail X'Glass
- `VSF_LOGIN`, `VSF_PASSWORD` — identifiants du portail VSF

Ne jamais afficher, logger ou recopier le contenu de ce fichier. En production (exécution via Odoo), ces mêmes identifiants sont configurés en tant que `ir.config_parameter` — voir [`docs/technique/configuration.md`](docs/technique/configuration.md) et [`push_credentials.py`](push_credentials.py) pour les pousser automatiquement depuis ce même `.env`.
