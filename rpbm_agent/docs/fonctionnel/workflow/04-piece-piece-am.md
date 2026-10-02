# 4 — Pièce et pièce après-marché (déduction eurocode)

- **Déclencheur** : clic utilisateur sur une pièce de la catégorie.
- **Code** : `onSelectPiece()` → `getSelectedPieceAm()`/`getPieceAm()` (`agent_widget_dialog.js`).
- **Route** : `POST /getPieceAm` (`main.py::getPieceAm`) → pièces après-marché correspondantes sur X'Glass.
- **Déduction eurocode** : un clic sur une pièce après-marché (`onSelectPieceAM()`) renseigne `state.baseEurocode` (état widget, pas encore un champ Odoo) avec les 5 premiers caractères de sa référence. Sans pièce après-marché, le champ reste à saisir à la main.

Aucun champ Odoo lu ou écrit à cette étape — uniquement de l'état widget local, qui alimentera l'écriture à la confirmation ([6](06-confirmation-crm-lead.md)/[7](07-confirmation-sale-order.md)).

La confirmation mémorise `piece.id`, `piece.pieceOe.id` et l'identifiant de la
pièce après-marché sélectionnée. À la réouverture, la pièce mémorisée est affichée
seule ; « Afficher les autres » réaffiche toutes les pièces. La base Eurocode enregistrée
est restaurée telle quelle, y compris lorsqu'elle a été saisie à la main ; la pièce
après-marché restaurée ne la remplace pas (R12, 2026-10-02). Un second clic sur la
pièce sélectionnée annule la sélection et efface la base Eurocode ainsi que la
recherche VSF.

Suivant : [5 — Recherche VSF par eurocode](05-recherche-vsf-eurocode.md).
