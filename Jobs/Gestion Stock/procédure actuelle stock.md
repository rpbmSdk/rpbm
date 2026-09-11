# Procédure actuelle de gestion du stock RPBM

## 1. Principe général

La gestion du stock RPBM repose actuellement principalement sur des fichiers Google Sheets.

Les fichiers de référence sont :

* **Gestion STOCK V4** : fichier principal de suivi du stock.
* **Fichier Entrées / Sorties** : fichier de suivi des mouvements.
* **Fichiers d’inventaire** : fichiers ponctuels permettant de comparer le stock théorique au stock réel.

Odoo sert aujourd’hui de référence pour les ventes, mais la gestion opérationnelle des mouvements physiques reste majoritairement suivie dans les fichiers.

---

## 2. Fichier principal de suivi : Gestion STOCK V4

Le fichier **Gestion STOCK V4** permet de suivre les articles en stock, leur état et leur emplacement.

### Légende utilisée

| Couleur | Signification |
| ------- | ------------- |
| Rouge   | Vendu         |
| Orange  | Réservé       |
| Jaune   | Cassé         |

Ce fichier est la base principale pour :

* suivre les articles disponibles ;
* identifier les articles vendus, réservés ou cassés ;
* préparer les inventaires ;
* analyser les écarts ;
* préparer les réapprovisionnements.

---

## 3. Suivi régulier du stock

Le suivi courant consiste à rapprocher régulièrement deux sources :

1. les ventes réalisées dans Odoo ;
2. les sorties indiquées dans le fichier de stock.

Ce contrôle doit être réalisé environ **tous les deux jours**.

### Contrôle depuis Odoo vers le fichier stock

Pour chaque vente Odoo :

1. Identifier l’article vendu.
2. Rechercher l’article correspondant dans le fichier **Gestion STOCK V4**.
3. Vérifier qu’une sortie de stock a bien été indiquée.
4. Vérifier que l’article est correctement marqué comme vendu.
5. Vérifier que la référence et l’emplacement correspondent.

### Contrôle depuis le fichier stock vers Odoo

Pour chaque sortie indiquée dans le fichier stock :

1. Identifier l’article sorti.
2. Rechercher la vente correspondante dans Odoo.
3. Vérifier que la sortie est justifiée par une vente.
4. Identifier les éventuelles sorties non justifiées.

### Écarts à investiguer

Les cas suivants doivent être analysés :

* article vendu dans Odoo mais non sorti du fichier stock ;
* article sorti du fichier stock mais sans vente Odoo correspondante ;
* article physiquement sorti mais non remis en stock ;
* article réservé mais finalement non vendu ;
* erreur de référence ;
* erreur d’emplacement ;
* doublon ou incohérence dans le fichier.

---

## 4. Inventaires globaux

Deux inventaires globaux sont prévus chaque année.

### Inventaire fiscal de clôture

Cet inventaire doit être réalisé :

* après le dernier jour d’activité de l’année ;
* avant le premier jour d’activité de l’année suivante.

Il permet de déterminer la valeur du stock à intégrer au bilan de clôture.

### Inventaire intermédiaire du 30 juin

Cet inventaire permet d’établir la situation intermédiaire du stock au 30 juin.

Il sert notamment à :

* comparer le stock théorique et le stock réel ;
* mesurer les écarts ;
* corriger les erreurs ;
* fiabiliser les données avant la suite de l’exercice.

---

## 5. Sondages d’inventaire

En complément des inventaires globaux, des sondages doivent être réalisés régulièrement, au minimum **une fois par trimestre**.

L’objectif est de vérifier la fiabilité du stock sans attendre l’inventaire complet.

Deux méthodes sont utilisées.

---

## 6. Méthode 1 : book to physical

La méthode **book to physical** consiste à partir du stock théorique pour vérifier le stock physique.

### Étapes

