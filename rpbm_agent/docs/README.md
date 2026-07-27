# Documentation — RPBM Agent

Index de la documentation du module. À maintenir à jour à chaque évolution fonctionnelle ou technique du module.

## Fonctionnel

- [`fonctionnel/parcours-utilisateur.md`](fonctionnel/parcours-utilisateur.md) — prérequis métier, parcours utilisateur détaillé (Piste/Opportunité et Ordre de Vente), diagrammes de flux.
- [`fonctionnel/workflow/README.md`](fonctionnel/workflow/README.md) — parcours utilisateur découpé en 9 étapes, chacune documentant précisément la route appelée et les champs Odoo lus/écrits.

## Technique

- [`technique/architecture.md`](technique/architecture.md) — stack, vue d'ensemble des composants, diagramme de séquence bout-en-bout.
- [`technique/backend.md`](technique/backend.md) — controllers Odoo, référence des routes, intégration X'Glass/VSF (scraping, authentification, contraintes de session).
- [`technique/frontend.md`](technique/frontend.md) — arborescence des composants OWL, gestion d'état, appels serveur.
- [`technique/configuration.md`](technique/configuration.md) — paramètres système, champs Studio (création automatique via `pre_init_hook`), dépendances Python, déploiement.
- [`technique/champs/README.md`](technique/champs/README.md) — référence complète des champs Odoo (`x_studio_*` et standards) par modèle porteur : type, related, origine (`pre_init_hook` ou Studio), champs obsolètes.

## Audit & pilotage

- [`etat-des-lieux.md`](etat-des-lieux.md) — fonctionnalités implémentées, cohérence technique et métier, optimisation UI/UX, recommandations priorisées.
- [`roadmap.md`](roadmap.md) — travaux à mener sur l'UI et le transfert vers Odoo, ordonnés par lots (L0 diagnostic → L1 transfert → L2 UI → L3 hygiène), établis sur les données réelles de l'instance.
- [`validations-metier.md`](validations-metier.md) — registre des décisions attendues du client, de leurs impacts et des réponses validées.
- [`_archive/`](_archive/README.md) — sections de doc rendues fausses par des évolutions du code, archivées pour suivi (texte erroné + motif + correction).
