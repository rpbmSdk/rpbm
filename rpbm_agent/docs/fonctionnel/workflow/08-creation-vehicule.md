# 8 — Création du véhicule (`fleet.vehicle`)

- **Déclencheur** : bouton "Créer" sur le véhicule sélectionné (`VehiculeComponent`), ou appel automatique depuis `getRecordData()` si aucun véhicule Odoo existant n'a été trouvé au moment de la confirmation (étapes [6](06-confirmation-crm-lead.md)/[7](07-confirmation-sale-order.md)).
- **Route** : `POST /createVehicule` (`main.py::createVehicule`).
- **Condition préalable** : si un `fleet.vehicle` existe déjà avec la même `license_plate`, il est réutilisé tel quel — aucun champ n'est mis à jour dessus, tout le reste de cette étape est sauté.

| Champ écrit | Source | Condition |
|---|---|---|
| `driver_id` | `partner_id` (paramètre de route) | toujours |
| `model_id` | `fleet.vehicle.model` trouvé/créé depuis `xGlassModele.gamme` | toujours |
| `license_plate` | immatriculation recherchée | toujours |
| `description` | `vehicule.libelleCourt` | toujours |
| `power` | `vehicule.puissanceKw` | toujours |
| `doors` | `vehicule.portesNbr` | toujours |
| `fuel_type` | `vehicule.energie` converti en clé native `fleet.FUEL_TYPES` (`XGLASS_ENERGY_TO_FUEL_TYPE`, `main.py`) | si l'énergie X'Glass a un équivalent Fleet ; sinon champ vide + warning serveur |
| `rpbm_detail_model` | `vehicule.libelleCourt` | toujours |
| `image_1920` | image téléchargée depuis X'Glass | si `vehicule.imgUrl` est renseigné et le téléchargement réussit (HTTP 200) |
| `vin_sn` | `vehicule_meta.vin` | si `vehicule_meta` fourni et `vin` renseigné |
| `rpbm_first_registration_date` | `vehicule_meta.dateMec` (`MM/YYYY` → date) | si `vehicule_meta` fourni et `dateMec` renseigné |

- **Effets de bord** : crée à la volée `fleet.vehicle.model.brand` (si la marque X'Glass n'existe pas déjà) et `fleet.vehicle.model` (si le modèle n'existe pas déjà, lié à la marque). Aucune valeur de sélection n'est créée sur `fuel_type` (Odoo refuse d'altérer un champ de base).
- **Retour** : `{id, name}` du `fleet.vehicle` créé ou réutilisé.

Détail des champs : [technique/champs/fleet-vehicle.md](../../technique/champs/fleet-vehicle.md).