1. Ouvrir le fichier **Gestion STOCK V4**.
2. Sélectionner environ 20 à 25 références significatives en valeur.
3. Rechercher physiquement ces références dans le dépôt.
4. Comparer le stock physique avec le stock théorique.
5. Noter les écarts constatés.
6. Formaliser les résultats du contrôle.

### Objectif

Cette méthode permet de vérifier que les articles indiqués dans le fichier existent réellement dans le dépôt.

---

## 7. Méthode 2 : physical to book

La méthode **physical to book** consiste à partir du dépôt physique pour vérifier le fichier théorique.

### Étapes

1. Se rendre dans le dépôt.
2. Choisir des articles physiquement présents, à l’aveugle.
3. Rechercher ces articles dans le fichier **Gestion STOCK V4**.
4. Vérifier que les références existent bien dans le stock théorique.
5. Vérifier que les emplacements sont corrects.
6. Noter les écarts constatés.
7. Formaliser les résultats.

### Objectif

Cette méthode permet d’identifier les articles présents physiquement mais absents ou mal renseignés dans le fichier de stock.

---

## 8. Déclenchement d’un inventaire anticipé

Si les sondages révèlent un niveau d’erreur important, un inventaire global anticipé peut être déclenché.

Les critères d’alerte peuvent être :

* écart financier significatif ;
* écart quantitatif important ;
* erreurs répétées d’emplacement ;
* articles présents physiquement mais absents du fichier ;
* articles absents physiquement mais présents dans le fichier ;
* incohérences récurrentes entre Odoo et le fichier stock.

---

## 9. Procédure d’inventaire physique

### Préparation du fichier

1. Mettre à jour le fichier **Gestion STOCK V4** avec toutes les dernières entrées et sorties.
2. Se placer dans une vue filtrée couvrant l’ensemble du fichier.
3. Vérifier que la plage filtrée inclut bien toutes les lignes du fichier.
4. Filtrer les articles à inventorier.
5. Trier les lignes par emplacement physique afin de faciliter le comptage.
6. Insérer une colonne dédiée à l’inventaire, par exemple :
   **Inventaire du JJ/MM/AA**.

### Organisation du comptage

Le comptage doit être réalisé à deux personnes :

* une personne devant le fichier ;
* une personne devant les racks.

La personne devant le fichier annonce l’emplacement à contrôler.

La personne devant le rack vérifie physiquement l’article et transmet le résultat.

### Valeurs à renseigner

| Valeur | Signification                                                                                     |
| ------ | ------------------------------------------------------------------------------------------------- |
| OK     | Le stock physique correspond au fichier                                                           |
| Pas là | L’article indiqué dans le fichier n’est pas trouvé physiquement                                   |
| ERREUR | L’article trouvé ne correspond pas à celui indiqué dans le fichier ou l’emplacement est incorrect |

### En cas d’erreur

Lorsqu’une erreur est constatée, il faut renseigner :

* l’article trouvé physiquement ;
* son Eurocode ;
* son emplacement réel ;
* la différence avec l’emplacement indiqué dans le fichier.

---

## 10. Dépôts concernés

La procédure s’applique aux deux dépôts :

* **D1**
* **D2**

La même méthode de comptage doit être appliquée pour chaque dépôt.

---

## 11. Traitement des écarts d’inventaire

Après l’inventaire :

1. Filtrer les lignes marquées **Pas là**.
2. Filtrer les lignes marquées **ERREUR**.
3. Valoriser les écarts.
4. Reporter la valeur des écarts dans la fiche Odoo d’inventaire.
5. Analyser chaque écart.
6. Corriger les données lorsque cela est possible.

### Typologies d’écarts

Les écarts peuvent correspondre à plusieurs situations :

