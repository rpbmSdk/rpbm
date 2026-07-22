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
| `fuel_type` | `vehicule.energieLibelle` (valeur de sélection trouvée/créée) | toujours |
| `x_studio_detail_model` | `vehicule.libelleCourt` | toujours |
| `image_1920` | image téléchargée depuis X'Glass | si `vehicule.imgUrl` est renseigné et le téléchargement réussit (HTTP 200) |
| `vin_sn` | `vehicule_meta.vin` | si `vehicule_meta` fourni et `vin` renseigné |
| `x_studio_date_mec` | `vehicule_meta.dateMec` (`%m/%Y` → date) | si `vehicule_meta` fourni et `dateMec` renseigné |

- **Effets de bord** : crée à la volée `fleet.vehicle.model.brand` (si la marque X'Glass n'existe pas déjà), `fleet.vehicle.model` (si le modèle n'existe pas déjà, lié à la marque), et une nouvelle valeur de sélection `ir.model.fields.selection` sur le champ `fuel_type` si le libellé énergie X'Glass ne correspond à aucune valeur existante.

Détail des champs : [technique/champs/fleet-vehicle.md](../../technique/champs/fleet-vehicle.md).
