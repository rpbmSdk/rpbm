# Matrice de conformité — architecture 1

Cette matrice compare la cible documentaire et les valeurs lues sur une instance. Les IDs sont
propres à chaque instance et doivent être ajoutés au rapport d'exécution.

Références : [architecture 1](../01-architecture-1-zones.md) et [invariants](../00-invariants.md).

## Emplacements

| Code | Chemin attendu | Usage | Réassort |
|---|---|---|---|
| `STOCK` | `RPBM/Stock` | internal | oui |
| `DEPOTS` | `RPBM/Stock/Dépôts` | internal | non |
| `D1` | `RPBM/Stock/Dépôts/Dépôt 1` | internal | non |
| `D2` | `RPBM/Stock/Dépôts/Dépôt 2` | internal | non |
| `GALL` | `RPBM/Stock/Galleria` | internal | non |
| `GENI` | `RPBM/Stock/Genipa` | internal | non |
| `CAM` | `RPBM/Camion` | internal | non |

`A controler` doit rester inchangé. `CAM` est frère de `STOCK`, pas son enfant.

## Types d'opération

| Code | Type | Code Odoo | Source | Destination |
|---|---|---|---|---|
| `DEP-GENI` | Dépôts → Genipa | internal | DEPOTS | GENI |
| `STK-CAM` | Chargement camion | internal | STOCK | CAM |
| `GALL-D1` | Galleria → D1 | internal | GALL | D1 |
| `GALL-D2` | Galleria → D2 | internal | GALL | D2 |
| `GENI-D1` | Genipa → D1 | internal | GENI | D1 |
| `GENI-D2` | Genipa → D2 | internal | GENI | D2 |
| `CAM-D1` | Camion → D1 | internal | CAM | D1 |
| `CAM-D2` | Camion → D2 | internal | CAM | D2 |
| `CAM-GALL` | Camion → Galleria | internal | CAM | GALL |
| `CAM-GENI` | Camion → Genipa | internal | CAM | GENI |
| `D1-D2` | D1 → D2 | internal | D1 | D2 |
| `D2-D1` | D2 → D1 | internal | D2 | D1 |
| `GALL-GENI` | Galleria → Genipa | internal | GALL | GENI |
| `GENI-GALL` | Genipa → Galleria | internal | GENI | GALL |
| `D1/IN` | Réception D1 | incoming | Vendors | D1 |
| `D2/IN` | Réception D2 | incoming | Vendors | D2 |
| `GALL/IN` | Réception Galleria | incoming | Vendors | GALL |
| `GENI/IN` | Réception Genipa | incoming | Vendors | GENI |
| `GALL/OUT` | Livraison Galleria | outgoing | GALL | Customers |
| `GENI/OUT` | Livraison Genipa | outgoing | GENI | Customers |
| `CAM/OUT` | Pose sur site | outgoing | CAM | Customers |
| `D1/RET` | Retour fournisseur D1 | outgoing | D1 | Vendors |
| `D2/RET` | Retour fournisseur D2 | outgoing | D2 | Vendors |
| `GALL/RET` | Retour fournisseur Galleria | outgoing | GALL | Vendors |
| `GENI/RET` | Retour fournisseur Genipa | outgoing | GENI | Vendors |

Tous les types utilisent `at_confirm`/`ask`, sauf `STK-CAM` et `CAM/OUT`, qui utilisent
`manual`/`always`. Les réceptions doivent pointer vers `return_picking_type_id` correspondant.

## Routes et règles

| Route | Séquence | Sélection | Règles attendues |
|---|---:|---|---|
| Retrait Galleria | 20 | vente + expédition | GALL → Clients ; DEPOTS → GALL |
| Retrait Genipa | 21 | vente + expédition | GENI → Clients ; DEPOTS → GENI |
| Pose sur site | 22 | vente + expédition | CAM → Clients ; STOCK → CAM |

La règle `Buy` doit être active, aboutir à `STOCK` et utiliser `D2/IN` comme type de réception si
ce choix est conservé sur l'instance auditée.

Les routes natives incompatibles, notamment « Livrer en 1 étape », doivent être archivées et leur
état réel doit être relevé.

## Transporteurs et services

| Transporteur | Route | Produit service | Prix de référence |
|---|---|---|---:|
| Retrait / pose Galleria | Retrait Galleria | `ARCH1-SHIP-GALL` | 0 € |
| Retrait / pose Genipa | Retrait Genipa | `ARCH1-SHIP-GENI` | 0 € |
| Pose sur site | Pose sur site | `ARCH1-SHIP-CAM` | 0 € provisoire |

## Verdict de matrice

Le rapport doit ajouter à chaque ligne : `PASS`, `FAIL`, `WARN`, `NOT_RUN` ou `NOT_APPLICABLE`,
avec ID Odoo, valeur observée, écart et preuve associée.
