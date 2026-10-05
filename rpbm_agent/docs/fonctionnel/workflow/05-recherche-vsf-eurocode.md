# 5 — Recherche VSF par eurocode

- **Déclencheur** : sur le dialog du devis, automatique dès que `state.baseEurocode` change (déduit à l'étape précédente, ou saisi/corrigé manuellement par l'utilisateur).
- **Code** : `onSearchBaseEurocode()` (`agent_widget_dialog.js`).
- **Route** : `POST /searchBaseEurocode` (`main.py::searchBaseEurocode`) → `vsfAgent.searchEurocodeArticlesClient(baseEurocode)`, retourne la liste des `VSFArticle` correspondants.

Cette étape n'existe que sur le devis (lot E1) : le dialog de l'opportunité s'arrête à la base Eurocode, qui reste saisissable, et la recherche s'y fait après « Créer un devis » ([6](06-confirmation-crm-lead.md), [7](07-confirmation-sale-order.md)).

Aucun champ Odoo n'est lu ou écrit à cette étape : la recherche externe VSF reste dans l'état local (`state.articlesVsf`). La sélection est multiple : un second clic sur la ligne désélectionne l'article ; désélectionner un article principal retire aussi ses suggestions sélectionnées. La sélection d'un principal enrichit ses suggestions à partir de leurs fiches VSF (lues en parallèle) avant affichage, sans les ajouter à la liste des résultats principaux.

Les résultats s'affichent dans un tableau, une ligne par article, dans le dialogue en plein écran
(R21, R22) :

| Colonne | Contenu |
|---|---|
| Eurocode | code VSF complet, en police à chasse fixe |
| Désignation | désignation VSF, suivie du lien « Fiche technique » (nouvel onglet) |
| Réf. constructeur | référence du constructeur |
| Stock | quantité en stock, ou « Indisponible » |
| Prix | prix de vente VSF |
| Coût | prix de vente VSF diminué de la remise RPBM |
| Photo | première vignette de l'article |

Le code VSF est l'eurocode complet : ses caractères tombent dans les mêmes colonnes d'une ligne à
l'autre, sans séparation ajoutée entre les rangs.

Un clic sur une ligne sélectionne ou désélectionne l'article ; la ligne sélectionnée est
surlignée. Une ligne de détail s'ouvre alors juste en dessous, avec toutes les vignettes de
l'article, ses caractéristiques techniques (ou « Détails VSF indisponibles » si sa fiche n'a pas
pu être lue) et ses actions de produit Odoo. Les « Articles suggérés par VSF » d'un article
sélectionné suivent sa ligne de détail : une ligne de légende, puis une ligne par suggestion,
sélectionnable de la même façon et groupée avec l'article.

À côté de « Rechercher sur VSF », « Ouvrir dans un nouvel onglet » ouvre le catalogue VSF
sur la valeur courante du champ, même si elle n'a pas encore été recherchée dans le widget.
Le lien est désactivé lorsque le champ est vide ou ne contient que des espaces. Il utilise
la session VSF du navigateur ; si nécessaire, VSF demande une connexion avant de revenir
à la recherche. La saisie seule ne déclenche pas de recherche à chaque caractère. Sur l'opportunité, le lien reste, sans bouton de recherche à côté.

Chaque vignette reçue dès la recherche associe la miniature à son URL VSF plein format signée.
La colonne Photo n'affiche que la première ; la ligne de détail les affiche toutes. Un clic simple
ouvre l'aperçu interne ; tout clic modifié garde le comportement natif sans sélectionner la ligne
(Ctrl/Cmd-clic ou clic central ouvre l'image dans un nouvel onglet). Le lien « Fiche technique »
ne sélectionne pas non plus la ligne ; son URL VSF est complète dès la recherche. Les flèches ← et →
font défiler en boucle les seules photos de l'article dans l'aperçu, quelle que soit la vignette
ouverte ; les photos du modèle sont exclues. Recette live du tableau, qui reprend R15 à R17, réussie
le 2026-10-05 sur le build `6cbecd3` : voir le [jeu de test](../../jeu-de-test.md#tableau-vsf-en-plein-écran-r21-r22-reprise-de-r15-à-r17).

Chaque article sélectionné garde ses propres actions de produit Odoo, dans sa ligne de détail. Sur un devis, l'ajout et le retrait sont indépendants par article ; le retrait ne concerne que la ligne de devis ajoutée par le widget pendant la dialog courante.

Sur le devis, la base Eurocode restaurée depuis l'enregistrement relance la recherche VSF à la
réouverture, dès que la pièce mémorisée est retrouvée. Sinon, la base reste affichée et la
recherche se lance par « Rechercher sur VSF ». Elle est écrite dans le formulaire lors de la confirmation ; son
effacement suit la désélection de la pièce principale.

Suivant, selon le modèle porteur : [6 — Confirmation sur Piste/Opportunité](06-confirmation-crm-lead.md) ou [7 — Confirmation sur Ordre de Vente](07-confirmation-sale-order.md).
