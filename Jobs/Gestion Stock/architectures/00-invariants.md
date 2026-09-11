# Invariants communs aux trois architectures de stock

Date : 2026-08-06 · Objet : fixer ce qui **ne dépend pas** de l'architecture retenue, pour que les
trois documents de configuration soient comparables ligne à ligne.

Ce document est le **contrat**. Les trois documents d'architecture ne redéfinissent rien de ce qui
est ici : ils s'y réfèrent et ne décrivent que leur propre implémentation.

| Document | Contenu |
|---|---|
| **00-invariants.md** *(ce document)* | Sites, référentiel des opérations, conventions, transporteurs, invariants métier |
| [01-architecture-1-zones.md](01-architecture-1-zones.md) | 1 entrepôt, les 5 sites en zones de stockage |
| [02-architecture-2-entrepots.md](02-architecture-2-entrepots.md) | 5 entrepôts Odoo distincts |
| [03-architecture-3-hybride.md](03-architecture-3-hybride.md) | Comptoirs en entrepôts imbriqués, dépôts et camion en zones |

Arbitrage, comparaison et recommandation : [../architectures-stock.md](../architectures-stock.md).
Décisions arrêtées : [../decisions.md](../decisions.md). Questions ouvertes :
[../questions-ouvertes.md](../questions-ouvertes.md).

---

## 1. Les cinq sites

| Code | Site | Profil | Reçoit un fournisseur ? | Sert un client ? |
|---|---|---|---|---|
| `D1` | Dépôt 1 | Dépôt | oui | non |
| `D2` | Dépôt 2 | Dépôt | oui | non |
| `GALL` | Galleria | Comptoir | oui | oui |
| `GENI` | Genipa | Comptoir | oui | oui |
| `CAM` | Camion | Camion | non | oui, chez le client |

**Dépôt 1 et Dépôt 2 sont deux sites distincts**, pas une unité logistique unique : deux bâtiments,
109 et 380 racks ([D12](../decisions.md)). Toute opération les concernant est différenciée.

