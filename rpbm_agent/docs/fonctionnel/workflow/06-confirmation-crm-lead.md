# 6 — Confirmation sur Piste/Opportunité (`crm.lead`)

- **Déclencheur** : clic sur "Confirmer" dans la fenêtre du widget, ouverte depuis une fiche `crm.lead`.
- **Code** : `AgentWidgetDialog.onConfirm()` → `getRecordData()` (`agent_widget_dialog.js:226-258`) ; classe `CrmLead` (`agent_widget_dialog_crm_lead.js`) qui surcharge les noms de champs.

| Champ écrit | Valeur source | Condition |
|---|---|---|
| `x_studio_field_NVioD` | `state.immatriculationValue` | toujours |
| `x_studio_vehicle_id` | véhicule Odoo réutilisé ou créé (cf. [8 — Création du véhicule](08-creation-vehicule.md)) | si un véhicule est sélectionné |
| `x_studio_categorie_xglass` | `selectedCalque.libelle` | si une catégorie est sélectionnée |
| `x_studio_field_ORIyy` (Base Eurocode) | `state.baseEurocode` | si un eurocode est renseigné — nécessite la surcharge `this.baseEurocodeField = 'x_studio_field_ORIyy'` dans `CrmLead` (sinon écriture dans `x_studio_base_eurocode`, inexistant sur `crm.lead`) |

- **Persistance** : mise à jour en mémoire (`this.props.record.update(data)`) ; écriture effective en base au clic utilisateur sur "Enregistrer" (pas de `write` ORM explicite dans ce module).
- `x_studio_field_NwRik` (Eurocode Complet) et `x_studio_eurocode_joint` (Eurocode Joint) ne sont **jamais écrits par le widget** — saisie manuelle ultérieure, voir [technique/champs/crm-lead.md](../../technique/champs/crm-lead.md#structure-des-3-champs-eurocode).

Détail de chaque champ : [technique/champs/crm-lead.md](../../technique/champs/crm-lead.md).
