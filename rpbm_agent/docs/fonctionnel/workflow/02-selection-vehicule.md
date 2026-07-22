# 2 — Sélection du véhicule

- **Déclencheur** : le premier véhicule trouvé est auto-sélectionné (`useEffect` sur `vehicules`) ; l'utilisateur peut aussi cliquer sur un autre véhicule de la liste.
- **Code** : `onSelectVehicule()` (`agent_widget_dialog.js`).
- **Routes déclenchées en cascade** :
  - `GET /getOdooVehicule` (`main.py::getVehicule`) — recherche `fleet.vehicle` existant par `license_plate` ; si le conducteur (`driver_id`) diffère du client de l'enregistrement, une alerte s'affiche.
  - `GET /getPlanche` (`main.py::getPlanche`) — récupère les catégories/calques disponibles pour ce véhicule sur X'Glass.

Aucun champ Odoo n'est lu ou écrit directement à cette étape (uniquement de l'état widget local + un appel en lecture seule sur `fleet.vehicle`). La création éventuelle du véhicule est différée à la confirmation — voir [8 — Création du véhicule](08-creation-vehicule.md).

Suivant : [3 — Catégorie X'Glass](03-categorie-xglass.md).
