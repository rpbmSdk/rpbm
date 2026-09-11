# Procédure d'audit réplicable des implémentations stock

Statut : procédure opérationnelle à appliquer en préproduction.

Cette procédure vérifie une implémentation stock Odoo par comparaison entre une cible d'architecture,
l'état observé de l'instance et une recette fonctionnelle persistante. Elle est conçue pour que les
opérateurs puissent consulter les articles, quants, commandes et mouvements après l'audit.

Références : [invariants communs](../00-invariants.md), [architecture 1](../01-architecture-1-zones.md),
[registre architecture 1](architecture-1-test-registry.md) et [matrice architecture 1](architecture-1-compliance-matrix.md).

## 1. Principes et statuts

L'audit distingue systématiquement :

- `OBSERVED` : fait lu ou comportement exécuté sur l'instance ;
- `PASS` : conforme à la cible ;
- `FAIL` : écart bloquant ;
- `WARN` : écart connu ou toléré ;
- `NOT_RUN` : contrôle non exécuté ;
- `NOT_APPLICABLE` : contrôle hors périmètre.

Une hypothèse ou une interprétation ne doit jamais être présentée comme un fait observé.

L'audit comporte deux modes :

- **structurel** : lecture seule ;
- **fonctionnel** : écritures limitées aux données de recette en préproduction.

Les mouvements, commandes, quants et partenaires de recette ne sont pas supprimés ni annulés.

## 2. Sécurisation avant accès

Avant tout appel Odoo :

1. lire `.paradigme.yaml` et identifier le profil demandé ;
2. charger exclusivement `paradigme-mcp-local` ;
3. confirmer l'URL de l'instance et son statut préproduction ;
4. vérifier que l'architecture auditée et la date d'exécution sont consignées ;
5. refuser l'exécution si le profil ou l'URL sont inattendus ;
6. ne jamais copier de secret dans le dépôt ou le rapport.

La vérification de cible est bloquante. Une erreur d'accès ou de profil interrompt l'audit avant
toute écriture.

## 3. Relevé initial en lecture seule

Capturer et conserver dans le rapport :

- `stock.warehouse` et paramètres de réassort ;
- arbre complet de `stock.location` ;
- `stock.picking.type`, séquences et emplacements par défaut ;
- `stock.route` et `stock.rule` ;
- `delivery.carrier` et produits de service ;
- produits stockables candidats et routes `Buy`/`MTO` ;
- fournisseurs et informations fournisseur ;
- nombre de quants, quantités et réservations par emplacement et par produit.

Le relevé initial constitue la référence pour calculer les deltas attendus après préparation des
données de test. Il ne doit pas être utilisé pour restaurer automatiquement le stock.

## 4. Préparation persistante de la recette

Utiliser le [registre de test](architecture-1-test-registry.md). Pour chaque exécution, attribuer le
préfixe :

`ARCH1-AUDIT-YYYYMMDD-<scenario>`

Créer ou réutiliser de manière idempotente les racks d'audit suivants, sans les marquer comme
emplacements de réassort :

| Code | Parent attendu |
|---|---|
| `ARCH1-AUDIT-D1` | `RPBM/Stock/Dépôts/Dépôt 1` |
| `ARCH1-AUDIT-D2` | `RPBM/Stock/Dépôts/Dépôt 2` |
| `ARCH1-AUDIT-GALL` | `RPBM/Stock/Galleria` |
| `ARCH1-AUDIT-GENI` | `RPBM/Stock/Genipa` |
| `ARCH1-AUDIT-CAM` | `RPBM/Camion` |

Sélectionner dynamiquement les articles selon leur disponibilité, puis enregistrer dans le registre
les IDs réels, références, catégories, fournisseurs, racks et quantités. Les produits dédiés MTO
portent le préfixe `ARCH1-AUDIT-MTO-`.

## 5. Préparation des quantités

Préparer par ajustement d'inventaire ou mécanisme Odoo équivalent :

- un article stocké à D1 ;
- un article stocké à D2 ;
- un article stocké à Galleria ;
- un article stocké uniquement à Genipa ;
- un article absent des emplacements de stock ;
- un article MTO sans stock local ;
- un article MTO avec stock disponible dans un dépôt.

Après chaque écriture :

