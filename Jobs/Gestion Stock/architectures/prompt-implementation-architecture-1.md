# Prompt — Implémentation de l'architecture 1 sur `rpbm-preprod`

> À copier tel quel comme instruction d'agent. Rédigé le 2026-08-06.
> Cible de référence : [01-architecture-1-zones.md](01-architecture-1-zones.md) ·
> Invariants : [00-invariants.md](00-invariants.md)

---

Tu implémentes **l'architecture 1** (un entrepôt Odoo unique, les 5 sites en zones de stockage) sur
l'instance de préproduction RPBM, via la skill **`paradigme-mcp-local`**.

## Accès — contrainte absolue

- Utilise **exclusivement** la skill `paradigme-mcp-local`. Elle lit le profil dans
  `.paradigme.yaml` à la racine du dépôt, qui vaut `rpbm-preprod`.
- **Le fichier `~/.paradigme/paradigme_odoo_mcp.yaml` déclare aussi un profil `rpbm`, qui est la
  PRODUCTION. Tu ne dois JAMAIS l'utiliser, ni le sélectionner, ni y écrire, sous aucun prétexte.**
  Avant la première écriture, confirme que l'URL cible est bien `https://rpbm-pre-prod.odoo.com/`.
  Si ce n'est pas le cas, arrête-toi immédiatement et signale-le.
- Ne copie aucun secret dans le dépôt.

## Mode opératoire

Le client a demandé une **application directe, sans point d'arrêt** : la préproduction est
considérée comme jetable. Tu appliques donc les phases dans l'ordre, sans demander de validation
intermédiaire. Mais :

- **chaque écriture est idempotente** : tu cherches avant de créer, tu mets à jour si l'objet
  existe. Le prompt doit pouvoir être rejoué sans créer de doublon ;
- **tu relis après chaque phase** ce que tu viens d'écrire, et tu passes à la suivante seulement si
  le relevé correspond ;
- **si une phase échoue, tu t'arrêtes** et tu rends compte — tu ne continues pas sur un état
  intermédiaire inconnu ;
- tu ne supprimes rien. Ce qui doit disparaître est **archivé** (`active = False`).

---

## Phase 0 — Relevé de l'existant

Relève et consigne, sans rien écrire :

1. `stock.warehouse` : `id`, `name`, `code`, `lot_stock_id`, `view_location_id`,
   `reception_steps`, `delivery_steps`, `buy_to_resupply`.
2. `stock.location` internes : arbre complet avec `location_id`, `usage`, `replenish_location`.
   Identifie précisément `Stock D1`, `Stock D2`, `GALLERIA`, `GENIPA`, `A controler`.
3. `stock.picking.type` existants : `name`, `code`, `sequence_code`,
   `default_location_src_id`, `default_location_dest_id`, `warehouse_id`.
4. `stock.route` et `stock.rule` existants : pour chaque règle, `action`, `location_src_id`,
   `location_dest_id`, `picking_type_id`, `procure_method`, `route_id`.
5. `stock.quant` : nombre de quants et somme des quantités **par emplacement**. Tu en auras besoin
   pour vérifier qu'aucune quantité ne bouge lors des déplacements d'emplacements.

### 0 bis — Vérification bloquante : la route `Buy` sur les articles

**C'est le point le plus important du prompt.** La route `Buy` n'est pas `warehouse_selectable` :
elle n'est trouvée par `_search_rule` que parce qu'elle est posée **par défaut sur chaque article**
(`purchase_stock/models/product.py:28-33`). Or [`import_odoo.py`](../import_odoo.py) n'écrit jamais
`route_ids`.

Vérifie sur un échantillon d'au moins 50 articles importés (ceux qui portent `x_studio_eurocode`)
si `route_ids` contient bien la route `Buy` :

- **si oui** : consigne-le et continue ;
- **si non** : c'est un défaut majeur — **82 % du catalogue ne pourrait pas être approvisionné**.
  Ajoute la route `Buy` à tous les articles stockables concernés, en une écriture par lot, puis
  recontrôle. Signale-le en tête de ton rapport final comme un correctif appliqué, pas comme une
  routine.

---

## Phase 1 — L'arbre d'emplacements

Cible :

