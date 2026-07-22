# 1 — Recherche véhicule par immatriculation

- **Déclencheur** : ouverture du widget (immatriculation déjà présente sur l'enregistrement) ou saisie manuelle + clic "Search".
- **Code** : `AgentWidgetDialog.onSearchImmatriculation()` (`agent_widget_dialog.js`).
- **Route** : `POST /searchImmatriculation` (`main.py::searchImmatriculation`) → `xglassAgent.searchVehiculeImmat(immatriculation)`.

| Champ lu | Modèle | Condition |
|---|---|---|
| `immatriculationField` (`x_studio_field_NVioD` sur `crm.lead`, `x_studio_immatriculation_` sur `sale.order`) | `crm.lead`/`sale.order` | pré-remplissage à l'ouverture de la fenêtre uniquement — aucune écriture à cette étape |

Aucun champ Odoo n'est écrit à cette étape — recherche externe (X'Glass) uniquement, résultat stocké en état local du widget (`state.vehicules`).

Suivant : [2 — Sélection du véhicule](02-selection-vehicule.md).
