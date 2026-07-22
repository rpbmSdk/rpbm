# 5 — Recherche VSF par eurocode

- **Déclencheur** : automatique dès que `state.baseEurocode` change (déduit à l'étape précédente, ou saisi/corrigé manuellement par l'utilisateur).
- **Code** : `onSearchBaseEurocode()` (`agent_widget_dialog.js`).
- **Route** : `POST /searchBaseEurocode` (`main.py::searchBaseEurocode`) → `vsfAgent.searchEurocodeArticlesClient(baseEurocode)`, retourne la liste des `VSFArticle` correspondants.

Aucun champ Odoo lu ou écrit à cette étape — recherche externe (VSF) uniquement, résultat stocké en état local (`state.articlesVsf`). L'utilisateur sélectionne ensuite un article dans la liste (pas d'écriture Odoo à ce clic non plus).

Suivant, selon le modèle porteur : [6 — Confirmation sur Piste/Opportunité](06-confirmation-crm-lead.md) ou [7 — Confirmation sur Ordre de Vente](07-confirmation-sale-order.md).
