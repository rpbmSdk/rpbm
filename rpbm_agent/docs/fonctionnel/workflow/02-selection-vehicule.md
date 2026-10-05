# 2 — Sélection du véhicule

- **Déclencheur** : le véhicule X'Glass mémorisé sur l'enregistrement (`rpbm_xglass_vehicle_id`) est auto-sélectionné s'il figure dans la liste, sinon le premier véhicule trouvé (`useEffect` sur `vehicules`) ; l'utilisateur peut aussi cliquer sur un autre véhicule de la liste.
- **Code** : `onSelectVehicule()` (`agent_widget_dialog.js`).
- **Routes déclenchées en cascade** :
  - `GET /getOdooVehicule` (`main.py::getVehicule`) — recherche `fleet.vehicle` existant par `license_plate` ; si le conducteur (`driver_id`) diffère du client de l'enregistrement, une alerte s'affiche.
  - `POST /rpbm_agent/getVehiculeMeta` (`main.py::getVehiculeMeta`) — sélectionne le véhicule côté X'Glass et ramène en un seul appel ses métadonnées (VIN/CNIT/date MEC) et la planche (catégories/calques disponibles).

Aucun champ Odoo n'est écrit à cette étape : le seul champ lu est `rpbm_xglass_vehicle_id` (véhicule X'Glass mémorisé, voir [6](06-confirmation-crm-lead.md)), avec un appel en lecture seule sur `fleet.vehicle` ; le reste est de l'état widget local. La création éventuelle du véhicule est différée à la confirmation — voir [8 — Création du véhicule](08-creation-vehicule.md).

Suivant : [3 — Catégorie X'Glass](03-categorie-xglass.md).
