# Champs — `fleet.vehicle`

Véhicule Odoo créé (ou réutilisé s'il existe déjà par `license_plate`) lors de la confirmation du widget — voir [8 — Création du véhicule](../../fonctionnel/workflow/08-creation-vehicule.md).

| Champ | Type | Origine | Rôle |
|---|---|---|---|
| `x_studio_detail_model` | char | `pre_init_hook` (nouveau) | Détail du modèle (ex : `KIA PICANTO III PHASE 2 - 5P 2020-09-> 1.2i 85`), copié depuis `vehicule.libelleCourt` (X'Glass) |
| `x_studio_date_mec` | date | `pre_init_hook` (nouveau) | Date de mise en circulation, extraite du scraping X'Glass (`vehicule_meta.dateMec`, format `%m/%Y`), écrite seulement si cette donnée est disponible |

Champs standards également écrits à la création (non `x_studio_*`, pour mémoire) : `driver_id`, `model_id`, `license_plate`, `description`, `power`, `doors`, `fuel_type`, `image_1920`, `vin_sn` (si disponible).

Documentés mais **non consommés par le code actuel** (ni lus ni écrits par `rpbm_agent` — voir [état des lieux](../../etat-des-lieux.md)), donc volontairement absents de `pre_init_hook` : `x_studio_autre_infos`, `x_studio_note` (champ HTML calculé). À ajouter à `FIELDS_TO_ENSURE` (`hooks.py`) si un usage futur les rend nécessaires.

## Vue

Affiché dans l'onglet "X'Glass" ajouté par `views/fleet_vehicle_views.xml` (hérite de `fleet.fleet_vehicle_view_form`).

## Lu/écrit par

- Écriture : [8 — Création du véhicule](../../fonctionnel/workflow/08-creation-vehicule.md) (route `/createVehicule`)
