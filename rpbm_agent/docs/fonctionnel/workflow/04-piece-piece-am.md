# 4 — Pièce et pièce après-marché (déduction eurocode)

- **Déclencheur** : clic utilisateur sur une pièce de la catégorie.
- **Code** : `onSelectPiece()` → `getSelectedPieceAm()`/`getPieceAm()` (`agent_widget_dialog.js`).
- **Route** : `POST /getPieceAm` (`main.py::getPieceAm`) → pièces après-marché correspondantes sur X'Glass.
- **Déduction eurocode** : si des pièces après-marché sont trouvées, `state.baseEurocode` (état widget, pas encore un champ Odoo) est déduit automatiquement comme les 5 premiers caractères de la référence de la première pièce après-marché ; sinon le champ reste vide pour saisie manuelle.

Aucun champ Odoo lu ou écrit à cette étape — uniquement de l'état widget local, qui alimentera l'écriture à la confirmation ([6](06-confirmation-crm-lead.md)/[7](07-confirmation-sale-order.md)).

Suivant : [5 — Recherche VSF par eurocode](05-recherche-vsf-eurocode.md).