**Un seul camion** est modélisé. L'extension à N est décrite en
[architectures-stock.md § G](../architectures-stock.md#g--extension-à-n-camions) et ne fait pas
partie de ces documents.

---

## 2. Le référentiel des opérations

**Principe directeur** : *toute opération doit être identifiable et différenciable sans ouvrir le
document*. Chaque couple de sites **orienté** a donc son propre type d'opération, et donc sa propre
file de travail et sa propre séquence.

**Un transfert inter-sites est UN document**, émis du côté de l'origine et allant directement à la
destination. Aucun emplacement de transit, aucune réception de contrepartie.

### 2.1 Transferts inter-sites — 20 types

`code = internal` · source = l'emplacement du site d'origine · destination = celui du site de
destination.

| # | Type d'opération | `sequence_code` | Origine → Destination | Flux servis |
|---|---|---|---|---|
| 1 | Transfert Dépôt 1 → Galleria | `D1-GALL` | D1 → GALL | F1, F3 |
| 2 | Transfert Dépôt 1 → Genipa | `D1-GENI` | D1 → GENI | F1, F3 |
| 3 | Transfert Dépôt 1 → Camion | `D1-CAM` | D1 → CAM | F2 |
| 4 | Transfert Dépôt 1 → Dépôt 2 | `D1-D2` | D1 → D2 | F10 |
| 5 | Transfert Dépôt 2 → Galleria | `D2-GALL` | D2 → GALL | F1, F3 |
| 6 | Transfert Dépôt 2 → Genipa | `D2-GENI` | D2 → GENI | F1, F3 |
| 7 | Transfert Dépôt 2 → Camion | `D2-CAM` | D2 → CAM | F2 |
| 8 | Transfert Dépôt 2 → Dépôt 1 | `D2-D1` | D2 → D1 | F10 |
| 9 | Transfert Galleria → Dépôt 1 | `GALL-D1` | GALL → D1 | F6 |
| 10 | Transfert Galleria → Dépôt 2 | `GALL-D2` | GALL → D2 | F6 |
| 11 | Transfert Galleria → Camion | `GALL-CAM` | GALL → CAM | F5 |
| 12 | Transfert Galleria → Genipa | `GALL-GENI` | GALL → GENI | F10 |
| 13 | Transfert Genipa → Dépôt 1 | `GENI-D1` | GENI → D1 | F6 |
| 14 | Transfert Genipa → Dépôt 2 | `GENI-D2` | GENI → D2 | F6 |
| 15 | Transfert Genipa → Camion | `GENI-CAM` | GENI → CAM | F5 |
| 16 | Transfert Genipa → Galleria | `GENI-GALL` | GENI → GALL | F10 |
| 17 | Retour Camion → Dépôt 1 | `CAM-D1` | CAM → D1 | F7 |
| 18 | Retour Camion → Dépôt 2 | `CAM-D2` | CAM → D2 | F7 |
| 19 | Retour Camion → Galleria | `CAM-GALL` | CAM → GALL | F7 |
| 20 | Retour Camion → Genipa | `CAM-GENI` | CAM → GENI | F7 |

### 2.2 Réceptions fournisseur — 4 types

`code = incoming` · source = `Partners/Vendors` · destination = l'emplacement du site.

| Type d'opération | `sequence_code` | Destination | Flux |
|---|---|---|---|
| Réception Dépôt 1 | `D1/IN` | D1 | F3 |
| Réception Dépôt 2 | `D2/IN` | D2 | F3 |
| Réception Galleria | `GALL/IN` | GALL | F4, F5 |
| Réception Genipa | `GENI/IN` | GENI | F4, F5 |

Le camion ne reçoit pas de fournisseur.

**C'est le type d'opération qui porte la destination réelle d'une réception** — champ « Livrer à »
de la demande de prix, `picking_type_id.default_location_dest_id`
(`purchase_stock/models/purchase_order.py:204-208`). L'acheteur bascule ce champ **avant
confirmation** pour faire livrer au comptoir (F4).

### 2.3 Livraisons client — 3 types

`code = outgoing` · destination = `Partners/Customers`.

| Type d'opération | `sequence_code` | Source | Flux |
|---|---|---|---|
| Livraison Galleria | `GALL/OUT` | GALL | F1, F3, F4, F9 |
| Livraison Genipa | `GENI/OUT` | GENI | F1, F3, F4, F9 |
| Pose sur site | `CAM/OUT` | CAM | F2, F5 |

Les dépôts ne servent pas de client : aucun type sortant client.

### 2.4 Retours fournisseur — 4 types

`code = outgoing` · destination = `Partners/Vendors`. Rattachés par
`return_picking_type_id` sur le type de réception correspondant : le wizard de retour l'utilise, et
retombe sur le type d'origine s'il est vide (`stock/wizard/stock_picking_return.py:116`).

| Type d'opération | `sequence_code` | `return_picking_type_id` de | Flux |
|---|---|---|---|
| Retour fournisseur Dépôt 1 | `D1/RET` | Réception Dépôt 1 | F11 |
| Retour fournisseur Dépôt 2 | `D2/RET` | Réception Dépôt 2 | F11 |
| Retour fournisseur Galleria | `GALL/RET` | Réception Galleria | F11 |
| Retour fournisseur Genipa | `GENI/RET` | Réception Genipa | F11 |

### 2.4 bis — Limite Odoo sur les transferts automatiques *(2026-08-06)*

**Le référentiel ci-dessus n'est pas intégralement atteignable pour les transferts déclenchés
automatiquement.** Les trois documents d'architecture ont buté indépendamment sur la même
contrainte ; elle est vérifiée :

- `stock.rule.picking_type_id` est **`required=True`** (`stock/models/stock_rule.py:75-78`) : une
  règle porte **un seul** type d'opération ;
- `_search_rule` retient **une seule règle** par route et destination — `limit=1`
  (`stock/models/stock_rule.py:536-549`), et `_search_rule_for_warehouses` ne garde qu'une règle
  par `(location_dest_id, warehouse_id, route_id)` (`:516-524`) ;
- le type est figé à la création du mouvement (`:352`) et n'est jamais réécrit à la réservation.

Conséquence : un transfert **tiré par une commande client** vers Galleria ne peut porter qu'**un
seul** type d'opération. Il est donc impossible de produire `D1-GALL` ou `D2-GALL` selon le rack
réellement prélevé. Les couples concernés sont ceux que la vente déclenche :
`D1-GALL`, `D2-GALL`, `D1-GENI`, `D2-GENI`, `D1-CAM`, `D2-CAM`, `GALL-CAM`, `GENI-CAM`.

**Ce qui n'est pas affecté** : tous les transferts **créés à la main** — F6 (comptoir → dépôt),
F7 (retours camion), F10 (rééquilibrages). L'utilisateur y choisit le type, donc les couples
orientés `GALL-D1`, `GALL-D2`, `CAM-GALL`, `D1-D2`… restent parfaitement distinguables.

**Arbitrage à rendre par le projet** — non tranché dans ce document :

| Option | Effet |
|---|---|
| **Regrouper** les couples tirés : `DEP-GALL`, `DEP-GENI`, `DEP-CAM`, `CPT-CAM` | 8 types → 4. Le dépôt d'origine reste lisible **à la ligne** du document (emplacement source = le rack) |
| **Une route par dépôt** | conserve les 8 types, mais impose au vendeur de choisir le dépôt à la vente — il ne le sait pas |
| **Rendre ces transferts manuels** | conserve les 8 types, mais supprime l'automatisme depuis la commande |

Chaque document d'architecture indique l'option qu'il a retenue pour ses tableaux.

### 2.5 Récapitulatif

**31 types d'opération** : 20 transferts + 4 réceptions + 3 livraisons + 4 retours fournisseur.
La casse (F8) passe par `stock.scrap` et ne consomme aucun type.

C'est le prix du principe directeur : chaque file de travail est un type, donc lisible sans filtre.
Chaque architecture indique **à quel entrepôt** chacun de ces types est rattaché — c'est là qu'elles
diffèrent, pas sur la liste.

---

## 3. Conventions transverses

### 3.1 Séquences

Le préfixe est reconstruit par Odoo en `<code entrepôt>/<sequence_code>/`
(`stock/models/stock_picking.py:183-190`). Un `sequence_code` renseigné suffit ; ne jamais écrire
le préfixe à la main.

### 3.2 Paramètres par profil de site

| Paramètre | Dépôt | Comptoir | Camion | Motif |
|---|---|---|---|---|
| `reservation_method` | `at_confirm` | `at_confirm` | **`manual`** | on ne réserve le camion qu'au chargement effectif |
| `create_backorder` | `ask` | `ask` | **`always`** | un article chargé et non posé doit rester dû |

### 3.3 Emplacement de rebut

`CASSE`, `usage = inventory`, `scrap_location = True`, sous `Virtual Locations`
([D14](../decisions.md)). Origine de la casse tracée par l'emplacement source du `stock.scrap`.

### 3.4 Valorisation

`property_cost_method = standard`, `property_valuation = manual_periodic` sur les catégories
([D8](../decisions.md)). **Aucune écriture comptable n'est générée**, quelle que soit
l'architecture — vérifié dans le code et sur l'instance
([architectures-stock.md § F.1](../architectures-stock.md#f1-le-comptable-est-neutre-il-ne-doit-pas-entrer-dans-larbitrage)).

### 3.5 Racks

489 emplacements, `R101`–`R336` → Dépôt 1, `R401`–`R937` / `J…` / `T…` → Dépôt 2
([D12](../decisions.md)). Leur rattachement ne change pas d'une architecture à l'autre ; seul leur
**parent** change.

---

## 4. Sélection de la route par transporteur

**Décision retenue** : la route est choisie par le **mode d'expédition**
(`delivery.carrier`), que le vendeur renseigne sur la commande.

### 4.1 Les trois transporteurs

| Mode d'expédition | Route rattachée | Effet |
|---|---|---|
| **Retrait / pose Galleria** | `Retrait Galleria` | sert depuis Galleria, à défaut depuis un dépôt |
| **Retrait / pose Genipa** | `Retrait Genipa` | idem avec Genipa |
| **Pose sur site (Camion)** | `Pose sur site — Camion` | charge le camion puis pose chez le client |

Toutes les routes portent `shipping_selectable = True`.

### 4.2 Mécanique vérifiée

- `delivery.carrier.route_ids`, domaine `[('shipping_selectable','=',True)]`
  (`stock_delivery/models/delivery_carrier.py:27-29`) ;
- la route du transporteur est injectée **en repli** de celle de la ligne
  (`stock_delivery/models/sale_order.py:51-55`) — précédence :
  `route de ligne > route du transporteur > emballage > produit/catégorie > entrepôt` ;
- **la route reste collante en remontant la chaîne** : `_get_stock_move_values` recopie `route_ids`
  sur le mouvement créé (`stock/models/stock_rule.py:352`) et
  `stock_move._prepare_procurement_values` le réémet (`stock/models/stock_move.py:1487`) ;
- **et elle se relâche pour l'achat** : `_search_rule` est une cascade avec `if not res` à chaque
  étage (`stock/models/stock_rule.py:536-549`). Quand `mts_else_mto` ne trouve pas de stock et doit
  remonter chez le fournisseur, la route du transporteur n'a pas de règle pour ça → repli, et la
  règle **Acheter** est trouvée. C'est ce qui fait fonctionner F3.

  > **Précision du 2026-08-06 — par quel étage exactement.** Formulation initiale corrigée : ce
  > n'est **pas** le repli « routes de l'entrepôt », c'est l'étage **produit / catégorie**.
  > La route `Buy` n'est pas `warehouse_selectable` — le champ n'est pas renseigné à sa création
  > (`purchase_stock/data/purchase_stock_data.xml:10-14`) et son défaut est `False`
  > (`stock/models/stock_location.py:473`). Or `stock.warehouse.route_ids` a pour domaine
  > `[('warehouse_selectable','=',True)]` (`stock/models/stock_warehouse.py:52-56`) : `Buy` n'y
  > entre jamais.
  >
  > Ce qui la rend trouvable, c'est qu'elle est **posée par défaut sur chaque article** :
  > `route_ids = fields.Many2many(default=lambda self: self._get_buy_route())`
  > (`purchase_stock/models/product.py:28-33`). L'étage 3 de `_search_rule`
  > (`product_id.route_ids | product_id.categ_id.total_route_ids`) la trouve donc.
  >
  > **Conséquence à vérifier pour RPBM, et elle porte sur 82 % du catalogue** :
  > [`import_odoo.py`](../import_odoo.py) n'écrit **jamais** `route_ids` (les champs produits sont
  > listés ligne 346). Le défaut Odoo doit donc s'appliquer aux 3 229 articles importés — mais cela
  > **n'a pas été contrôlé sur l'instance**. Si la route `Buy` manque sur les articles migrés,
  > **F3 ne se déclenche pas**. À vérifier avant toute mise en service, sur un échantillon
  > d'articles importés.

### 4.3 Deux limites à documenter dans chaque architecture

1. **Le transporteur doit être posé avant la confirmation** de la commande : l'approvisionnement est
   calculé à ce moment-là, et le changer après ne rejoue pas les règles.
2. **C'est un choix par commande, pas par ligne.** Une commande mixte (une pièce posée sur site, une
   autre retirée au comptoir) demande de revenir à `sale.order.line.route_id`, qui reprend la main
   puisqu'elle est prioritaire.

L'assistant standard « Ajouter un mode de livraison » crée aussi une **ligne de livraison** sur la
commande (`delivery/models/sale_order.py:58-63`, `product_id` est `required` sur
`delivery.carrier`). À prix nul c'est une ligne de bruit ; à documenter comme tel.

---

## 5. Périmètre de réservation — pool par comptoir

**Défaut retenu le 2026-08-06, à confirmer par le client** ([Q9](../questions-ouvertes.md#q9)) :

> **Une vente comptoir ne réserve pas le stock de l'autre comptoir.**

Ce que cela veut dire exactement :

- le comptoir sert d'abord **son propre stock** ;
- à défaut, il puise dans les **dépôts**, par un transfert qui produit un document ;
- le stock de **l'autre comptoir** n'est jamais atteint ;
- le stock **du camion** non plus — le camion est hors de l'arbre de réservation des comptoirs.

**Aucun levier natif n'existe pour exclure un emplacement de la réservation** : `stock.quant._gather`
filtre en `child_of` (`stock/models/stock_quant.py:813-819`). Les deux seuls leviers sont la
**forme de l'arbre d'emplacements** et le `location_src_id` des règles. Chaque architecture doit
donc montrer **comment elle obtient ce comportement**.

**Conséquence sur les documents** : F1 coûte 2 documents et F3 en coûte 3. F9 reste à 1.

---

## 6. Les onze flux

Liste canonique. Chaque document d'architecture produit **un diagramme de séquence par flux**,
en nommant les types d'opération et les emplacements de son implémentation.

| # | Flux | Chemin |
|---|---|---|
| F1 | Pièce en stock au dépôt → pose au comptoir | Dépôt → Comptoir → Client |
| F2 | Pièce en stock au dépôt → pose sur site | Dépôt → Camion → Client |
| F3 | Pièce absente → achat → dépôt → comptoir | Fournisseur → Dépôt → Comptoir → Client |
| F4 | Pièce absente → le fournisseur livre au comptoir | Fournisseur → Comptoir → Client |
| F5 | Réception au comptoir → chargement camion → pose sur site | Fournisseur → Comptoir → Camion → Client |
| F6 | Le comptoir renvoie une pièce en dépôt | Comptoir → Dépôt |
| F7 | Article chargé mais non posé → retour | Camion → Comptoir ou Dépôt |
| F8 | Casse au dépôt, au comptoir ou en tournée | site → `CASSE` |
| F9 | Vente servie depuis le stock du comptoir | Comptoir → Client |
| F10 | Rééquilibrage entre sites de même profil | D1 ↔ D2, Galleria ↔ Genipa |
| F11 | Retour fournisseur | site → Fournisseur |

Narration métier et diagrammes d'intention :
[architectures-stock.md § A.3](../architectures-stock.md#a3-les-onze-flux).

---

## 7. Format imposé aux trois documents d'architecture

Pour qu'ils soient comparables, les trois suivent le **même plan** :

1. **Structure** — arbre des emplacements, entrepôts s'il y en a
2. **Enregistrements** — un tableau par modèle, avec les champs à renseigner :
   `stock.warehouse` · `stock.location` · `stock.picking.type` · `stock.route` · `stock.rule` ·
   `delivery.carrier`
3. **Les onze flux** — un diagramme de séquence Mermaid par flux, plus le décompte de documents
4. **Ce que cette architecture impose de particulier** — écarts au standard, configurations
   manuelles, points à vérifier en préproduction
5. **Ce qu'elle ne donne pas**

Règles de rédaction :

- **les diagrammes nomment les types d'opération et les emplacements réels**, pas des rôles
  génériques — `D2-GALL` et `RPBM/Stock/Dépôt 2/R412`, pas « transfert » et « le dépôt » ;
- **toute affirmation sur le comportement d'Odoo est sourcée** `fichier:ligne` depuis
  `D:\git\odoo_17`, jamais de mémoire ;
- **aucune configuration n'est appliquée sur l'instance** — ces documents décrivent une cible ;
- ce qui est déjà dans ce document-ci n'est pas répété, il y est renvoyé.
