# 5 — Recherche VSF par eurocode

- **Déclencheur** : automatique dès que `state.baseEurocode` change (déduit à l'étape précédente, ou saisi/corrigé manuellement par l'utilisateur).
- **Code** : `onSearchBaseEurocode()` (`agent_widget_dialog.js`).
- **Route** : `POST /searchBaseEurocode` (`main.py::searchBaseEurocode`) → `vsfAgent.searchEurocodeArticlesClient(baseEurocode)`, retourne la liste des `VSFArticle` correspondants.

Aucun champ Odoo n'est lu ou écrit à cette étape : la recherche externe VSF reste dans l'état local (`state.articlesVsf`). La sélection est multiple : un second clic désélectionne une carte ; désélectionner un article principal retire aussi ses suggestions sélectionnées. La sélection d'un principal enrichit ses suggestions à partir de leurs fiches VSF (lues en parallèle) avant affichage, sans les ajouter à la liste des résultats principaux.

Les résultats et les « Articles suggérés par VSF » s'affichent sur une seule colonne. Le titre
contient la désignation seule ; la ligne « Eurocode : … », en police à chasse fixe, précède
« Référence constructeur ». Le code VSF est l'eurocode complet : les caractères restent
alignés d'une carte à l'autre, sans séparation ajoutée entre les rangs.

À côté de « Rechercher sur VSF », « Ouvrir dans un nouvel onglet » ouvre le catalogue VSF
sur la valeur courante du champ, même si elle n'a pas encore été recherchée dans le widget.
Le lien est désactivé lorsque le champ est vide ou ne contient que des espaces. Il utilise
la session VSF du navigateur ; si nécessaire, VSF demande une connexion avant de revenir
à la recherche. La saisie seule ne déclenche pas de recherche à chaque caractère.

Chaque vignette reçue dès la recherche associe la miniature à son URL VSF plein format signée.
Un clic simple ouvre l'aperçu interne ; tout clic modifié garde le comportement natif sans
sélectionner la carte (Ctrl/Cmd-clic ou clic central ouvre l'image dans un nouvel onglet). Les flèches ← et →
font défiler en boucle les seules photos de l'article dans l'aperçu ; les photos du modèle sont
exclues. La recette live R16/R17 reste ouverte.

Chaque carte sélectionnée garde ses propres actions de produit Odoo. Sur un devis, l'ajout et le retrait sont indépendants par article ; le retrait ne concerne que la ligne ajoutée par le widget pendant la dialog courante.

La base Eurocode restaurée depuis l'enregistrement relance la recherche VSF à la
réouverture, dès que la pièce mémorisée est retrouvée. Sinon, la base reste affichée et la
recherche se lance par « Rechercher sur VSF ». Elle est écrite dans le formulaire lors de la confirmation ; son
effacement suit la désélection de la pièce principale.

Suivant, selon le modèle porteur : [6 — Confirmation sur Piste/Opportunité](06-confirmation-crm-lead.md) ou [7 — Confirmation sur Ordre de Vente](07-confirmation-sale-order.md).
