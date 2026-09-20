# Champs — `fleet.vehicle`

Véhicule Odoo créé (ou réutilisé s'il existe déjà par `license_plate`) lors de la confirmation du
widget — voir [8 — Création du véhicule](../../fonctionnel/workflow/08-creation-vehicule.md).
Fleet est le **référentiel canonique** du véhicule : marque, modèle, VIN, énergie, détail et date
de mise en circulation de l'opportunité en dérivent (voir [crm-lead.md](crm-lead.md)).

| Champ | Type | Origine | Rôle |
|---|---|---|---|
| `rpbm_detail_model` | char | `models/fleet_vehicle.py` | Détail du modèle (ex : `KIA PICANTO III PHASE 2 - 5P 2020-09-> 1.2i 85`), copié depuis `vehicule.libelleCourt` (X'Glass) |
| `rpbm_first_registration_date` | date | `models/fleet_vehicle.py` | Date de mise en circulation, extraite du scraping X'Glass (`vehicule_meta.dateMec`, `MM/YYYY`), écrite seulement si disponible |

Champs standards également écrits à la création : `driver_id`, `model_id` (marque et modèle
Fleet créés à la volée depuis X'Glass), `license_plate`, `description`, `power`, `doors`,
`fuel_type` (clé native déduite de l'énergie X'Glass, vide si sans équivalent), `image_1920`,
`vin_sn` (si disponible). Lorsqu'un véhicule existe déjà, `/enrichVehicule` complète seulement
`vin_sn` et `rpbm_first_registration_date` s'ils sont absents ; le seul remplacement admis est un
VIN de l'ancienne forme `var = <VIN>;`.

## Vue

Onglet « X'Glass » ajouté par `views/fleet_vehicle_views.xml`.

## Lu/écrit par

- Écriture : [8 — Création du véhicule](../../fonctionnel/workflow/08-creation-vehicule.md) (`/createVehicule`) et confirmation d'un véhicule existant (`/enrichVehicule`)
