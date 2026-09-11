# Registre du jeu de test — architecture 1

Ce document définit les critères reproductibles. Les IDs et quantités propres à une exécution sont
reportés dans [le rapport de run](runs/_template.md), jamais déduits d'un autre environnement.

## Règles communes

- Préfixe : `ARCH1-AUDIT-YYYYMMDD-<scenario>`.
- Les articles métier sont sélectionnés par critères et leurs IDs réels sont enregistrés.
- Les produits MTO sont dédiés et préfixés `ARCH1-AUDIT-MTO-`.
- Les racks d'audit sont persistants, idempotents et sans `replenish_location`.
- Les mouvements et données ne sont ni supprimés ni annulés.
- Les quantités préparées sont volontaires et documentées comme deltas.

## Racks

| Code | Parent | Usage de test |
|---|---|---|
| `ARCH1-AUDIT-D1` | D1 | stock dépôt 1, MTO avec stock |
| `ARCH1-AUDIT-D2` | D2 | stock dépôt 2, T2 |
| `ARCH1-AUDIT-GALL` | Galleria | T1 et contrôle de réservation |
| `ARCH1-AUDIT-GENI` | Genipa | T4 |
| `ARCH1-AUDIT-CAM` | Camion | T5 et retours camion |

## Articles stockables

| Alias | Critères de sélection | Tests |
|---|---|---|
| `STOCK-GALL` | stock positif à Galleria, stockable, unité simple | T1 |
| `STOCK-D2` | stock positif à D2, stockable, quantité suffisante | T2 |
| `STOCK-ABSENT` | article stockable, fournisseur actif, aucun quant utile | T3 |
| `STOCK-GENI-ONLY` | stock positif à Genipa, absent de Galleria | T4 |
| `STOCK-D1` | stock positif à D1 | T5, MTO-3 |
| `STOCK-MTO-ABSENT` | produit dédié, MTO + Buy, sans quant | MTO-1, MTO-2 |
| `STOCK-MTO-DISPONIBLE` | produit dédié, MTO + Buy, quant à D1 ou D2 | MTO-3 |

Pour chaque alias, enregistrer : ID produit, `default_code`, nom, catégorie, fournisseur, unité,
quantité initiale, quantité préparée, emplacement et réservation.

## Partenaires et documents

Créer ou réutiliser de façon idempotente :

- un client `ARCH1-AUDIT-CLIENT-<date>` ;
- un fournisseur de test `ARCH1-AUDIT-FOURNISSEUR-<date>` si aucun fournisseur réel ne convient ;
- un entrepôt et une société existants, jamais de doublon organisationnel.

Les commandes, demandes de prix et pickings portent le préfixe du scénario et restent visibles.

## Préparation des quants

Le registre d'exécution doit contenir ce tableau :

| Alias | Produit ID | Quant ID | Emplacement ID | Avant | Préparé | Réservé | Delta attendu |
|---|---:|---:|---:|---:|---:|---:|---:|
| `STOCK-GALL` | à remplir | à remplir | à remplir | à remplir | à remplir | à remplir | à remplir |
| `STOCK-D2` | à remplir | à remplir | à remplir | à remplir | à remplir | à remplir | à remplir |
| `STOCK-GENI-ONLY` | à remplir | à remplir | à remplir | à remplir | à remplir | à remplir | à remplir |
| `STOCK-D1` | à remplir | à remplir | à remplir | à remplir | à remplir | à remplir | à remplir |
| `STOCK-MTO-ABSENT` | à remplir | aucun | aucun | 0 | 0 | 0 | 0 |

## Choix opérateur

Un article candidat est rejeté si son unité, son suivi par lot/série, son fournisseur ou ses
réservations existantes rendent le résultat ambigu. Le motif du rejet est écrit dans le rapport.