1. relire le quant ;
2. vérifier produit, emplacement, quantité, unité et réservation ;
3. enregistrer l'ID du quant et le delta attendu ;
4. arrêter la phase si la relecture ne correspond pas.

L'état final peut différer de l'état initial uniquement par les quantités et réservations prévues
dans le registre et par les mouvements ouverts de recette.

## 6. Audit structurel

Comparer l'instance à la matrice architecture 1 :

- arbre et `lot_stock_id` ;
- `replenish_location` et emplacement `A controler` ;
- 26 types d'opération attendus ;
- unicité des séquences Galleria/Genipa ;
- sources, destinations et méthodes de réservation ;
- liens de retour fournisseur ;
- trois routes et six règles métier ;
- règle `Buy` vers `RPBM/Stock` ;
- archivage des routes et règles natives incompatibles ;
- trois transporteurs et produits de service.

Le référentiel général contient 31 types, tandis que l'architecture 1 regroupe certains flux
automatiques. Cette réduction est un choix d'architecture et doit être contrôlée explicitement.

## 7. Contrôle des articles et de Buy

Contrôler un échantillon d'au moins 50 articles importés portant `x_studio_eurocode`, puis relever :

- route `Buy` présente ou absente ;
- route `MTO` présente ou absente ;
- fournisseur utilisable ;
- catégorie et type d'article ;
- emplacement et quantité disponibles.

Si une correction est autorisée dans le périmètre de l'audit, l'ajout de `Buy` doit être fait par
lot, relu, puis comptabilisé séparément comme correction appliquée.

## 8. Recette T1 à T8

Pour chaque test, consigner article, quantité, rack, commande, lignes, pickings, bon fournisseur,
types, emplacements, états, réservations, résultat attendu et résultat observé.

| Test | Cas | Contrôle principal |
|---|---|---|
| T1 | article à Galleria | `GALL/OUT` |
| T2 | article à D2 | `DEP-GALL` puis `GALL/OUT` |
| T3 | article absent | achat, réception, transfert et sortie |
| T4 | article à Genipa uniquement | absence de prélèvement Genipa pour Galleria |
| T5 | pose sur site | `STK-CAM` puis `CAM/OUT` |
| T6 | réception fournisseur vers Galleria | comportement réel et non documenté |
| T7 | vente sans transporteur | route ou erreur réellement observée |
| T8 | transfert manuel Galleria → D1 | type `GALL-D1` et emplacements |

Les documents sont laissés dans leur état de recette pour inspection humaine.

## 9. Recette MTO

Utiliser des produits dédiés avec `MTO + Buy` et les inscrire dans le registre.

- `MTO-1` : article sans stock, vente Galleria, création du besoin fournisseur ;
- `MTO-2` : article sans stock, pose sur site, chaîne achat/camion ;
- `MTO-3` : article MTO avec stock en dépôt, vérification du déclenchement d'achat ;
- `MTO-4` : traçabilité commande client → demande de prix → réception → mouvements aval.

Confirmer uniquement les documents nécessaires à l'observation. Ne jamais valider physiquement une
réception, un transfert ou une livraison de recette.

## 10. Suite complémentaire

Prévoir et afficher même lorsqu'ils ne sont pas joués : retours comptoir, retours camion, casse,
rééquilibrages, retours fournisseur, commandes mixtes, changement de transporteur après confirmation
et routes explicites par ligne.

## 11. Conservation et rapport

Conserver les produits, partenaires, racks, quants, commandes, bons fournisseurs, pickings,
mouvements, réservations et erreurs de recette. Ne lancer aucun nettoyage automatique.

Le rapport d'exécution doit reprendre le [modèle daté](runs/_template.md) et contenir :

1. cible, profil, architecture, opérateur et date ;
2. documents de référence ;
3. registre des données et IDs Odoo ;
4. relevé initial ;
5. conformité structurelle ;
6. résultats T1-T8 et MTO ;
7. tests complémentaires ;
8. état final et deltas de quantités ;
9. documents persistants et états ;
10. écarts, contrôles non réalisés et recommandations.

Le verdict est séparé pour la sécurité, la structure, Buy, MTO, les flux dépôt-comptoir, les flux
dépôt-camion et la traçabilité des données.
