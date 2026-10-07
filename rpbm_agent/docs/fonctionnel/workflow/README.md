# Parcours — étape par étape

Le parcours utilisateur complet (voir [vue narrative avec diagrammes](../parcours-utilisateur.md)) découpé en 9 étapes séquentielles, chacune documentant précisément la route Odoo appelée et les champs lus/écrits. Détail des champs par modèle : [technique/champs/](../../technique/champs/README.md).

1. [Recherche véhicule par immatriculation](01-recherche-immatriculation.md)
2. [Sélection du véhicule](02-selection-vehicule.md)
3. [Catégorie X'Glass (calque)](03-categorie-xglass.md)
4. [Pièce et pièce après-marché (déduction eurocode)](04-piece-piece-am.md)
5. [Recherche VSF par eurocode](05-recherche-vsf-eurocode.md) (devis seulement)
6. [Confirmation sur Piste/Opportunité (`crm.lead`)](06-confirmation-crm-lead.md), avec le bouton « Créer un devis »
7. [Confirmation sur Ordre de Vente (`sale.order`)](07-confirmation-sale-order.md), avec l'ouverture automatique après « Créer un devis » et le devis sans X'Glass (lot E2)
8. [Création du véhicule (`fleet.vehicle`)](08-creation-vehicule.md)
9. [Création du produit (`product.product`)](09-creation-produit.md)

Les étapes 1 à 4 sont communes aux deux modèles porteurs. Depuis le lot E1, l'opportunité s'arrête à la base Eurocode : la recherche VSF (5) et la création du produit (9) n'existent que sur le devis, que l'opportunité crée par « Créer un devis » (6) et dont le dialog s'ouvre alors seul (7). Depuis le lot E2, le devis commence par l'étape 5 (recherche VSF immédiate, encart « Dossier ») : les étapes 1 à 4 ne partent qu'après « Charger X'Glass ». Seule la main-d'œuvre (section « 4. Main d'œuvre X'Glass » du devis) y échappe depuis le correctif du 2026-10-07 : enregistrée à l'opportunité (6), elle est proposée dès l'ouverture (7). 6/7 divergent selon le modèle sur lequel le widget est ouvert ; 8/9 sont déclenchées depuis les étapes précédentes (pas des clics utilisateur séparés dans le fil principal).