* article mal positionné dans le dépôt ;
* emplacement incorrect dans le fichier ;
* article présent physiquement mais absent du stock théorique ;
* article présent dans le stock théorique mais absent physiquement ;
* vente Odoo non répercutée dans le fichier stock ;
* sortie physique non justifiée par une vente ;
* article cassé non correctement identifié ;
* article réservé non correctement suivi ;
* erreur de saisie ;
* doublon ou incohérence de référence.

---

## 12. Corrections possibles

Selon le type d’écart, les corrections peuvent être les suivantes :

### Correction d’emplacement

Si l’article est présent physiquement mais à un autre emplacement :

1. Mettre à jour l’emplacement dans le fichier.
2. Noter l’erreur constatée.
3. Vérifier si d’autres articles sont concernés par le même problème.

### Article présent physiquement mais absent du fichier

1. Rechercher l’origine de l’article.
2. Vérifier les achats ou réceptions.
3. Vérifier les ventes Odoo.
4. Ajouter ou corriger la ligne dans le fichier si nécessaire.

### Article présent dans le fichier mais absent physiquement

1. Rechercher une vente Odoo correspondante.
2. Vérifier si l’article a été sorti mais non marqué comme vendu.
3. Vérifier s’il a été cassé, déplacé ou réservé.
4. Sortir l’article du stock si la vente ou la sortie est confirmée.

### Article vendu mais non sorti du stock

1. Identifier la vente Odoo.
2. Retrouver la référence concernée.
3. Mettre à jour le fichier stock.
4. Marquer l’article comme vendu.

### Article sorti mais non vendu

1. Identifier la personne ou l’opération à l’origine de la sortie.
2. Vérifier s’il s’agit d’une réservation, d’une casse ou d’une erreur.
3. Remettre l’article en stock si nécessaire.
4. Corriger le fichier.

---

## 13. Réapprovisionnement

Le fichier **Gestion STOCK V4** contient également un onglet de propositions de réapprovisionnement basé sur les statistiques VSF.

La logique indiquée est :

| Mode de livraison | Couverture cible |
| ----------------- | ---------------- |
| Avion             | 1 mois           |
| Bateau            | 3 mois           |

Cette partie permet d’aider à préparer les commandes de réapprovisionnement.

---

## 14. Limites de la procédure actuelle

La procédure actuelle présente plusieurs limites :

* gestion encore très manuelle ;
* double suivi entre Odoo et Google Sheets ;
* risque d’oubli de sortie ;
* risque d’erreur de saisie ;
* risque d’erreur d’emplacement ;
* difficulté à fiabiliser les réservations ;
* difficulté à suivre les articles cassés ;
* dépendance forte au fichier **Gestion STOCK V4** ;
* nécessité de contrôles fréquents pour garantir la fiabilité du stock.

---

## 15. Objectif cible avec Odoo

La bascule vers Odoo doit permettre de fiabiliser la gestion du stock.

Les objectifs principaux sont :

* automatiser les entrées de stock à la réception des commandes ;
* automatiser les sorties de stock lors des livraisons ou ventes ;
* fiabiliser les emplacements ;
* limiter les manipulations manuelles ;
* réduire les erreurs de double saisie ;
* suivre les réservations ;
* suivre les articles cassés ;
* faciliter les inventaires ;
* historiser les mouvements ;
* rapprocher automatiquement les ventes, livraisons et mouvements de stock.

---

## 16. Points d’attention pour la migration vers Odoo

Pour préparer la migration, il faudra notamment traiter les points suivants :

* nettoyer les références articles ;
* identifier les doublons ;
* normaliser les catégories ;
* distinguer les articles stockables, les consommables et les services ;
* importer les emplacements physiques ;
* importer le stock initial fiable ;
* définir les règles de sortie lors des ventes ;
* définir les règles d’entrée lors des réceptions ;
* gérer les réservations ;
* gérer les articles cassés ;
* définir les droits utilisateurs ;
* définir les contrôles d’inventaire ;
* reprendre la valorisation du stock ;
* valider le paramétrage comptable avec le responsable comptable.
