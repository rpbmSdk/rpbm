# RPBM — Correspondances de catégories, emplacements et données utiles à la migration Odoo

> **Document de cadrage figé au 2026-07-23.** Conservé pour le détail terrain (dépôts, typologies,
> statuts d'inventaire, sources GRH) qui ne figure nulle part ailleurs. Il contient en revanche des
> propositions dépassées et des chiffres faux — notamment « 7 blocs de racks jusqu'à R728 », alors
> qu'il y en a 9 jusqu'à R937. **En cas de contradiction, [decisions.md](decisions.md) fait foi**, et
> ce qui reste à trancher est dans [questions-ouvertes.md](questions-ouvertes.md).

## 1. Sources utilisées

Les informations ci-dessous proviennent des tâches GRH suivantes :

| ID tâche | Nom                                                                       |
| -------: | ------------------------------------------------------------------------- |
|    #1263 | RPBM - Gestion de stock                                                   |
|    #1269 | RPBM - Valorisation des stock                                             |
|    #2079 | RPBM - Inventaire Stock Marchandises Juin 2026                            |
|     #251 | RPBM - Mise à Jour Statistiques Fichier Stock Rapid Pare-Brise Martinique |

Les fichiers de référence mentionnés sont :

| Fichier                               | Usage                                                         |
| ------------------------------------- | ------------------------------------------------------------- |
| Gestion STOCK V4                      | Fichier principal de suivi du stock                           |
| Onglet STOCK COMPLET                  | Base principale pour les articles, catégories et emplacements |
| Fichier Entrées / Sorties             | Suivi des mouvements de stock                                 |
| Stock théorique inventaire 30/06/2026 | Base théorique utilisée pour l’inventaire                     |
| Stock réel inventaire 30/06/2026      | Résultat physique de l’inventaire                             |

---

# 2. Correspondances de catégories

## 2.1 Catégories cibles validées / proposées

| Catégorie cible Odoo | Sous-types / libellés rattachés                                                                                         |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Pare-brise           | Pare-Brise                                                                                                              |
| Lunette              | Lunette                                                                                                                 |
| Glace latérale       | Glace Latérale, Custode, Déflecteur                                                                                     |
| Joint                | Joint, Enjoliveurs                                                                                                      |
| Main d’œuvre         | Temps MO 1, Temps MO 2                                                                                                  |
| Consommable          | Kit Colle, Gel capteur, Agraphes KIT, Cale Pare-brise, Produit connexe                                                  |
| Film solaire         | Film solaire, Film sécuritaire                                                                                          |
| Autres               | Optique, Rétroviseur, Toit panoramique, Baie de pare-brise, Cache rétro, Rétroviseur ext., Rétroviseur int., Lève-vitre |
| Services             | Frais d’identification, Retraitement des déchets, Nettoyage bris de glace, Frais de déplacement, Pose simple            |
| Accessoires          | Balai essuie-glace                                                                                                      |

---

## 2.2 Correspondance entre les valeurs du fichier et les catégories cibles

Les valeurs suivantes ont été repérées dans la colonne **TYPE** du fichier **Gestion STOCK V4**.

| Valeur trouvée dans le fichier | Catégorie cible recommandée | Remarque migration                                 |
| ------------------------------ | --------------------------- | -------------------------------------------------- |
| PARE BRISE                     | Pare-brise                  | Normaliser en “Pare-Brise”                         |
| PaRE BRISE                     | Pare-brise                  | Typo à corriger                                    |
| PARE-BRISE                     | Pare-brise                  | Normaliser en “Pare-Brise”                         |
| PARE BRISE                     | Pare-brise                  | Supprimer les espaces parasites                    |
| LUNETTES                       | Lunette                     | Normaliser au singulier                            |
| LUNETTES                       | Lunette                     | Supprimer les espaces parasites                    |
| GLACES LATERALES               | Glace latérale              | Normaliser accents / casse                         |
| JOINTS                         | Joint                       | Regrouper avec Joint                               |
| jOINTS                         | Joint                       | Typo à corriger                                    |
| JOINTS                         | Joint                       | Supprimer les espaces parasites                    |
| ENJOLIVEURS                    | Joint                       | Mentionné comme équivalent / rattaché aux joints   |
| TOIT                           | Autres                      | Regrouper avec Toit panoramique                    |
| TOIT                           | Autres                      | Supprimer les espaces parasites                    |
| TOIT PANO                      | Autres                      | Regrouper avec Toit panoramique                    |
| TOIT PANORAMIQUE               | Autres                      | Libellé cible possible                             |
| VITRE PAVILLON                 | Autres                      | À regrouper avec Toit / Toit panoramique           |
| FEU                            | Autres                      | Regrouper avec Optique / Phare                     |
| PHARE                          | Autres                      | Regrouper avec Optique                             |
| PHARES                         | Autres                      | Regrouper avec Optique                             |
| PHARES                         | Autres                      | Supprimer les espaces parasites                    |
| OPTIQUE                        | Autres                      | Libellé cible possible                             |
| OPTIQUES                       | Autres                      | Normaliser au singulier                            |
| ANTIBROUILLARD                 | Autres                      | Regrouper avec Optique / Feu                       |
| FAISCEAU                       | Autres                      | Regrouper avec Optique / Feu selon décision métier |
| RETROVISEUR                    | Autres                      | Renommer en Rétroviseur EXT si extérieur           |
| RETROVISEUR INT                | Autres                      | Conserver comme Rétroviseur INT                    |
| CACHE RETRO                    | Autres                      | Regrouper avec Cache rétro                         |
| CACHE RETRO INT                | Autres                      | Regrouper avec Cache rétro                         |
| LEVE-VITRE                     | Autres                      | Regrouper avec Lève-vitre                          |
| LEVE VITRE                     | Autres                      | Normaliser avec tiret ou accent                    |
| MECANISME LV                   | Autres                      | Regrouper avec Lève-vitre / Mécanisme              |
| MECANISME                      | Autres                      | Regrouper avec Lève-vitre / Mécanisme              |
| BAIE DE PARE BRISE             | Autres                      | Catégorie Autres proposée                          |
| CAMERA                         | Autres                      | À éviter comme catégorie dédiée si rare            |
| AUTRES                         | Autres                      | Conserver en catégorie fourre-tout contrôlée       |
| Valeur vide                    | À traiter                   | Ligne à analyser avant import                      |

---

## 2.3 Règles de normalisation à appliquer

Avant import Odoo, il faut nettoyer les catégories du fichier source.

### Nettoyage de texte

* Supprimer les espaces en début / fin.
* Uniformiser la casse.
* Corriger les fautes de frappe.
* Normaliser les accents.
* Éviter les doublons proches.

### Exemples de regroupements explicitement mentionnés

| Valeurs sources à regrouper                                     | Valeur cible recommandée     |
| --------------------------------------------------------------- | ---------------------------- |
| Toit panoramique, VITRE PAVILLON, TOIT PANO, TOIT               | Toit panoramique             |
| JOINTS, ENJOLIVEURS                                             | Joint / Enjoliveurs          |
| OPTIQUE, OPTIQUES, FAISCEAU, PHARE, PHARES, ANTIBROUILLARD, FEU | Optique / Feu                |
| CACHE RETRO, CACHE RETRO INT                                    | Cache rétro                  |
| LEVE-VITRE, LEVE VITRE, MECANISME LV, MECANISME                 | Lève-vitre                   |
| RETROVISEUR                                                     | Rétroviseur EXT si extérieur |
| RETROVISEUR INT                                                 | Rétroviseur INT              |

---

# 3. Proposition d’arborescence Odoo

Une arborescence de catégories a été proposée pour faciliter le reporting.

```text
Tous
├── Dépenses
├── Ventes
│   ├── Stockable
│   │   ├── Pare-brise
│   │   ├── Lunette
│   │   ├── Glace latérale
│   │   ├── Joint
│   │   ├── Film solaire
│   │   ├── Accessoires
│   │   └── Autres (voir décision du 2026-07-23 ci-dessous : 7 sous-catégories réelles créées sous Autres)
│   ├── Consommables
│   │   ├── Kit colle
│   │   ├── Gel capteur
│   │   ├── Agrafes kit
│   │   ├── Cale pare-brise
│   │   └── Produit connexe
│   └── Services
│       ├── Main d’œuvre
│       ├── Frais d’identification
│       ├── Retraitement des déchets
│       ├── Nettoyage bris de glace
│       ├── Frais de déplacement
│       └── Pose simple
```

**Décision du 2026-07-23** : `Autres` n'est plus une catégorie plate. Sept sous-catégories Odoo réelles (`product.category`) ont été créées en dessous : `Optique`, `Rétroviseur EXT`, `Rétroviseur INT`, `Toit panoramique`, `Cache rétro`, `Lève-vitre`, `Baie de pare-brise`. Seul `CAMERA` reste directement dans `Autres` sans sous-catégorie (article rare, exception explicite du gestionnaire). Détail dans `README.md` (« Analyse du message gestionnaire ») et `categories_odoo_proposition.csv`.

---

# 4. Typologie produit recommandée pour Odoo

## 4.1 Articles stockables

À traiter comme produits stockables :

* Pare-brise
* Lunettes
* Glaces latérales
* Custodes
* Déflecteurs
* Joints
* Enjoliveurs
* Optiques
* Phares
* Feux
* Antibrouillards
* Rétroviseurs
* Toits panoramiques
* Vitres pavillon
* Baies de pare-brise
* Caches rétro
* Lève-vitres
* Accessoires stockés

## 4.2 Consommables

À traiter selon le niveau de suivi souhaité.

Produits candidats :

* Kit colle
* Gel capteur
* Agrafes kit
* Cale pare-brise
* Produit connexe

Décision à prendre :

* soit suivi en stock réel ;
* soit suivi en consommable non valorisé ;
* soit achat / consommation simplifiés sans suivi unitaire strict.

## 4.3 Services

À traiter comme services non stockables :

* Temps MO 1
* Temps MO 2
* Frais d’identification
* Retraitement des déchets
* Nettoyage bris de glace
* Frais de déplacement
* Pose simple

---

# 5. Emplacements utilisés / identifiés

## 5.1 Colonnes et champs sources

| Élément source       | Usage                                                                   |
| -------------------- | ----------------------------------------------------------------------- |
| Onglet STOCK COMPLET | Onglet principal contenant les articles                                 |
| Colonne TYPE         | Catégorie / type d’article                                              |
| Colonne Place        | Emplacement physique de l’article                                       |
| Colonne J            | Filtre utilisé pour isoler les lignes à inventorier, valeur `1`         |
| Colonne T            | Colonne utilisée pour trier les emplacements physiques                  |
| Colonne W            | Colonne ajoutée lors de l’inventaire, nommée `Inventaire du JJ/MM/AA`   |
| Colonne X            | Colonne utilisée pour noter l’article réellement trouvé en cas d’erreur |
| Cellule O4           | Valeur des écarts d’inventaire après filtre                             |

---

## 5.2 Dépôts identifiés

| Dépôt                                  | Description / usage                                        |
| -------------------------------------- | ---------------------------------------------------------- |
| D1                                     | Dépôt Lézarde                                              |
| D2                                     | Second dépôt de stockage                                   |
| Dépôt / rack                           | Zone physique utilisée pour le comptage                    |
| Emplacements type `R101`, `R102`, etc. | Exemples d’emplacements physiques utilisés dans le fichier |

### Mise à jour du 2026-07-23 (retour client)

Le client a précisé l'architecture réelle des dépôts, plus riche que la simple distinction D1/D2 :

- `Galleria` et `Genipa` sont les **entrepôts principaux**.
- `Dépôt 1` et `Dépôt 2` sont des **entrepôts déportés** (et non de simples emplacements sous un entrepôt unique).
- Un nouvel entrepôt `Camion` doit être créé pour les opérations sur site.
- **Décision d'architecture Odoo** : ces 5 dépôts seront modélisés comme **5 `stock.warehouse` distincts**, chacun avec ses propres emplacements Stock/Input/Output — pas comme des emplacements imbriqués sous l'entrepôt unique `RPBM` déjà en place. Cela implique une restructuration de l'existant en préproduction, où `D1`/`D2` existent déjà comme emplacements sous `RPBM` (434 emplacements) : à traiter avec prudence, pas en écriture directe non contrôlée.
- Répartition tranchée par le client le **2026-08-05** : `R101` à `R336` → Dépôt 1, `R401` à `R937` → Dépôt 2, `J…`/`T…` → Dépôt 2. Les bornes tombent exactement sur la frontière réelle des blocs. La numérotation `R` compte **9 blocs** par allée (`R1xx` 101-136, `R2xx` 201-236, `R3xx` 301-336, `R4xx` 401-436, `R5xx` 501-538, `R6xx` 601-642, `R7xx` 701-739, `R8xx` 801-837, `R9xx` 900-937), et non 7 s'arrêtant à `R728` comme indiqué dans les versions antérieures de ce document. Les 49 valeurs non couvertes (cellules multi-racks, libellés non codifiés, statuts) restent sous `A controler`.
- Règle actée : un emplacement Odoo par référence distincte de la colonne `Place` (pas de regroupement par plage de racks).
- Reste à définir : usage exact de l'entrepôt `Camion`, et les routes de transfert inter-entrepôts pour le réapprovisionnement de `Galleria`/`Genipa` depuis `Dépôt 1`/`Dépôt 2` lors d'une vente.

---

## 5.3 Informations opérationnelles sur les dépôts

### D1 — Dépôt Lézarde

Informations connues :

* dépôt utilisé pour le stockage physique ;
* inventaire réalisé rack par rack ;
* les emplacements doivent être triés pour suivre l’ordre pratique de comptage ;
* accès physique encadré par clés disponibles auprès des personnes habilitées ;
* présence d’un réseau Wi-Fi dépôt mentionnée dans la procédure interne.

> Note migration : les informations d’accès physique et réseau ne doivent pas être reprises dans les imports Odoo. Elles relèvent d’une procédure interne d’inventaire, pas du référentiel stock.

### D2 — Second dépôt

Informations connues :

* la même procédure d’inventaire que D1 doit être appliquée ;
* absence de Wi-Fi dédié mentionnée ;
* connexion possible via partage de connexion ;
* prise secteur disponible à l’entrée sur la gauche ;
* clés disponibles auprès des collaborateurs.

> Note migration : D2 doit probablement être créé comme emplacement interne distinct dans Odoo.

> **Mise à jour du 2026-07-23** : cette note est dépassée par la décision d'architecture ci-dessus (§5.2) — D2 devient un entrepôt (`stock.warehouse`) autonome, pas un simple emplacement interne.

---

# 6. Proposition de modélisation des emplacements dans Odoo

## 6.1 Structure minimale recommandée (obsolète, voir décision du 2026-07-23 en §5.2)

```text
RPBM / Stock
├── D1 - Dépôt Lézarde
│   ├── R101
│   ├── R102
│   ├── ...
│   └── À compléter depuis la colonne Place
└── D2 - Dépôt 2
    ├── Rxxx
    ├── ...
    └── À compléter depuis la colonne Place
```

Cette structure traitait D1/D2 comme des emplacements sous un entrepôt unique `RPBM`. Elle est remplacée par 5 entrepôts Odoo distincts (`Galleria`, `Genipa`, `Dépôt 1`, `Dépôt 2`, `Camion`), chacun avec sa propre arborescence d'emplacements internes.

## 6.2 Règles d’import des emplacements

| Donnée source      | Donnée cible Odoo                          |
| ------------------ | ------------------------------------------ |
| Place              | stock.location complet ou sous-emplacement |
| D1 / D2            | entrepôt (`stock.warehouse`) autonome, plus emplacement parent |
| R101, R102, etc.   | sous-emplacement physique, un par référence distincte (pas de regroupement par plage) |
| Article + Place    | quant initial / stock.quant à importer     |
| Article sans Place | à mettre en anomalie avant import          |
| Place inconnue     | emplacement temporaire `À contrôler`       |

---

# 7. Données d’inventaire utiles à la migration

## 7.1 Inventaire au 30/06/2026

| Indicateur      |      Montant |
| --------------- | -----------: |
| Stock théorique | 106 745,23 € |
| Stock réel      | 100 297,05 € |
| Écart           |   6 448,18 € |

## 7.2 Statuts utilisés dans le fichier

| Couleur / statut | Signification                            | Traitement cible Odoo                                              |
| ---------------- | ---------------------------------------- | ------------------------------------------------------------------ |
| Rouge            | Vendu                                    | Ne doit pas être importé comme stock disponible                    |
| Orange           | Réservé                                  | À transformer en réservation ou stock bloqué selon processus cible |
| Jaune            | Cassé                                    | À sortir, rebuter ou placer en emplacement de casse                |
| OK               | Comptage physique conforme               | Peut être importé comme stock initial fiable                       |
| Pas là           | Article théorique absent physiquement    | À exclure ou investiguer avant import                              |
| ERREUR           | Article différent ou mauvais emplacement | À corriger avant import                                            |

---

# 8. Règles de préparation avant import

## 8.1 Nettoyage des articles

Avant import Odoo, il faut :

* supprimer ou corriger les lignes sans nom d’article ;
* identifier les doublons ;
* normaliser les références ;
* nettoyer les catégories ;
* vérifier les prix publics ;
* vérifier les prix d’achat ;
* vérifier les emplacements ;
* distinguer les articles stockables, consommables et services ;
* isoler les articles vendus, cassés ou réservés.

## 8.2 Nettoyage des catégories

À faire :

* appliquer la table de correspondance des catégories ;
* supprimer les catégories inutiles ou trop rares ;
* éviter la création de catégories trop spécifiques ;
* conserver une catégorie `Autres` maîtrisée ;
* valider les cas ambigus avec RPBM.

Cas ambigu mentionné :

* `CAMERA` : ne pas créer une catégorie dédiée si l’article est rare ; rattacher à `Autres`.

## 8.3 Nettoyage des emplacements

À faire :

* extraire toutes les valeurs distinctes de la colonne `Place` ;
* séparer les dépôts D1 / D2 si l’information est disponible ;
* normaliser les codes d’emplacement ;
* identifier les emplacements vides ;
* identifier les emplacements incohérents ;
* créer un emplacement temporaire `À contrôler` pour les cas non résolus ;
* vérifier les emplacements à partir du dernier inventaire réel.

---

# 9. Paramétrage stock / comptable utile

La tâche de valorisation du stock indique que les catégories valorisées doivent être configurées avec :

| Paramètre              | Valeur / remarque                               |
| ---------------------- | ----------------------------------------------- |
| Méthode de coût        | FIFO ou AVCO                                    |
| Valorisation           | Manuelle ou automatisée                         |
| Compte de valorisation | À créer / valider avec le responsable comptable |
| Compte d’entrée stock  | À créer / valider                               |
| Compte de sortie stock | À créer / valider                               |
| Coûts logistiques      | À appliquer aux bons transferts                 |

Point d’attention :

> Si la valorisation automatique est activée, chaque entrée ou sortie de stock peut générer une écriture comptable. La configuration doit être validée comptablement avant migration.

---

# 10. Flux cible à préparer pour Odoo

## 10.1 Entrées de stock

Objectif cible :

* réception fournisseur = entrée automatique en stock ;
* mise à jour de la quantité disponible ;
* affectation à un emplacement physique ;
* valorisation éventuelle du stock ;
* prise en compte des coûts logistiques si applicable.

## 10.2 Sorties de stock

Objectif cible :

* vente / livraison = sortie de stock ;
* éviter les ventes sans sortie physique ;
* éviter les sorties physiques sans vente ;
* rendre l’étape livraison obligatoire pour les articles stockables ;
* ne pas bloquer les factures composées uniquement de main-d’œuvre.

## 10.3 Réservations

Le fichier utilise actuellement le statut `Réservé`.

Dans Odoo, il faudra décider si ce statut devient :

* une réservation de stock via commande client ;
* un emplacement interne `Réservé` ;
* un statut custom ;
* ou un processus standard basé sur devis / commande / livraison.

## 10.4 Casse

Le fichier utilise actuellement le statut `Cassé`.

Dans Odoo, il faudra décider si les articles cassés sont :

* sortis via rebut ;
* déplacés vers un emplacement `Casse` ;
* conservés en stock non disponible ;
* valorisés ou dévalorisés selon décision comptable.

---

# 11. Anomalies à contrôler avant migration

| Anomalie                              | Risque                               | Action recommandée               |
| ------------------------------------- | ------------------------------------ | -------------------------------- |
| Ligne sans nom d’article              | Import impossible ou article inutile | Exclure ou corriger              |
| Catégorie vide                        | Mauvais reporting                    | Affecter une catégorie cible     |
| Catégorie avec typo                   | Doublons de catégories               | Normaliser                       |
| Article vendu encore disponible       | Stock surévalué                      | Exclure du stock initial         |
| Article réservé                       | Quantité disponible fausse           | Créer réservation / stock bloqué |
| Article cassé                         | Stock disponible faux                | Rebut ou emplacement casse       |
| Emplacement vide                      | Stock difficile à retrouver          | Affecter à `À contrôler`         |
| Mauvais emplacement                   | Erreurs opérationnelles              | Corriger via inventaire          |
| Article théorique absent physiquement | Stock surévalué                      | Exclure ou investiguer           |
| Article physique absent du fichier    | Stock sous-évalué                    | Ajouter après validation         |
| Doublon produit                       | Mauvaise disponibilité               | Fusionner / normaliser           |

---

# 12. Recommandation de fichiers de travail pour la migration

## 12.1 Fichier `categories_mapping.csv`

Colonnes recommandées :

```text
source_type,target_category,target_subcategory,product_type,stockable,notes
```

Exemple :

```text
PARE BRISE,Pare-brise,,stockable,true,Normalisation casse
PaRE BRISE,Pare-brise,,stockable,true,Typo source
ENJOLIVEURS,Joint,Enjoliveurs,stockable,true,Rattaché aux joints
TEMPS MO 1,Main d’œuvre,,service,false,Service non stockable
KIT COLLE,Consommable,Kit colle,consumable,true,A confirmer selon suivi souhaité
```

## 12.2 Fichier `locations_mapping.csv`

Colonnes recommandées :

```text
source_place,warehouse,location_parent,location_name,location_complete_name,notes
```

Exemple :

```text
R101,D1,D1 - Dépôt Lézarde,R101,RPBM / Stock / D1 - Dépôt Lézarde / R101,Exemple mentionné dans procédure
R102,D1,D1 - Dépôt Lézarde,R102,RPBM / Stock / D1 - Dépôt Lézarde / R102,Exemple mentionné dans procédure
```

## 12.3 Fichier `initial_stock_import.csv`

Colonnes recommandées :

```text
product_reference,product_name,category,location,quantity,cost,public_price,status,inventory_status,notes
```

Statuts à prévoir :

```text
available
reserved
sold
broken
missing
error
to_check
```

---

# 13. Décisions métier à obtenir avant migration

Avant migration dans Odoo, il faudra valider :

1. ~~La liste finale des catégories.~~ → largement tranché le 2026-07-23 (architecture validée, sous-catégories sous `Autres` créées, cf. §3). Reste ouvert : confirmer que `Accessoires` et `Main d'Oeuvre` (déjà existantes sous `All / Saleable`) doivent être réutilisées telles quelles.
2. Le rattachement exact des anciennes valeurs `TYPE`.
3. Le traitement des consommables.
4. Le traitement des articles cassés.
5. Le traitement des articles réservés.
6. Le traitement des articles vendus mais encore présents dans le fichier.
7. ~~La structure exacte des dépôts D1 / D2.~~ → tranché le 2026-07-23 : 5 entrepôts Odoo distincts (`Galleria`, `Genipa`, `Dépôt 1`, `Dépôt 2`, `Camion`). ~~Répartition des blocs de racks entre Dépôt 1 et Dépôt 2.~~ → tranchée le 2026-08-05 (voir §5.2). Reste ouvert : migration des emplacements `D1`/`D2` déjà existants en préproduction, et sort des 49 emplacements laissés sous `A controler`.
8. ~~La règle de création des emplacements depuis la colonne `Place`.~~ → tranché le 2026-07-23 : un emplacement Odoo par référence distincte (pas de regroupement par plage).
9. La méthode de coût : FIFO ou AVCO.
10. Le type de valorisation : manuelle ou automatisée.
11. Les comptes comptables de stock.
12. La date de référence du stock initial.
13. La source à considérer comme fiable : stock théorique, stock réel ou fichier V4 corrigé.
14. Le traitement de l’écart d’inventaire du 30/06/2026.
15. Les droits utilisateurs sur les mouvements de stock.

---

# 14. Synthèse migration

La migration stock RPBM devra s’appuyer sur trois axes :

1. **Référentiel articles**

   * nettoyage des noms ;
   * nettoyage des catégories ;
   * distinction stockable / consommable / service.

2. **Référentiel emplacements**

   * reprise de la colonne `Place` ;
   * structuration par dépôt D1 / D2 ;
   * création des sous-emplacements physiques.

3. **Stock initial**

   * reprise depuis l’inventaire réel ;
   * exclusion ou traitement des articles vendus, réservés, cassés, absents ou en erreur ;
   * valorisation après validation comptable.
