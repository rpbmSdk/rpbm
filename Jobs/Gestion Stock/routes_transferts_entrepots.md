# Routes et transferts entre entrepôts — réapprovisionnement et opérations sur site

Date de rédaction : 2026-07-23
Statut : proposition à valider avec RPBM, aucune configuration Odoo effectuée.

> **Note du 2026-08-05.** Ce document part de l'hypothèse de 5 entrepôts Odoo distincts, qui est
> précisément ce que la question ouverte Q1 remet en cause : la forme du stock RPBM (78 % des
> références en stock n'ont qu'une seule unité) rend le réapprovisionnement par anticipation sans
> objet, ce qui retire leur intérêt aux routes inter-entrepôts. Il reste la meilleure référence sur
> les mécanismes Odoo mobilisables ; l'analyse et la recommandation à jour sont dans
> [questions-ouvertes.md](questions-ouvertes.md#q1).

## 1. Contexte

Suite à la décision d'architecture du 2026-07-23 (voir `infos.md` §5.2 et `README.md`), RPBM aura **5 entrepôts Odoo distincts** (`stock.warehouse`) : `Galleria`, `Genipa` (entrepôts principaux / points de vente), `Dépôt 1`, `Dépôt 2` (entrepôts déportés de stockage), et `Camion` (opérations sur site).

Deux besoins métier restent à câbler avec les mécanismes de routes Odoo :

1. **Réapprovisionnement** : quand un article est vendu à `Galleria` ou `Genipa` mais que le stock physique est en réalité à `Dépôt 1` ou `Dépôt 2`, comment Odoo doit-il organiser le transfert ?
2. **Opérations de pose sur site** : quand un conducteur de camion doit récupérer des articles répartis entre `Dépôt 1`, `Dépôt 2`, `Galleria` et `Genipa` avant de les poser chez le client, comment modéliser ce trajet dans Odoo ?

Ce document traduit les mécanismes documentés par Odoo (routes, règles push/pull, réapprovisionnement inter-entrepôts, cross-dock, entrepôt virtuel, suivi de service via Project, routes spécifiques de ligne de commande) en propositions concrètes pour ces deux cas, et liste les décisions encore à prendre par RPBM. Field Service a été étudié puis écarté de la proposition retenue (cf. §2.5 et révision du §4) — il reste documenté pour référence future uniquement.

## 2. Concepts Odoo mobilisés

### 2.1 Routes et règles push/pull

Une **route** est un ensemble de règles qui automatisent le déplacement des produits entre emplacements. Une règle **pull** (tirer) crée un transfert à la demande (ex. commande client, réapprovisionnement) ; elle remonte depuis le point de demande vers la source. Une règle **push** (pousser) déplace automatiquement un produit dès son arrivée à un emplacement donné, sans demande externe. Les routes peuvent être appliquées sur un produit, une catégorie de produits, un entrepôt ou une ligne de commande de vente. Odoo permet des flux de réception/livraison en 1, 2 ou 3 étapes en chaînant plusieurs règles.

Source : [Routes and push/pull rules — Odoo 17.0 documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/shipping_receiving/daily_operations/use_routes.html)

### 2.2 Réapprovisionnement inter-entrepôts (« Resupply From »)

Sur la fiche d'un entrepôt, un champ **« Réapprovisionner depuis » (Resupply From)** permet de cocher un ou plusieurs entrepôts sources. Odoo crée alors automatiquement une route **« Approvisionner le produit depuis [entrepôt source] »**, qu'il faut activer sur la fiche produit (onglet Inventaire) ou sur une catégorie de produits pour qu'elle s'applique. Une fois la route active, deux mécanismes peuvent la déclencher :

- **Règle de stock min/max (reordering rule)** : quand le stock prévisionnel d'un entrepôt descend sous un seuil `Min`, Odoo génère automatiquement un réapprovisionnement pour remonter jusqu'à `Max`. Le déclenchement peut être `Auto` (automatique, au passage du planificateur, par défaut la nuit) ou `Manuel` (visible dans le rapport de réapprovisionnement, validation humaine avant lancement).
- **Route MTO (Make To Order)** combinée à la route de réapprovisionnement : la confirmation d'une commande client à l'entrepôt de destination déclenche directement la chaîne de transferts.

Dans les deux cas, Odoo crée **deux transferts liés** : un bon de livraison depuis l'entrepôt source, et une réception à l'entrepôt de destination (transitant par l'emplacement virtuel « Inter-warehouse transit »).

Sources : [Inter-warehouse replenishment — Odoo 17.0 documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/warehouses_storage/inventory_management/resupply_warehouses.html) · [Reordering rules — Odoo 17.0 documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/product_management/product_replenishment/reordering_rules.html)

### 2.3 Cross-dock

Le cross-dock est le fait d'acheminer un produit reçu directement vers le client sans qu'il n'entre réellement en stock durable : la réception et l'expédition sont configurées en 2 étapes, avec une zone de cross-dock entre l'emplacement d'entrée et l'emplacement de sortie. À la confirmation d'une commande, Odoo crée deux transferts liés (entrée → sortie, puis sortie → client), tous deux en attente jusqu'à l'arrivée effective de la marchandise. C'est un mécanisme pensé pour un flux fournisseur → client au sein d'un même entrepôt, mais le principe (transit sans stockage durable, deux transferts chaînés) est transposable à un point de transit inter-entrepôts comme `Camion`.

Source : [Organize a cross-dock in a warehouse — Odoo 17.0 documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/shipping_receiving/daily_operations/cross_dock.html)

### 2.4 Entrepôt virtuel (vente depuis plusieurs entrepôts)

Quand un article peut être livré depuis plusieurs entrepôts pour une seule commande, Odoo propose un **emplacement virtuel de type « Vue » (View)**, parent des entrepôts réels, utilisable comme entrepôt par défaut sur la commande de vente ou sur la fiche d'un vendeur. Les entrepôts réels (ex. `Dépôt 1`, `Dépôt 2`, `Galleria`, `Genipa`) deviennent des enfants de cet entrepôt virtuel, et Odoo peut puiser le stock disponible chez l'un ou l'autre pour satisfaire la demande.

Source : [Sell stock from multiple warehouses using virtual locations — Odoo 18.0 documentation](https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/inventory/shipping_receiving/daily_operations/stock_warehouses.html)

### 2.5 Field Service — entrepôt par défaut du technicien / du véhicule

L'application **Field Service** (services d'intervention sur site) permet de définir un **entrepôt par défaut** pour un technicien, pensé explicitement pour « ceux qui gardent un stock dans leur camionnette ». Les commandes créées pendant une intervention puisent automatiquement dans cet entrepôt, et une fois l'intervention marquée terminée, le stock de l'entrepôt par défaut est mis à jour automatiquement — sans double saisie. Prérequis : emplacements de stockage activés, plusieurs entrepôts configurés dans la base, **et l'application Field Service elle-même**, distincte de l'application Project de base (confirmé par la documentation : la création automatique de tâche depuis une commande de vente y est explicitement décrite comme une fonctionnalité de Field Service, pas de Project).

Source : [Product management — Odoo 19.0 documentation (Field Service)](https://www.odoo.com/documentation/19.0/applications/services/field_service/product_management.html) · [Creating field service tasks — Odoo 17.0 documentation](https://www.odoo.com/documentation/17.0/applications/services/field_service/creating_tasks.html)

**Correction du 2026-07-23** : RPBM a indiqué ne pas être prêt à adopter l'application Field Service, et fonctionne par le circuit de vente classique (devis → commande). Cette section 2.5 reste documentée pour référence future, mais la proposition du §4 ci-dessous repose désormais sur les mécanismes de base **Ventes + Project + Inventaire**, sans Field Service.

### 2.6 Créer une tâche de service depuis une commande de vente, sans Field Service (Project)

Indépendamment de Field Service, l'application **Project** de base propose un mécanisme de **suivi de service** (« Service Tracking ») directement sur la fiche produit : pour un produit de type **Service**, l'onglet Ventes propose un champ « Suivi du service » avec plusieurs options — créer une tâche dans un projet existant, créer un projet dédié pour la commande, ou créer un projet sans tâche. Une fois le devis confirmé en commande, la tâche (ou le projet) est créée automatiquement, et le temps passé peut être suivi via les feuilles de temps.

C'est le mécanisme correspondant exactement à l'intuition de RPBM : vendre un article de type **Service** (« Pose sur site ») sur la commande, dont le suivi de service crée automatiquement une tâche — sans nécessiter l'application Field Service, qui n'apporte que des fonctionnalités additionnelles (planification calendaire, application mobile, checklist d'intervention, consommation automatique depuis un entrepôt par défaut).

Source : [Create Projects and Tasks from Sales Orders — Odoo 13.0 documentation](https://www.odoo.com/documentation/13.0/applications/services/project/advanced/so_to_task.html) *(mécanisme stable depuis plusieurs versions ; page 13.0 la plus explicite trouvée, comportement à reconfirmer sur la version exacte de la base RPBM)*.

### 2.7 Router spécifiquement les lignes stockables d'une commande (indépendamment du service)

Le mécanisme de suivi de service (§2.6) ne concerne que la ligne de service elle-même : il ne route **pas** automatiquement les autres lignes de la commande (articles stockables/consommables) vers un circuit logistique particulier. Pour cela, Odoo propose un réglage Ventes distinct : **« Choisir des routes spécifiques sur les lignes de commande (avancé) »** (Configuration → Réglages de l'application Ventes). Une fois activé, un champ Route apparaît sur chaque ligne de commande (à rendre visible via les options de colonnes), permettant de choisir manuellement, ligne par ligne, quelle route logistique le produit doit suivre — utile quand certaines lignes suivent un circuit standard et d'autres un circuit particulier comme le passage par `Camion`.

Cela permet de construire une route dédiée (ex. « Pose sur site via Camion ») et de ne l'appliquer qu'aux lignes de commande stockables/consommables d'une intervention de pose, sans toucher au reste du catalogue.

Source : [Routes and push/pull rules — Odoo 17.0 documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/shipping_receiving/daily_operations/use_routes.html)

## 3. Application au cas Galleria / Genipa (réapprovisionnement lors d'une vente)

Proposition, à valider avec RPBM :

1. Sur la fiche de l'entrepôt `Galleria`, cocher **« Réapprovisionner depuis »** = `Dépôt 1` et/ou `Dépôt 2` (idem pour `Genipa`).
2. Activer la route générée (« Galleria : Approvisionner le produit depuis Dépôt 1 », etc.) sur les catégories de produits stockables (`Pare-brise`, `Lunette`, `Glace latérale`, `Joint`, `Film solaire`, `Autres` et ses sous-catégories) plutôt que produit par produit, pour éviter une configuration manuelle sur des milliers de références.
3. Choisir le mode de déclenchement par catégorie de rotation :
   - **Règles de stock min/max** pour les familles à forte rotation (`Pare-brise`, `Joint`) : réapprovisionnement de fond, indépendant d'une vente précise.
   - **Route MTO** pour les familles rares ou de forte valeur unitaire, où l'on préfère ne déplacer l'article qu'au moment où une vente est confirmée (évite de dupliquer du stock cher sur plusieurs sites).

### Décision à obtenir de RPBM

- Règle de rattachement : quel dépôt (`Dépôt 1` ou `Dépôt 2`) réapprovisionne quel entrepôt principal (`Galleria` ou `Genipa`) ? Les deux dépôts peuvent-ils réapprovisionner les deux points de vente indifféremment, ou existe-t-il une règle géographique/organisationnelle ?
- Seuils min/max par catégorie ou par référence (nécessite un historique de rotation, à construire une fois le catalogue importé).
- Répartition règles min/max vs MTO par catégorie.

## 4. Application au cas Camion (opérations de pose sur site)

**Révision du 2026-07-23** : la première version de cette section proposait Field Service comme option B. RPBM a indiqué ne pas être prêt à adopter cette application, et fonctionne par le circuit de vente classique (devis → commande), qui peut mélanger sur une même commande une ligne de service (pose sur site) et des lignes d'articles stockables/consommables. La proposition ci-dessous est donc reconstruite sans Field Service, à partir des mécanismes Ventes + Project + Inventaire de base (§2.6 et §2.7).

Le cas comporte deux besoins distincts, à traiter par deux mécanismes indépendants sur la **même commande de vente** :

1. La ligne de **service** « Pose sur site » doit générer une tâche de suivi (qui fait quoi, quand, chez quel client).
2. Les lignes d'**articles stockables/consommables** de cette même commande doivent suivre un circuit logistique `Stock (entrepôt source) → Camion → Client`, et non le circuit de livraison standard d'un entrepôt vers le client.

### 4.1 Suivi de la ligne de service (sans Field Service)

Créer un article de type **Service**, par exemple « Pose sur site », avec **Suivi du service = créer une tâche** (dans un projet existant type « Interventions », ou un projet dédié par commande — cf. §2.6). À la confirmation de la commande, la tâche est créée automatiquement et sert de point d'ancrage pour la planification et le suivi de l'intervention (qui, quand, chez quel client), sans dépendre d'Inventaire.

Ce mécanisme est indépendant du routage logistique ci-dessous : la tâche ne pilote pas automatiquement les transferts de stock, elle sert de suivi opérationnel/planification. Le lien entre « cette tâche » et « ce transfert » reste à faire manuellement par le planificateur (même commande de vente comme référence commune), sauf développement spécifique ultérieur.

### 4.2 Routage des lignes stockables via Camion (sans Field Service)

1. Activer dans Ventes → Configuration → Réglages : **« Choisir des routes spécifiques sur les lignes de commande (avancé) »** (§2.7).
2. Créer une route dédiée, par exemple **« Pose sur site via Camion »**, composée de règles pull chaînées : `Dépôt 1/Stock → Camion/Stock`, `Dépôt 2/Stock → Camion/Stock`, `Galleria/Stock → Camion/Stock`, `Genipa/Stock → Camion/Stock` (une règle par entrepôt source potentiel), puis `Camion/Stock → Emplacement client`. C'est une extrapolation du mécanisme de réapprovisionnement inter-entrepôts (§2.2) et de la logique cross-dock (§2.3) à un point de transit `Camion` alimenté par 4 sources possibles plutôt qu'une seule — **ce montage précis n'est pas documenté tel quel par Odoo et devra être testé en préproduction** pour valider quelle règle se déclenche quand plusieurs entrepôts sources ont du stock disponible.
3. Sur la commande de vente, sélectionner manuellement cette route sur les lignes d'articles stockables/consommables concernées par l'intervention (colonne Route, à rendre visible). La ligne de service (§4.1) n'a pas de route logistique, elle n'est pas stockée.
4. Le chargement effectif du camion reste, dans un premier temps, un **geste opérationnel humain** : le planificateur ou le conducteur valide les transferts générés (`Dépôt 1/2`, `Galleria`, `Genipa` → `Camion`) chaque matin selon la tournée du jour, plutôt qu'une automatisation complète — l'automatisation (règles min/max, priorité de source) pouvant être ajoutée dans un second temps si le volume d'interventions le justifie.

### Décisions à obtenir de RPBM

- Valider le principe : une commande = une ligne de service (tâche) + des lignes d'articles routées via `Camion`, sans Field Service.
- Règle de priorité quand un article est disponible dans plusieurs entrepôts sources (le plus proche ? le moins cher à transporter ? choix manuel du conducteur/planificateur) ?
- Qui prépare le chargement du camion et à quelle fréquence (manuel chaque matin vs règle automatique) ?
- Que se passe-t-il si un article chargé dans le camion n'est finalement pas posé chez le client (retour vers quel entrepôt) ?
- Le projet/tâche de suivi des interventions existe-t-il déjà dans une autre partie de l'organisation RPBM (planification actuelle des poses), ou faut-il le créer de toutes pièces ?

## 5. Sources consultées

- [Routes and push/pull rules — Odoo 17.0 documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/shipping_receiving/daily_operations/use_routes.html)
- [Inter-warehouse replenishment — Odoo 17.0 documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/warehouses_storage/inventory_management/resupply_warehouses.html)
- [Reordering rules — Odoo 17.0 documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/product_management/product_replenishment/reordering_rules.html)
- [Organize a cross-dock in a warehouse — Odoo 17.0 documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/shipping_receiving/daily_operations/cross_dock.html)
- [Sell stock from multiple warehouses using virtual locations — Odoo 18.0 documentation](https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/inventory/shipping_receiving/daily_operations/stock_warehouses.html)
- [Product management — Odoo 19.0 documentation (Field Service)](https://www.odoo.com/documentation/19.0/applications/services/field_service/product_management.html)
- [Creating field service tasks — Odoo 17.0 documentation](https://www.odoo.com/documentation/17.0/applications/services/field_service/creating_tasks.html)
- [Create Projects and Tasks from Sales Orders — Odoo 13.0 documentation](https://www.odoo.com/documentation/13.0/applications/services/project/advanced/so_to_task.html)

Ces pages n'ont pas pu être vérifiées directement dans le code source `D:\git\odoo_17` (hors périmètre de cette recherche, focalisée sur la documentation odoo.com comme demandé) ; une vérification du comportement exact des règles de réapprovisionnement dans le module `stock` d'Odoo 17 Community/Enterprise est recommandée avant configuration en préproduction.
