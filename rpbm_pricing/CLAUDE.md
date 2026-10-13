# Directives — module rpbm_pricing

Documentation du module : [`docs/README.md`](docs/README.md). Les règles de [`../rpbm_agent/CLAUDE.md`](../rpbm_agent/CLAUDE.md)
s'appliquent ; en résumé :

- **Champs natifs `rpbm_*`**, jamais `x_`. Un nom `x_studio_*` n'apparaît que dans
  [`models/legacy_fields.py`](models/legacy_fields.py), et tout accès est gardé par `name in model._fields` : le
  module s'installe sur une base sans Studio (les tests qui en ont besoin font `skipTest`).
- **Version du manifeste** (`17.0.AAMMJJ.N`) incrémentée à chaque modification déployée.
- **Mise en place** : une fonction idempotente par mise en place, appelée par `setup()` de
  [`hooks.py`](hooks.py) (donc par `post_init_hook` à l'installation) et, pour une version qui en ajoute une
  sur une base où le module est déjà installé, par `migrations/<version>/post-setup.py` qui rappelle `setup()`.
- **Paramètres** : lus par [`models/params.py`](models/params.py), jamais d'exception sur une valeur invalide ;
  clés `rpbm_pricing.*`, valeurs de repli identiques aux données `noupdate`.
- **Logique pure** dans `lib/` (aucun import d'Odoo), testée par `tests/test_*_pure.py` avec l'en-tête
  `BaseCase` / `unittest.TestCase` ; `python3 -I rpbm_pricing/tests/run_pure.py` avant chaque commit.
- **Vues** : aucun xpath positionnel (les formulaires sont aussi modifiés par Studio).
- Commentaires et documentation en français. Vérifier tout mécanisme Odoo dans le source Odoo 17.
