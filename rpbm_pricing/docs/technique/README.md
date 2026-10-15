# Manuel technique

[RPBM Pricing](../../README.md) › [Documentation](../README.md) › Manuel technique

Manuel technique du module `rpbm_pricing` (version `17.0.261012.1`), qui s'installe au-dessus de `rpbm_agent`
(version `17.0.261013.1`). Il décrit ce que le code fait, où il le fait et pourquoi. À tenir à jour à chaque
version déployée. Tout ce qui est annoncé ici est implémenté, sauf mention « différé » ou « itération 2 ».

## Pages, dans l'ordre de lecture

1. [Vue d'ensemble](vue-ensemble.md) : place dans l'architecture, lots livrés et différés.
2. [Modèles et champs](modeles.md) : ce que le module ajoute au modèle de données.
3. [Surcharges](surcharges.md) : méthodes Odoo surchargées et raison de chacune.
4. [Garde de la règle 8](regle-8.md) : automatisation Studio « Tarif x glass », réversible.
5. [Colisage VSF](colisage.md) : modèles, reprise de l'historique, coefficient annuel.
6. [Données, paramètres et droits](parametres.md) : clés `rpbm_pricing.*`, actions serveur, groupes.
7. [Installation et déploiement](installation.md) : installer, mettre à jour, désinstaller, Odoo.sh.
8. [Tests](tests.md) : tests purs, tests sous Odoo, commande du webshell.
9. [Recette Jev](recette-jev.md) : scénarios `pricing_*` et résultats du 2026-10-13.
10. [Conventions de développement](conventions.md) : règles à suivre pour toute modification.

## Par besoin

| Je veux… | Page |
|---|---|
| comprendre pourquoi le module existe | [Vue d'ensemble](vue-ensemble.md) |
| savoir quel champ porte quoi | [Modèles et champs](modeles.md) |
| comprendre un prix de ligne de devis | [Garde de la règle 8](regle-8.md), [Surcharges](surcharges.md) |
| changer le coefficient, l'arrondi ou un seuil | [Données, paramètres et droits](parametres.md) |
| comprendre un coefficient de colisage | [Colisage VSF](colisage.md) |
| déployer ou rejouer l'installation | [Installation et déploiement](installation.md) |
| lancer les tests | [Tests](tests.md) |
| modifier le code | [Conventions de développement](conventions.md) |

Voir aussi : [Documentation du module](../README.md) · [Documentation de `rpbm_agent`](../../../rpbm_agent/docs/README.md)

---
Suivant : [Vue d'ensemble](vue-ensemble.md)
