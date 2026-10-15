# Conventions de développement

[RPBM Pricing](../../README.md) › [Documentation](../README.md) › [Manuel technique](README.md) › Conventions de développement

Source : [`CLAUDE.md`](../../CLAUDE.md) du module. Les règles de [`rpbm_agent/CLAUDE.md`](../../../rpbm_agent/CLAUDE.md)
s'appliquent aussi.

## Règles

| Sujet | Règle |
|---|---|
| Champs | natifs `rpbm_*`, jamais `x_`. Un nom `x_studio_*` n'apparaît que dans [`models/legacy_fields.py`](../../models/legacy_fields.py), et tout accès est gardé par `name in model._fields` : le module s'installe sur une base sans Studio. Les tests qui en ont besoin font `skipTest`. |
| Version | `17.0.AAMMJJ.N` dans le manifeste, incrémentée à chaque modification déployée. |
| Mise en place | une fonction idempotente par mise en place, appelée par `setup()` de [`hooks.py`](../../hooks.py) (donc par `post_init_hook` à l'installation). Pour une version qui en ajoute une sur une base où le module est déjà installé : `migrations/<version>/post-setup.py` qui rappelle `setup()`. |
| Paramètres | lus par [`models/params.py`](../../models/params.py), jamais d'exception sur une valeur invalide ; clés `rpbm_pricing.*`, valeurs de repli identiques aux données `noupdate`. |
| Logique pure | dans `lib/`, sans import d'Odoo, testée par `tests/test_*_pure.py` avec l'en-tête `BaseCase` / `unittest.TestCase`. |
| Avant chaque commit | `python3 -I rpbm_pricing/tests/run_pure.py` |
| Vues | aucun xpath positionnel : les formulaires sont aussi modifiés par Studio. |
| Langue | commentaires et documentation en français. |
| Mécanismes Odoo | vérifier dans le source Odoo 17 (`/root/git/odoo17/odoo`), pas de mémoire. |

## Pourquoi ces règles

- **Garde par `in model._fields`** : la garde de la règle 8 en est l'exemple. Elle fonctionne parce que
  l'expression de l'action teste la présence du champ, voir [Garde de la règle 8](regle-8.md#la-garde).
- **Pas d'exception sur un paramètre** : `params.py` est appelé depuis l'automatisation Studio, où une
  exception bloquerait la saisie d'une ligne de devis.
- **Un seul fichier pour les noms Studio** : lorsqu'un champ Studio disparaît ou est renommé, un seul endroit
  est à corriger.
- **Pas de xpath positionnel** : Studio réécrit les vues ; une cible déplacée casserait le formulaire.

## Avant de livrer une modification

1. Incrémenter la version du manifeste.
2. Tests purs, `py_compile` et analyse des XML ([Tests](tests.md#tests-purs)).
3. Mettre à jour cette documentation (page concernée, index [Manuel technique](README.md)), puis lancer
   `python3 -I .paradigme/scripts/check_doc_nav.py rpbm_pricing/docs` et
   `bash .paradigme/scripts/check_mermaid.sh rpbm_pricing/docs`.
4. Pousser sur `pre-prod`, ouvrir le build du commit, lancer les tests sous Odoo puis la
   [recette Jev](recette-jev.md).

Voir aussi : [Installation et déploiement](installation.md)

---
Précédent : [Recette Jev](recette-jev.md) · Retour à l'[index du manuel technique](README.md)
