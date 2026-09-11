# Rapport d'audit — `rpbm-preprod` — `2026-08-07`

Statut : `DRAFT` — implémentation et recette exécutées ; validation humaine finale des données persistantes attendue.

Ce rapport est le relevé de l'instance reconstruite. Les documents de recette sont volontairement conservés dans Odoo pour inspection humaine.

## 1. Cible et références

| Champ | Valeur |
|---|---|
| Profil | `rpbm-preprod` |
| URL | `https://rpbm-pre-prod.odoo.com/` |
| Architecture | Architecture 1 |
| Date | `2026-08-07` |
| Opérateur | Codex ; poursuite autorisée après validation humaine du catalogue |
| Module | `rpbm_agent`, `ir.module.module` ID `1551`, état `installed`, version `17.0.260730.6` |
| Procédure | [procédure commune](../procedure-audit-implementation.md) |
| Registre | [registre architecture 1](../architecture-1-test-registry.md) |
| Matrice | [matrice de conformité](../architecture-1-compliance-matrix.md) |

Le profil et l'URL ont été contrôlés avant chaque phase d'écriture. Aucun secret n'est présent dans ce rapport.

## 2. Relevé initial et migration du catalogue

La base reconstruite contenait déjà l'entrepôt `RPBM` et des données Odoo natives. La migration du catalogue a été réalisée par lots, relue après écriture, puis rejouée sans création supplémentaire.

| Objet | Résultat observé |
|---|---:|
| Articles importables | 3 229 |
| Articles stockables avec `x_studio_eurocode` valide | 3 229 / 3 229 |
| Articles avec code interne après migration, base comprise | 3 334 |
| Tarifs fournisseurs attendus | 3 137 |
| Tarifs fournisseurs présents, base comprise | 3 202 |
| Fournisseur VSF réutilisé | `res.partner` ID `5708` |
| Catégories métier racines | IDs `15` à `22` |
| Sous-catégories `Autres` | IDs `23` à `29` |
| Coûts RV chargés | 3 188 attendus selon l'auto-contrôle local |

Le module `rpbm_agent` est donc requis pour la migration et installé avant la configuration stock. Il n'a pas été réinstallé pendant la recette.

### État stock avant préparation de la recette

Le relevé initial des groupes de quants indiquait notamment : Galleria 36 quants / 314 unités, Genipa 17 / 195, Dépôt 1 8 / 67 avec 18 réservées et Dépôt 2 12 / 223. Les quants existants n'ont pas été supprimés ni remis à zéro par l'architecture.

## 3. Arbre et entrepôt configurés

| Objet | ID Odoo | État / paramètre |
|---|---:|---|
| Entrepôt `RPBM` | `1` | actif |
| Vue `RPBM` | `11` | inchangée |
| `RPBM/Stock` | `1778` | interne, `replenish_location=true` |
| `RPBM/Stock/Dépôts` | `1779` | interne, sans réassort |
| `RPBM/Stock/Dépôts/Dépôt 1` | `14` | interne, sans réassort ; racks existants conservés |
| `RPBM/Stock/Dépôts/Dépôt 2` | `1519` | interne, sans réassort |
| `RPBM/Stock/Galleria` | `1775` | interne, sans réassort |
| `RPBM/Stock/Genipa` | `1776` | interne, sans réassort |
| `RPBM/Camion` | `1780` | frère de `Stock`, interne, sans réassort |
| `lot_stock_id` de l'entrepôt | `1778` | conforme à `RPBM/Stock` |

`A controler` n'a pas été modifié. Aucun orderpoint n'a été créé sur les comptoirs ni sur les racks d'audit (`stock.warehouse.orderpoint` : aucun résultat dans le périmètre contrôlé).

## 4. Types d'opération

Les 26 types attendus sont actifs, rattachés à l'entrepôt `RPBM` et portent des `sequence_code` uniques.

