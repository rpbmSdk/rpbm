# Directives — module rpbm_agent

Documentation complète du module : voir [`docs/README.md`](docs/README.md) (fonctionnel, technique avec diagrammes Mermaid, état des lieux).

Avant toute modification, consulter [`docs/etat-des-lieux.md`](docs/etat-des-lieux.md) — liste les incohérences connues (duplications, code mort, valeurs hardcodées) pour éviter de les reproduire ou de les aggraver.

Les travaux en cours sur l'UI et le transfert vers Odoo suivent [`docs/roadmap.md`](docs/roadmap.md), par lots ordonnés (L0 diagnostic → L1 transfert → L2 UI → L3 hygiène). Mettre à jour l'état des items au fur et à mesure des implémentations.

## Champs : natifs `rpbm_*`, jamais de Studio en dur

Toute information stockée par le module vit dans un champ natif déclaré en Python, préfixé `rpbm_`
(jamais `x_`). Les champs Studio historiques de l'instance ne sont cités **que** dans la table
[`models/legacy_fields.py`](models/legacy_fields.py), qui les alimente en double tant qu'ils existent ;
aucun nom `x_studio_*` ailleurs (Python, JS, vues, rapports, tests), et tout accès gardé par
`name in model._fields` : le module doit s'installer et fonctionner sur une base sans ces champs.
Pour consommer un nouveau champ Studio : créer son équivalent natif, l'ajouter à la table avec son
convertisseur, remplir le natif par migration. Ne jamais supprimer un champ Studio historique
depuis le module. Détail et audit : `docs/architecture-champs.local.md` (non suivi) et
[`docs/technique/champs/`](docs/technique/champs/README.md).

## Déploiement : bumper la version du manifest

**À chaque modification destinée à être déployée** (JS, XML, Python), incrémenter `version` dans [`__manifest__.py`](__manifest__.py) — sinon Odoo.sh ne recharge pas le module (surtout les assets JS/XML mis en cache). Format `17.0.AAMMJJ.N` (date + compteur du jour) : ex. `17.0.260725.1`. Le faire **systématiquement** avant de committer une modif à déployer.

## Débogage des portails X'Glass / VSF

Ne jamais raisonner de mémoire sur le comportement des portails : rejouer une trace HTTP réelle avec [`debug_portals.py`](debug_portals.py) (`python debug_portals.py --immat DS808DZ --dump trace/`), qui trace chaque requête via `controllers/portal_trace.py`. Les mécanismes déjà vérifiés de cette manière (session unique X'Glass, rejeu de requête Spring, détection de succès VSF) sont documentés dans [`docs/technique/configuration.md`](docs/technique/configuration.md#authentification-des-portails) — les modifier sans nouvelle trace fait régresser l'authentification. `python test_portal_auth.py` vérifie cette logique sans réseau.

## Secrets en développement local

Pour exécuter les agents `controllers/vsf.py` / `controllers/xglass.py` hors Odoo (via [`debug_portals.py`](debug_portals.py) ou un notebook), les secrets de connexion aux portails XGlass et VSF sont lus depuis `.env` (racine du module, non suivi par git). Ce sont les scripts standalone qui chargent ce fichier avec `python-dotenv` ; les controllers eux-mêmes ne lisent jamais `.env` :

- `XGLASS_USER`, `XGLASS_PASS` — identifiants du portail X'Glass
- `VSF_LOGIN`, `VSF_PASSWORD` — identifiants du portail VSF

Ne jamais afficher, logger ou recopier le contenu de ce fichier. En production (exécution via Odoo), ces mêmes identifiants sont configurés en tant que `ir.config_parameter` — voir [`docs/technique/configuration.md`](docs/technique/configuration.md) et [`push_credentials.py`](push_credentials.py) pour les pousser automatiquement depuis ce même `.env`. La cible Odoo du script est toutefois résolue exclusivement par le profil sélectionné dans `.paradigme.yaml`, avec les secrets Odoo dans `~/.paradigme/.env` ; ne pas réintroduire de `ODOO_*` dans un `.env` du dépôt.

Toute connexion à l'instance Odoo (XML-RPC **et** session navigateur pour les vérifications via `chrome-devtools`) passe par le profil sélectionné par la skill `paradigme-mcp-local` (`.paradigme.yaml` → `rpbm-preprod`, secrets `RPBM_USERNAME`/`RPBM_PASSWORD` dans `~/.paradigme/.env`). Aucun identifiant parallèle dans `.env` du module : les anciennes clés `RPBM_DEV_WEB_*` sont obsolètes. Ne jamais afficher ces identifiants.
