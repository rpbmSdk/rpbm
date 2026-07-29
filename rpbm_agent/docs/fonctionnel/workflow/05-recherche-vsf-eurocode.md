# 5 — Recherche VSF par eurocode

- **Déclencheur** : automatique dès que `state.baseEurocode` change (déduit à l'étape précédente, ou saisi/corrigé manuellement par l'utilisateur).
- **Code** : `onSearchBaseEurocode()` (`agent_widget_dialog.js`).
- **Route** : `POST /searchBaseEurocode` (`main.py::searchBaseEurocode`) → `vsfAgent.searchEurocodeArticlesClient(baseEurocode)`, retourne la liste des `VSFArticle` correspondants.

Aucun champ Odoo n'est lu ou écrit à cette étape : la recherche externe VSF reste dans l'état local (`state.articlesVsf`). La sélection est multiple : un second clic désélectionne une carte ; désélectionner un article principal retire aussi ses suggestions sélectionnées. La sélection d'un principal enrichit ses suggestions à partir de leurs fiches VSF avant affichage, sans les ajouter à la liste des résultats principaux.

Chaque carte sélectionnée garde ses propres actions de produit Odoo. Sur un devis, l'ajout et le retrait sont indépendants par article ; le retrait ne concerne que la ligne ajoutée par le widget pendant la dialog courante.

Suivant, selon le modèle porteur : [6 — Confirmation sur Piste/Opportunité](06-confirmation-crm-lead.md) ou [7 — Confirmation sur Ordre de Vente](07-confirmation-sale-order.md).