| Code | Type ID | Source → destination | Réservation | Retour |
|---|---:|---|---|---:|
| `DEP-GALL` | `15` | Dépôts `1779` → Galleria `1775` | confirmation | — |
| `DEP-GENI` | `16` | Dépôts `1779` → Genipa `1776` | confirmation | — |
| `STK-CAM` | `17` | Stock `1778` → Camion `1780` | manuelle | — |
| `GALL-D1` | `3` | Galleria `1775` → Dépôt 1 `14` | confirmation | — |
| `GALL-D2` | `18` | Galleria `1775` → Dépôt 2 `1519` | confirmation | — |
| `GENI-D1` | `19` | Genipa `1776` → Dépôt 1 `14` | confirmation | — |
| `GENI-D2` | `20` | Genipa `1776` → Dépôt 2 `1519` | confirmation | — |
| `CAM-D1` | `21` | Camion `1780` → Dépôt 1 `14` | confirmation | — |
| `CAM-D2` | `22` | Camion `1780` → Dépôt 2 `1519` | confirmation | — |
| `CAM-GALL` | `23` | Camion `1780` → Galleria `1775` | confirmation | — |
| `CAM-GENI` | `24` | Camion `1780` → Genipa `1776` | confirmation | — |
| `D1-D2` | `25` | Dépôt 1 `14` → Dépôt 2 `1519` | confirmation | — |
| `D2-D1` | `26` | Dépôt 2 `1519` → Dépôt 1 `14` | confirmation | — |
| `GALL-GENI` | `27` | Galleria `1775` → Genipa `1776` | confirmation | — |
| `GENI-GALL` | `28` | Genipa `1776` → Galleria `1775` | confirmation | — |
| `D1/IN` | `29` | Fournisseurs `8` → Dépôt 1 `14` | confirmation | `33` |
| `D2/IN` | `5` | Fournisseurs `8` → Dépôt 2 `1519` | confirmation | `34` |
| `GALL/IN` | `30` | Fournisseurs `8` → Galleria `1775` | confirmation | `35` |
| `GENI/IN` | `31` | Fournisseurs `8` → Genipa `1776` | confirmation | `36` |
| `GALL/OUT` | `1` | Galleria `1775` → Clients `9` | confirmation | — |
| `GENI/OUT` | `11` | Genipa `1776` → Clients `9` | confirmation | — |
| `CAM/OUT` | `32` | Camion `1780` → Clients `9` | manuelle | — |
| `D1/RET` | `33` | Dépôt 1 `14` → Fournisseurs `8` | confirmation | — |
| `D2/RET` | `34` | Dépôt 2 `1519` → Fournisseurs `8` | confirmation | — |
| `GALL/RET` | `35` | Galleria `1775` → Fournisseurs `8` | confirmation | — |
| `GENI/RET` | `36` | Genipa `1776` → Fournisseurs `8` | confirmation | — |

Le type natif `GALL-D1` et les types natifs Galleria, Genipa et `D2/IN` ont été réutilisés conformément à la cible. Les retours fournisseurs sont reliés aux types de réception correspondants.

## 5. Routes, règles et Buy

### Routes

| Route | ID | État | Paramétrage |
|---|---:|---|---|
| `Make To Order` | `1` | active | conservée |
| `Buy` | `6` | active | sélectionnable produit et catégorie |
| `Retrait / pose Galleria` | `10` | active | sélectionnable vente / livraison |
| `Retrait / pose Genipa` | `11` | active | sélectionnable vente / livraison |
| `Pose sur site — Camion` | `12` | active | sélectionnable vente / livraison |
| `RPBM: Livrer en 1 étape (livrer)` | `3` | archivée | anciennes règles désactivées |

La route native de livraison a été archivée afin qu'une commande sans transporteur échoue explicitement au test T7. Le type `Livraison Galleria` ID `1` reste actif, car il a été réutilisé par la route métier Galleria. Cette décision résout la tension entre « réutiliser le type Galleria » et « archiver le type natif » ; elle est conservée comme choix d'implémentation à confirmer humainement.

### Règles actives principales

| Règle | ID | Route | Type | Source → destination | Méthode |
|---|---:|---|---:|---|---|
| Galleria → Clients | `12` | `10` | `1` | `1775` → `9` | `mts_else_mto` |
| Dépôts → Galleria | `13` | `10` | `15` | `1779` → `1775` | `mts_else_mto` |
| Genipa → Clients | `14` | `11` | `11` | `1776` → `9` | `mts_else_mto` |
| Dépôts → Genipa | `15` | `11` | `16` | `1779` → `1776` | `mts_else_mto` |
| Camion → Clients | `16` | `12` | `32` | `1780` → `9` | `make_to_order` |
| Stock → Camion | `17` | `12` | `17` | `1778` → `1780` | `mts_else_mto` |
| Acheter → Stock | `6` | `6` | `5` | — → `1778` | `make_to_stock` |
| Stock → Clients (MTO) | `2` | `1` | `1` | `1778` → `9` | `make_to_order` |