```
RPBM (vue)                          existant
├── Stock                           À CRÉER — internal — futur lot_stock_id
│   ├── Dépôts                      À CRÉER — internal
│   │   ├── Dépôt 1                 = « Stock D1 » existant, déplacé
│   │   └── Dépôt 2                 = « Stock D2 » existant, déplacé
│   ├── Galleria                    = « GALLERIA » existant, déplacé
│   └── Genipa                      = « GENIPA » existant, déplacé
├── Camion                          À CRÉER — internal — HORS de Stock, volontairement
└── A controler                     existant, laissé où il est
```

Ordre imposé :

1. créer `Stock` (`usage = internal`, parent = la `view_location_id` de l'entrepôt `RPBM`) ;
2. créer `Dépôts` (`usage = internal`, parent = `Stock`) ;
3. **déplacer** `Stock D1` et `Stock D2` sous `Dépôts` (écrire `location_id`), et `GALLERIA` /
   `GENIPA` sous `Stock`. Leurs enfants — les racks — suivent automatiquement ;
4. créer `Camion` (`usage = internal`, parent = la vue `RPBM`, **pas** sous `Stock`) ;
5. positionner `stock.warehouse.lot_stock_id` de `RPBM` sur le nouveau `Stock`.

**Contrôles après phase 1** :

- le total des quants et des quantités par produit est **identique** au relevé de la phase 0 —
  déplacer un emplacement ne doit rien déplacer physiquement ;
- l'ancien défaut est corrigé : une commande client doit désormais pouvoir réserver les **799**
  unités, contre 67 auparavant.

**Piège à traiter** : `default_location_src_id` et `default_location_dest_id` des types d'opération
existants dépendent de `warehouse_id`, **pas** de `lot_stock_id`. Changer `lot_stock_id` ne les
recalcule donc pas. Repointe-les explicitement, ainsi que les `location_src_id` /
`location_dest_id` des règles des routes existantes `RPBM: Recevoir en 1 étape` et
`RPBM: Livrer en 1 étape`, qui visent encore `Stock D1`.

**`replenish_location`** : ne le coche sur aucun comptoir. Odoo interdit deux emplacements de
réassort dans une même chaîne parent/enfant (`stock/models/stock_location.py:171-178`) et le
nouveau `Stock` le porte déjà (`stock/models/stock_warehouse.py:640`). Le réassort des comptoirs
passera par des `stock.warehouse.orderpoint` avec `location_id` sur la zone.

---

## Phase 2 — Les 26 types d'opération

Tous rattachés à l'unique entrepôt `RPBM` : les préfixes seront `RPBM/<sequence_code>/`.

Paramètres communs : `reservation_method = at_confirm`, `create_backorder = ask`, **sauf** pour les
deux types du camion, signalés ci-dessous.

### 2.1 Tirés par la vente — 3 types, `code = internal`

Ce sont les seuls que les règles peuvent déclencher. Ils sont volontairement **regroupés** : une
`stock.rule` porte un `picking_type_id` unique (`required=True`,
`stock/models/stock_rule.py:75-78`) et `_search_rule` n'en retient qu'une par route et destination
(`:536-549`). Différencier `D1-GALL` de `D2-GALL` en automatique est donc impossible — le dépôt
d'origine reste lisible **à la ligne** du document, via l'emplacement source.

| Nom | `sequence_code` | `default_location_src_id` | `default_location_dest_id` |
|---|---|---|---|
| Transfert Dépôts → Galleria | `DEP-GALL` | `RPBM/Stock/Dépôts` | `RPBM/Stock/Galleria` |
| Transfert Dépôts → Genipa | `DEP-GENI` | `RPBM/Stock/Dépôts` | `RPBM/Stock/Genipa` |
| Chargement camion | `STK-CAM` | `RPBM/Stock` | `RPBM/Camion` | 

`STK-CAM` : `reservation_method = manual`, `create_backorder = always`.

> **Pourquoi une seule règle de chargement.** Un type `Dépôts → Camion` et un type
> `Comptoir → Camion` viseraient la même destination sur la même route : une seule serait retenue.
> La source est donc `RPBM/Stock`, qui couvre dépôts et comptoirs. C'est une **exception assumée au
> pool par comptoir** — le camion est une ressource d'entreprise, pas le stock d'un site. À
> consigner comme telle.

### 2.2 Créés à la main — 12 types, `code = internal`

Aucune règle ne les déclenche : l'utilisateur choisit le type, donc les couples orientés restent
tous distincts. C'est là que la différenciation demandée est intégralement obtenue.

| Flux | Types |
|---|---|
| F6 — comptoir → dépôt | `GALL-D1`, `GALL-D2`, `GENI-D1`, `GENI-D2` |
| F7 — retour camion | `CAM-D1`, `CAM-D2`, `CAM-GALL`, `CAM-GENI` |
| F10 — rééquilibrage | `D1-D2`, `D2-D1`, `GALL-GENI`, `GENI-GALL` |

Source et destination de chacun : les deux emplacements nommés dans son code.

### 2.3 Réceptions fournisseur — 4 types, `code = incoming`

Source = `Partners/Vendors`.

| Nom | `sequence_code` | `default_location_dest_id` |
|---|---|---|
| Réception Dépôt 1 | `D1/IN` | `RPBM/Stock/Dépôts/Dépôt 1` |
| Réception Dépôt 2 | `D2/IN` | `RPBM/Stock/Dépôts/Dépôt 2` |
| Réception Galleria | `GALL/IN` | `RPBM/Stock/Galleria` |
| Réception Genipa | `GENI/IN` | `RPBM/Stock/Genipa` |

**Réutilise le type `Réceptions` [IN] existant** comme `Réception Dépôt 2` plutôt que d'en créer un
de plus, et repointe-le.

Ces types sont le mécanisme de **F4** : l'acheteur bascule le champ « Livrer à » de la demande de
prix sur `Réception Galleria` **avant confirmation**, et la marchandise arrive au comptoir
(`purchase_stock/models/purchase_order.py:204-208`).

### 2.4 Livraisons client — 3 types, `code = outgoing`

Destination = `Partners/Customers`.

| Nom | `sequence_code` | `default_location_src_id` | Note |
|---|---|---|---|
| Livraison Galleria | `GALL/OUT` | `RPBM/Stock/Galleria` | **réutiliser** `Livraisons Galleria` existant |
| Livraison Genipa | `GENI/OUT` | `RPBM/Stock/Genipa` | **réutiliser** `Livraisons Génipa` existant |
| Pose sur site | `CAM/OUT` | `RPBM/Camion` | `reservation_method = manual`, `create_backorder = always` |

Les deux types existants partagent aujourd'hui le `sequence_code` `OUT` : c'est ce qu'il faut
corriger ici pour obtenir une numérotation distincte par comptoir.

### 2.5 Retours fournisseur — 4 types, `code = outgoing`

Destination = `Partners/Vendors`. Rattache chacun au type de réception correspondant via
`return_picking_type_id`, qui est ce que le wizard de retour utilise
(`stock/wizard/stock_picking_return.py:116`).

`D1/RET`, `D2/RET`, `GALL/RET`, `GENI/RET`.

---

## Phase 3 — Routes et règles

Trois routes, toutes en `shipping_selectable = True` **et** `sale_selectable = True` — la première
pour la sélection par transporteur, la seconde pour reprendre la main ligne par ligne sur une
commande mixte.

### Route « Retrait Galleria »

| # | `location_src_id` | `location_dest_id` | `action` | `procure_method` | `picking_type_id` |
|---|---|---|---|---|---|
| 1 | `RPBM/Stock/Galleria` | `Partners/Customers` | `pull` | `mts_else_mto` | `GALL/OUT` |
| 2 | `RPBM/Stock/Dépôts` | `RPBM/Stock/Galleria` | `pull` | `mts_else_mto` | `DEP-GALL` |

Lecture : la pièce est servie depuis le comptoir si elle y est (1 document) ; sinon la règle 2 la
prend aux dépôts (2 documents) ; sinon l'achat part. **Le stock de l'autre comptoir n'est jamais
atteint** — c'est le pool par comptoir.

### Route « Retrait Genipa »

Symétrique, avec `Genipa`, `GENI/OUT` et `DEP-GENI`.

### Route « Pose sur site »

| # | `location_src_id` | `location_dest_id` | `action` | `procure_method` | `picking_type_id` |
|---|---|---|---|---|---|
| 1 | `RPBM/Camion` | `Partners/Customers` | `pull` | `make_to_order` | `CAM/OUT` |
| 2 | `RPBM/Stock` | `RPBM/Camion` | `pull` | `mts_else_mto` | `STK-CAM` |

### La règle `Buy` — piège à traiter explicitement

`_get_rule` remonte vers les **parents** de la destination, jamais vers ses enfants. Une règle
`Buy` pointant sur `Dépôt 2` serait donc invisible depuis une escalade portée par `Dépôts`, et
**F3 échouerait**.

- `location_dest_id` de la règle `Buy` doit être **`RPBM/Stock`** ;
- son `picking_type_id` peut être `D2/IN`, donc **diverger** de sa destination. C'est voulu.

Attention : Odoo réaligne ces deux champs dès qu'on écrit `reception_steps` ou `buy_to_resupply`
sur l'entrepôt (`purchase_stock/models/stock.py:37-42`). Après toute modification de l'entrepôt,
**recontrôle cette règle**.

---

## Phase 4 — Les trois transporteurs

Un `delivery.carrier` par route. `product_id` est `required` : crée pour chacun un article de
service dédié, `detailed_type = service`, non stockable.

| Transporteur | `route_ids` | `delivery_type` | Prix |
|---|---|---|---|
| Retrait / pose Galleria | `Retrait Galleria` | `fixed` | 0 |
| Retrait / pose Genipa | `Retrait Genipa` | `fixed` | 0 |
| Pose sur site | `Pose sur site` | `fixed` | à définir avec RPBM — c'est le frais de déplacement |

Deux limites à consigner dans ton rapport, pas à corriger :

1. le transporteur doit être posé **avant la confirmation** de la commande ; le changer après ne
   rejoue pas les règles ;
2. l'assistant « Ajouter un mode de livraison » crée aussi une **ligne de livraison** sur la
   commande (`delivery/models/sale_order.py:58-63`). À 0 €, c'est une ligne de bruit sur chaque
   devis.

---

## Phase 5 — Recette fonctionnelle

Déroule ces scénarios sur l'instance et consigne le résultat réel de chacun. Ce sont les points
**déduits du code mais jamais exécutés** — c'est ici qu'on saura.

| # | Scénario | Attendu |
|---|---|---|
| T1 | Vente, transporteur « Retrait Galleria », pièce présente à Galleria | **1** document : `GALL/OUT` |
| T2 | Idem, pièce présente au rack `Dépôt 2/R…` | **2** documents : `DEP-GALL` réservé au rack dès la confirmation, puis `GALL/OUT` en attente |
| T3 | Idem, pièce nulle part | **3** : demande de prix `Buy` + réception + `DEP-GALL` + `GALL/OUT` — vérifie que l'achat part bien, c'est le test de la route `Buy` |
| T4 | Idem, pièce présente **à Genipa uniquement** | la pièce n'est **pas** réservée, un achat se déclenche — c'est le pool par comptoir |
| T5 | Vente, transporteur « Pose sur site » | **2** : `STK-CAM` puis `CAM/OUT` |
| T6 | Sur T3, bascule « Livrer à » sur `Réception Galleria` avant confirmation de l'achat | **comportement inconnu** : la marchandise arrive au comptoir alors qu'un `DEP-GALL` reste planifié. Décris exactement ce qui se passe |
| T7 | Vente sans transporteur | décris quelle route s'applique par défaut |
| T8 | Transfert manuel `GALL-D1` créé à la main | 1 document, type correct |

---

## Rapport final

Rends compte en distinguant clairement :

1. **le résultat de la vérification 0 bis** sur la route `Buy` — en tête, c'est le risque numéro un ;
2. **les enregistrements créés, modifiés, archivés**, avec leurs identifiants ;
3. **le résultat réel de chacun des 8 tests**, en particulier **T6**, dont le comportement n'est
   documenté nulle part ;
4. **les écarts** entre la cible décrite ici et ce que tu as réellement pu configurer, avec le
   motif ;
5. **ce que tu n'as pas vérifié.**

Ne présente comme fait que ce que tu as observé. Si un test n'a pas pu être joué, dis-le — ne le
déduis pas du code.
