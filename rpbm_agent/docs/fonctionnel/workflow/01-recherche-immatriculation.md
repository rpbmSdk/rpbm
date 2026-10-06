# 1 — Recherche véhicule par immatriculation

- **Déclencheur** : ouverture du widget (immatriculation déjà présente sur l'enregistrement) ou saisie manuelle + clic "Search". Sur le devis, depuis le lot E2, l'ouverture ne se connecte pas à X'Glass : cette étape et les suivantes (2 à 4) ne partent qu'après « Charger X'Glass » ([7](07-confirmation-sale-order.md#devis-sans-xglass-lot-e2)).
- **Code** : `AgentWidgetDialog.onSearchImmatriculation()` (`agent_widget_dialog.js`).
- **Route** : `POST /searchImmatriculation` (`main.py::searchImmatriculation`) → `xglassAgent.searchVehiculeImmat(immatriculation)`.

| Champ lu | Modèle | Condition |
|---|---|---|
| `immatriculationField` (`x_studio_field_NVioD` sur `crm.lead`, `x_studio_immatriculation_` sur `sale.order`) | `crm.lead`/`sale.order` | pré-remplissage à l'ouverture de la fenêtre uniquement — aucune écriture à cette étape |

Aucun champ Odoo n'est écrit à cette étape — recherche externe (X'Glass) uniquement, résultat stocké en état local du widget (`state.vehicules`).

Suivant : [2 — Sélection du véhicule](02-selection-vehicule.md).