La règle `Buy` est active, cible `RPBM/Stock` et utilise `D2/IN` comme type de réception. Un contrôle de présence sur les 3 229 articles importés a trouvé `route_ids` incluant `Buy` pour `3 229 / 3 229` ; aucune correction de masse n'a donc été nécessaire.

Les anciennes règles de la route native archivée sont inactives. La route native `RPBM: Correspondance` ID `4` et ses règles historiques restent hors périmètre de cette architecture ; elles sont signalées `OBSERVED`, sans modification.

## 6. Transporteurs et produits de service

| Objet | ID | Produit lié | Route | Tarif |
|---|---:|---|---:|---:|
| Produit `ARCH1-SERVICE-GALL` | `3413` | Retrait comptoir Galleria | — | 0 € |
| Produit `ARCH1-SERVICE-GENI` | `3414` | Retrait comptoir Genipa | — | 0 € |
| Produit `ARCH1-SERVICE-CAM` | `3415` | Pose sur site | — | 0 € |
| Transporteur Retrait / pose Galleria | `3` | `3413` | `10` | 0 € |
| Transporteur Retrait / pose Genipa | `4` | `3414` | `11` | 0 € |
| Transporteur Pose sur site (Camion) | `5` | `3415` | `12` | 0 € |

Le tarif camion est provisoire, conformément à l'hypothèse de l'architecture.

## 7. Jeu de test persistant

### Racks et partenaires

| Alias | ID | Parent | Quantité préparée |
|---|---:|---|---:|
| `ARCH1-AUDIT-D1` | `1781` | Dépôt 1 `14` | — |
| `ARCH1-AUDIT-D2` | `1782` | Dépôt 2 `1519` | — |
| `ARCH1-AUDIT-GALL` | `1783` | Galleria `1775` | — |
| `ARCH1-AUDIT-GENI` | `1784` | Genipa `1776` | — |
| `ARCH1-AUDIT-CAM` | `1785` | Camion `1780` | — |
| Client `ARCH1-AUDIT-2026-08-07-CLIENT` | `15343` | — | — |
| Fournisseur `ARCH1-AUDIT-2026-08-07-FOURNISSEUR` | `15344` | — | — |

### Articles et quants

| Alias | Produit | Produit ID | Quant ID | Rack ID | Quantité finale | Réservée |
|---|---|---:|---:|---:|---:|---:|
| `STOCK-GALL` | `00009221V1` — LEVE VITRE ELEC AVG C4 | `184` | `131` | `1783` | `10` | `1` |
| `STOCK-D2` | `1034902-00-P` — RR DOOR ROOF GLASS ASY, LH | `185` | `133` | `1782` | `10` | `1` |
| `STOCK-GENI-ONLY` | `1034903-00-Q` — RR DOOR ROOF GLASSY ASY, RH | `186` | `135` | `1784` | `10` | `0` |
| `STOCK-D1` | `1364076080` — CUSTODE ARG FIAT DUCATO | `187` | `137` | `1781` | `10` | `0` |
| Article absent acheté T3 | `1606972480` — FAISCEAU PROJECTEUR | `188` | — | — | 0 au démarrage | — |
| Article sans transporteur T7 | `1612401680` — PEUGEOT BOXER... | `189` | — | — | 0 au démarrage | — |

Les articles MTO dédiés portent les routes `Make To Order` et `Buy`, et disposent d'un fournisseur d'audit ID `15344` à 50 € :

| Article | Produit ID | Quant ID | Rack | Quantité |
|---|---:|---:|---:|---:|
| `ARCH1-AUDIT-MTO-1` | `3416` | — | — | 0 |
| `ARCH1-AUDIT-MTO-2` | `3417` | — | — | 0 |
| `ARCH1-AUDIT-MTO-3` | `3418` | `139` | `1782` | 2 |
| `ARCH1-AUDIT-MTO-4` | `3419` | — | — | 0 |

La préparation des quants a utilisé l'ajustement d'inventaire puis une relecture. L'appel Odoo de validation de l'ajustement a retourné une réponse non sérialisable après écriture, mais les relectures ont confirmé les quantités finales ; cet effet est classé `OBSERVED`.

