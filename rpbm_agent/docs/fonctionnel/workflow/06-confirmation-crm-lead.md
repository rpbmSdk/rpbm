# 6 — Confirmation sur Piste/Opportunité (`crm.lead`)

- **Déclencheur** : clic sur « Confirmer », « Confirmer et enregistrer » ou « Créer un devis » dans la fenêtre du widget, ouverte depuis une fiche `crm.lead`.
- **Code** : `AgentWidgetDialog.onConfirm()` / `onConfirmAndSave()` → `confirmRecord(save)` → `writeRecord(save)` → `getRecordData()` (`agent_widget_dialog.js`) ; classe `AgentWidgetDialogCrmLead` (`agent_widget_dialog_crm_lead.js`) : pas de recherche VSF sur l'opportunité, et bouton « Créer un devis » (`onCreateQuotation()`).

| Champ écrit | Valeur source | Condition |
|---|---|---|
| `rpbm_license_plate` | `state.immatriculationValue` | toujours |
| `rpbm_vehicle_id` | véhicule Odoo réutilisé ou créé (cf. [8 — Création du véhicule](08-creation-vehicule.md)) | si un véhicule est sélectionné |
| `rpbm_xglass_vehicle_id` | identifiant du véhicule X'Glass sélectionné, repris à la réouverture ([2](02-selection-vehicule.md)) | toujours ; un véhicule étant requis pour confirmer, il est renseigné |
| `rpbm_xglass_category` | `selectedCalque.libelle` | si une catégorie est sélectionnée |
| `rpbm_part_type` | suggestion depuis le calque, visible et modifiable (`windshield`, `rear_window`, `side_window`, `other`) | si une catégorie est sélectionnée |
| `rpbm_eurocode_base` | `state.baseEurocode` | toujours (vide efface) |
| `rpbm_xglass_piece_id` / `rpbm_piece_oe_id` / `rpbm_piece_am_id` | identifiants X'Glass/OE/après-marché | toujours, vides pour effacer une ancienne sélection |

- **Article VSF principal** : depuis le lot E1, le dialog de l'opportunité ne cherche plus d'article VSF et n'écrit plus `rpbm_eurocode`, `rpbm_vsf_designation`, `rpbm_vsf_stock` ni `rpbm_constructor_reference`. Ces champs restent visibles et modifiables à la main dans le formulaire ; seul le dialog du devis les désigne (« Définir comme article principal », voir [7](07-confirmation-sale-order.md)).
- **Persistance** : mise à jour en mémoire (`this.props.record.update(data)`) ; écriture effective en base au clic sur « Enregistrer » (bouton « Confirmer »), ou immédiate via `record.save()` (boutons « Confirmer et enregistrer » et « Créer un devis »).
- **Dérivés à l'enregistrement** : marque, modèle, VIN, énergie, détail du modèle et date MEC (`rpbm_vehicle_brand_id`, `rpbm_vehicle_model_id`, `rpbm_vin`, `rpbm_fuel_type`, `rpbm_vehicle_detail_model`, `rpbm_first_registration_date`) sont calculés depuis le véhicule Fleet lié ; sans véhicule, ils restent saisissables. Pour un véhicule existant, `/enrichVehicule` complète d'abord VIN et date MEC Fleet manquants.
- **Champs Studio historiques** (immatriculation, marque, modèle, VIN, énergie, détail, date, pièce concernée, eurocodes, désignation/stock VSF, code constructeur) : recopiés automatiquement depuis les natifs par le module s'ils existent encore sur l'instance ; `x_studio_eurocode_joint` reste manuel. `rpbm_xglass_vehicle_id` n'a pas d'équivalent Studio.

## Créer un devis (lot E1)

Le bouton « Créer un devis » se place dans le pied de la fenêtre, après « Confirmer et enregistrer » : le raccourci Ctrl+Entrée reste donc « Confirmer ». Il est affiché lorsque l'opportunité a un client et n'est pas une piste, comme le bouton natif « Nouveau devis » ; contrairement à ce dernier, il n'est pas masqué sur une opportunité perdue. Il est désactivé comme « Confirmer » : véhicule et catégorie requis, et aussi pendant une reconnexion aux portails et pendant une écriture.

Un clic :

1. écrit les champs du dialog dans l'opportunité et l'enregistre, comme « Confirmer et enregistrer » ; si l'enregistrement échoue (champ requis manquant, erreur serveur), rien d'autre ne se passe et la fenêtre reste ouverte pour réessayer ;
2. ferme les portails et la fenêtre ;
3. lance l'action native « Nouveau devis » (`action_sale_quotations_new`) : un **nouveau** devis, non enregistré, lié à l'opportunité, comme avec le bouton natif. Chaque clic en ouvre un nouveau ; les devis existants de l'opportunité ne sont ni réutilisés ni modifiés. Si l'action échoue (droits, par exemple), Odoo affiche l'erreur comme pour le bouton natif et l'opportunité reste enregistrée ;
4. la fenêtre du widget s'ouvre alors seule sur ce devis (voir [7](07-confirmation-sale-order.md#ouverture-automatique-du-dialog-après-création-du-devis)).

Un double clic n'écrit et n'ouvre qu'une fois : l'état « écriture en cours » est partagé par les trois boutons. Détail technique : [frontend](../../technique/frontend.md#créer-un-devis-lot-e1).

Détail de chaque champ : [technique/champs/crm-lead.md](../../technique/champs/crm-lead.md).
