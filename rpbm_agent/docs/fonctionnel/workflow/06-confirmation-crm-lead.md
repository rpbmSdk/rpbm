# 6 — Confirmation sur Piste/Opportunité (`crm.lead`)

- **Déclencheur** : clic sur "Confirmer" (ou "Confirmer et enregistrer") dans la fenêtre du widget, ouverte depuis une fiche `crm.lead`.
- **Code** : `AgentWidgetDialog.onConfirm()` / `onConfirmAndSave()` → `confirmRecord(save)` → `getRecordData()` (`agent_widget_dialog.js`) ; classe `CrmLead` (`agent_widget_dialog_crm_lead.js`) qui surcharge les noms de champs.

| Champ écrit | Valeur source | Condition |
|---|---|---|
| `rpbm_license_plate` | `state.immatriculationValue` | toujours |
| `rpbm_vehicle_id` | véhicule Odoo réutilisé ou créé (cf. [8 — Création du véhicule](08-creation-vehicule.md)) | si un véhicule est sélectionné |
| `rpbm_xglass_category` | `selectedCalque.libelle` | si une catégorie est sélectionnée |
| `rpbm_part_type` | suggestion depuis le calque, visible et modifiable (`windshield`, `rear_window`, `side_window`, `other`) | si une catégorie est sélectionnée |
| `rpbm_eurocode_base` | `state.baseEurocode` | toujours (vide efface) |
| `rpbm_xglass_piece_id` / `rpbm_piece_oe_id` / `rpbm_piece_am_id` | identifiants X'Glass/OE/après-marché | toujours, vides pour effacer une ancienne sélection |
| `rpbm_eurocode`, `rpbm_vsf_designation`, `rpbm_vsf_stock`, `rpbm_constructor_reference` | article VSF désigné **principal** | si un article principal est désigné |

- **Persistance** : mise à jour en mémoire (`this.props.record.update(data)`) ; écriture effective en base au clic sur « Enregistrer » (bouton « Confirmer »), ou immédiate via `record.save()` (bouton « Confirmer et enregistrer »).
- **Dérivés à l'enregistrement** : marque, modèle, VIN, énergie, détail du modèle et date MEC (`rpbm_vehicle_brand_id`, `rpbm_vehicle_model_id`, `rpbm_vin`, `rpbm_fuel_type`, `rpbm_vehicle_detail_model`, `rpbm_first_registration_date`) sont calculés depuis le véhicule Fleet lié ; sans véhicule, ils restent saisissables. Pour un véhicule existant, `/enrichVehicule` complète d'abord VIN et date MEC Fleet manquants.
- **Champs Studio historiques** (immatriculation, marque, modèle, VIN, énergie, détail, date, pièce concernée, eurocodes, désignation/stock VSF, code constructeur) : recopiés automatiquement depuis les natifs par le module s'ils existent encore sur l'instance ; `x_studio_eurocode_joint` reste manuel.

Détail de chaque champ : [technique/champs/crm-lead.md](../../technique/champs/crm-lead.md).
