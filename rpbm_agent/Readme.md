# RPBM Agent

Outil de récupération des données des portails **X'Glass** et **VSF** pour intégration dans le processus de vente (véhicule, pièces, articles) directement depuis Odoo.

## Prérequis rapides

1. Installer le module : ses champs natifs `rpbm_*` sont créés par l'ORM et le widget est placé par les vues versionnées (`views/*.xml`) ; sur une base existante, la migration `17.0.260921.1` remplit les natifs depuis les champs Studio historiques, qui restent alimentés en double.
2. Renseigner les identifiants portails dans `Réglages > Paramètres généraux > Intégrations > Accès catalogues X'Glass / VSF` (`XGLASS_USER`, `XGLASS_PASS`, `VSF_LOGIN`, `VSF_PASSWORD`), ou les pousser avec [`push_credentials.py`](push_credentials.py).
3. Vérifier les paramètres optionnels `rpbm_agent.vsf_partner_id`, `rpbm_agent.vsf_discount`, `rpbm_agent.labor_product_t1/t2/t3` (défauts calés sur `rpbm-preprod`).
4. Droits : le module ne crée aucun groupe. Les vendeurs lisent Fleet et sont utilisateurs Stock, et les acheteurs reçoivent les groupes Achats et Inventaire par la migration `17.0.260928.3` (détail : [`docs/technique/configuration.md#droits-et-rôles`](docs/technique/configuration.md#droits-et-rôles)).

Détail complet : [`docs/technique/configuration.md`](docs/technique/configuration.md).

## Documentation

Toute la documentation détaillée (fonctionnelle, technique, état des lieux) est dans [`docs/`](docs/README.md).

- [Parcours utilisateur](docs/fonctionnel/parcours-utilisateur.md) — comment utiliser le widget au quotidien
- [Architecture](docs/technique/architecture.md) — vue d'ensemble technique et diagrammes
- [Backend](docs/technique/backend.md) — controllers, intégration X'Glass/VSF
- [Frontend](docs/technique/frontend.md) — composants OWL
- [Configuration](docs/technique/configuration.md) — prérequis d'installation détaillés, droits et rôles, migrations
- [Tests](docs/technique/tests.md) — tests Odoo, portails sans réseau et widget
- [Interaction avec `rpbm_pricing`](docs/technique/rpbm-pricing.md) — règle 8 gardée par le module optionnel
- [Historique des versions](docs/technique/versions.md) — de `17.0.260921.1` à `17.0.261013.1`
- [Jeu de test](docs/jeu-de-test.md) — plaques, bases Eurocode et scénarios de recette
- [État des lieux](docs/etat-des-lieux.md) — fonctionnalités, cohérence, pistes d'optimisation
- [Feuille de route](docs/roadmap.md) — lots L0 à L3
- [Validations métier](docs/validations-metier.md) — décisions attendues du client
