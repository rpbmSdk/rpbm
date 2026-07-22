# RPBM Agent

Outil de récupération des données des portails **X'Glass** et **VSF** pour intégration dans le processus de vente (véhicule, pièces, articles) directement depuis Odoo.

## Prérequis rapides

1. Créer 4 paramètres système (`Réglages > Technique > Paramètres > Paramètres système`) :
   - `XGLASS_USER`, `XGLASS_PASS` — identifiants du portail X'Glass
   - `VSF_LOGIN`, `VSF_PASSWORD` — identifiants du portail VSF
2. Créer les champs Studio requis sur `fleet.vehicle`, `crm.lead` et `sale.order`.
3. Placer le widget `<widget name="rpbm_agent_widget" />` sur les vues formulaire concernées.

Détail complet de ces prérequis : [`docs/technique/configuration.md`](docs/technique/configuration.md).

## Documentation

Toute la documentation détaillée (fonctionnelle, technique, état des lieux) est dans [`docs/`](docs/README.md).

- [Parcours utilisateur](docs/fonctionnel/parcours-utilisateur.md) — comment utiliser le widget au quotidien
- [Architecture](docs/technique/architecture.md) — vue d'ensemble technique et diagrammes
- [Backend](docs/technique/backend.md) — controllers, intégration X'Glass/VSF
- [Frontend](docs/technique/frontend.md) — composants OWL
- [Configuration](docs/technique/configuration.md) — prérequis d'installation détaillés
- [État des lieux](docs/etat-des-lieux.md) — fonctionnalités, cohérence, pistes d'optimisation