## 8. Recette fonctionnelle T1 à T8

Les commandes, pickings et mouvements sont persistants. Aucun picking, réception ou livraison n'a été validé physiquement.

| Test | Données principales | Documents | Résultat observé |
|---|---|---|---|
| T1 — article présent à Galleria | produit `184`, 1 unité | `SO7574` ID `7573` ; picking `5067` | `PASS` fonctionnel : `GALL/OUT`, Galleria → client, `assigned` |
| T2 — article présent à D2 | produit `185`, 1 unité | `SO7575` ID `7574` ; pickings `5068`, `5069` | `PASS` : `DEP-GALL` assigné puis `GALL/OUT` en attente |
| T3 — absent, achat puis acheminement | produit `188`, 1 unité | `SO7576` ID `7575` ; PO `PO00003` ID `3` ; pickings `5070`, `5071`, réception `5076` | `PASS` partiel/observé : achat créé, PO confirmé, réception redirigée à Galleria ; aval en attente |
| T4 — présent uniquement à Genipa | produit `186`, 1 unité | `SO7577` ID `7576` ; pickings `5072`, `5073` ; PO `PO00004` ID `4` | `PASS` conforme au pool par comptoir : Genipa n'est pas consommé ; `DEP-GALL` puis achat sont déclenchés |
| T5 — pose sur site camion | produit `187`, 1 unité | `SO7578` ID `7577` ; pickings `5074`, `5075` | `PASS` structurel : `STK-CAM` confirmé puis `CAM/OUT` en attente |
| T6 — redirection réception | PO de T3 | PO `3` modifié de `D2/IN` vers `GALL/IN` ID `30`, puis confirmé | `OBSERVED` : réception `5076`, `RPBM/GALL/IN/00001`, `assigned`, fournisseur → Galleria |
| T7 — commande sans transporteur | produit `189`, 1 unité | `SO7579` ID `7578`, aucun picking ni PO | `PASS` de protection : confirmation refusée explicitement, commande laissée `draft` |
| T8 — transfert manuel Galleria → D1 | produit `184`, 1 unité | picking `5077`, mouvement `16149` | `PASS` de création : `GALL-D1`, brouillon, rack `1783` → `1781`, non validé |

### Détail T3

Le bon de commande client `SO7576` ID `7575` est distinct du bon fournisseur `PO00003` ID `3`. Les trois opérations logistiques sont :

1. `DEP-GALL`, picking `5070`, Dépôts → Galleria, état `waiting` ;
2. `GALL/OUT`, picking `5071`, Galleria → Client, état `waiting` ;
3. `GALL/IN`, picking `5076`, Fournisseurs → Galleria, état `assigned`, issu de `PO00003`.

Le PO `PO00003` est en état `purchase`, fournisseur métier `BLUE AUTO` ID `15321`. La redirection T6 a été effectuée avant sa confirmation et est donc visible dans l'état courant.

### Écart de séquence observé

Les pickings créés avant la correction de configuration ont reçu un préfixe `RPBM/GENI/OUT/` alors que leur type était `GALL/OUT` : IDs `5067`, `5069`, `5071`, `5073`, `5079`, `5083`, `5085`. La cause était le partage initial de la séquence Odoo ID `17` entre Galleria et Genipa. La séquence Galleria a été séparée et relue : type `GALL/OUT` ID `1`, séquence ID `86`, préfixe `RPBM/GALL/OUT/`. Les documents historiques n'ont pas été renommés ; l'écart est `WARN` et ne concerne pas les prochains documents.

## 9. Recette MTO

| Test | Données | Documents | Résultat |
|---|---|---|---|
| MTO-1 — absent, MTO + Buy, Galleria | produit `3416` | `SO7580` ID `7579`, PO `PO00005` ID `5`, pickings `5078`, `5079` | `PASS` de déclenchement : achat créé, aval Galleria en attente |
| MTO-2 — absent, MTO + Buy, camion | produit `3417` | `SO7581` ID `7580`, PO `PO00006` ID `6`, pickings `5080`, `5081` | `PASS` de déclenchement : achat créé, chaîne camion en attente |
| MTO-3 — stock disponible en dépôt | produit `3418`, quant `139` à D2, quantité 2 | `SO7582` ID `7581`, pickings `5082`, `5083`, aucun PO | `PASS` observé : stock D2 utilisé, `DEP-GALL` assigné, aucun achat déclenché |
| MTO-4 — traçabilité complète | produit `3419` | `SO7583` ID `7582`, PO `PO00007` ID `7`, réception `5086`, aval `5084`, `5085` | `PASS` de traçabilité : PO confirmé, réception `D2/IN` assignée, mouvements aval en attente |

