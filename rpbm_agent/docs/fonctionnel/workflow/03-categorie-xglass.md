# 3 — Catégorie X'Glass (calque)

- **Déclencheur** : clic utilisateur sur une catégorie, OU auto-sélection si le champ `categorieXglass` est déjà renseigné sur l'enregistrement au chargement de la planche (`useEffect` sur `planche`, `agent_widget_dialog.js`).
- **Code** : `onClickCalque()` (`agent_widget_dialog.js`).
- **Route** : `POST /getPieces` (`main.py::getPieces`) → liste des pièces de la catégorie.

| Champ | Modèle | Sens | Détail |
|---|---|---|---|
| `x_studio_categorie_xglass` | `crm.lead` / `sale.order` | **lecture** | Comparé aux `libelle` des calques chargés ; si une correspondance est trouvée, la catégorie est présélectionnée automatiquement (seule lecture de champ Odoo de toute la chaîne réactive du widget, en dehors de l'ouverture de la fenêtre) |

Aucune écriture à cette étape — la valeur n'est écrite qu'à la confirmation (voir [6](06-confirmation-crm-lead.md)/[7](07-confirmation-sale-order.md)). Détail du champ : [technique/champs/crm-lead.md](../../technique/champs/crm-lead.md) / [sale-order.md](../../technique/champs/sale-order.md).

Suivant : [4 — Pièce et pièce après-marché](04-piece-piece-am.md).