Les PO `5` et `6` sont restés en brouillon pour observation. Le PO `7` est confirmé mais sa réception `5086` n'est pas validée. Aucun mouvement MTO n'est physiquement terminé.

## 10. État final et conservation

| Domaine | État final |
|---|---|
| Racks d'audit | 5 créés, actifs, internes, sans réassort |
| Quants préparés | +10 sur chacun des quatre cas stock ; +2 pour MTO-3 |
| Réservations | 1 sur `STOCK-GALL`, 1 sur `STOCK-D2`, 1 sur MTO-3, liées aux pickings assignés |
| Commandes client | T1–T5 et MTO en `sale` ; T7 en `draft` |
| Bons fournisseurs | `PO00003` et `PO00007` en `purchase` ; `PO00004`, `PO00005`, `PO00006` en `draft` |
| Pickings | conservés dans les états `draft`, `confirmed`, `waiting` ou `assigned` selon le scénario |
| Suppression / annulation | aucune suppression ni annulation de données de recette |
| Validation physique | aucune réception, livraison ou transfert de recette validé |

Les quantités initiales n'ont pas été restaurées : le delta du jeu de test est volontairement persistant conformément à la procédure de préproduction. Les réservations persistantes peuvent influencer les essais humains suivants et doivent être prises en compte.

## 11. Verdict par domaine

| Domaine | Verdict | Commentaire |
|---|---|---|
| Sécurité de la cible | `PASS` | Profil et URL contrôlés avant écritures ; aucun secret documenté |
| Structure | `PASS` | Arbre, `lot_stock_id`, réassort et 26 types relus |
| Routes et règles | `PASS` avec `WARN` | Routes et 6 règles actives conformes ; conflit documenté sur type Galleria / route native |
| Articles et Buy | `PASS` | 3 229 articles importés et équipés de Buy |
| MTO | `PASS` avec `OBSERVED` | MTO-1 à MTO-4 exécutés ; comportement MTO-3 sans achat observé |
| Dépôt → comptoir | `PASS` | Flux Galleria et D2 vérifiés ; T4 confirme l'isolation du stock Genipa |
| Dépôt → camion | `PASS` structurel | T5 et MTO-2 ont produit la chaîne camion attendue |
| Conservation / traçabilité | `PASS` | Documents persistants, aucune validation physique ; T3 et MTO-4 traçables |
| Mise en stock / putaway dédié | `NOT_RUN` | Aucun scénario de règle de mise en stock dédié n'a été exécuté |
| Tests complémentaires | `NOT_RUN` | Retours, casse, rééquilibrages, commandes mixtes et changement de transporteur à planifier |

## 12. Écarts connus et contrôles non réalisés

- La validation humaine visuelle des articles, racks, quants et documents reste à effectuer dans Odoo.
- Les anciens pickings Galleria portent un préfixe de séquence Genipa ; ils sont conservés pour audit et ne doivent pas être renommés sans décision métier.
- T4 confirme que la route Galleria n'atteint pas le stock frère Genipa. Si une commande doit être servie par Genipa, le transporteur Genipa ou une route explicite Genipa doit être choisi avant confirmation.
- La route `RPBM: Correspondance` ID `4` et ses règles historiques n'ont pas été refactorisées.
- Les règles de putaway dédiées et les scénarios complémentaires ne sont pas exécutés.
- Aucun test n'a validé physiquement une réception, une livraison ou un transfert.

## 13. Validation humaine attendue

L'opérateur doit vérifier dans Odoo :

1. les cinq racks et les cinq quants de recette ;
2. les états et emplacements des pickings T1–T8 et MTO-1 à MTO-4 ;
3. le PO `PO00003` et sa réception Galleria `5076` ;
4. l'échec explicite de T7 et l'absence de picking associé ;
5. les documents non validés physiquement et l'impact des réservations persistantes.

Après cette revue, renseigner la décision, l'opérateur et les éventuelles corrections métier dans ce rapport sans supprimer les données de recette.
