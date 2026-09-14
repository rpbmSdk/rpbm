# 6 — Confirmation sur Piste/Opportunité (`crm.lead`)

- **Déclencheur** : clic sur "Confirmer" (ou "Confirmer et enregistrer") dans la fenêtre du widget, ouverte depuis une fiche `crm.lead`.
- **Code** : `AgentWidgetDialog.onConfirm()` / `onConfirmAndSave()` → `confirmRecord(save)` → `getRecordData()` (`agent_widget_dialog.js`) ; classe `CrmLead` (`agent_widget_dialog_crm_lead.js`) qui surcharge les noms de champs.

| Champ écrit | Valeur source | Condition |
|---|---|---|
| `x_studio_field_NVioD` | `state.immatriculationValue` | toujours |
| `x_studio_vehicle_id` | véhicule Odoo réutilisé ou créé (cf. [8 — Création du véhicule](08-creation-vehicule.md)) | si un véhicule est sélectionné |
| `x_studio_categorie_xglass` | `selectedCalque.libelle` | si une catégorie est sélectionnée |
| `x_studio_field_eENQz` (Pièce concernée) | suggestion X'Glass visible et modifiable | si une catégorie est sélectionnée |
| `x_studio_field_ORIyy` (Base Eurocode) | `state.baseEurocode` | si un eurocode est renseigné — nécessite la surcharge `this.baseEurocodeField = 'x_studio_field_ORIyy'` dans `CrmLead` (sinon écriture dans `x_studio_base_eurocode`, inexistant sur `crm.lead`) |
| `x_studio_field_KyCjB` / `x_studio_field_ZhaeY` | marque/modèle du véhicule Fleet | si le nom est non vide et la correspondance du référentiel historique est unique ; une orthographe canonique exacte est privilégiée et une valeur manquante peut être créée à la confirmation |
| `x_studio_field_PfJlB` / `x_studio_field_i8fWl` | VIN / détail modèle Fleet | seulement si la source Fleet ou, pour VIN, la métadonnée X'Glass est renseignée |
| `x_studio_field_Eh6Wd` | date MEC Fleet ou métadonnée X'Glass | seulement si renseignée, convertie en texte `MM/YYYY` |
| `x_studio_field_TAhpP` | énergie Fleet | seulement pour les valeurs supportées ; variantes hybrides → `Hybride` |

- **Persistance** : mise à jour en mémoire (`this.props.record.update(data)`) ; écriture effective en base au clic utilisateur sur "Enregistrer" (bouton "Confirmer"), ou immédiate via `record.save()` (bouton "Confirmer et enregistrer"). Pas de `write` ORM explicite dans ce module.
- `x_studio_eurocode_joint` (Eurocode Joint) n'est **jamais écrit par le widget** : il reste saisi manuellement. L'Eurocode complet est, lui, renseigné uniquement quand un article VSF principal est désigné.

Le véhicule Fleet lié reste la source de vérité pour la marque, le modèle, le
VIN, le détail, l'énergie et la date MEC. Pour un véhicule existant, les
métadonnées X'Glass complètent les champs Fleet VIN/date manquants ; elles
servent aussi de repli pour préparer le CRM si l'écriture Fleet est refusée.
Depuis AG01-01, la confirmation
prépare les champs historiques existants ci-dessus ; elle ne crée plus les
alias `x_rpbm_vehicle_*`. Une source vide, ambiguë ou non autorisée produit un
avertissement sans bloquer et conserve l'ancienne valeur. Le kilométrage n'est
jamais modifié. Si un article VSF est sélectionné comme **article principal**, son Eurocode complet,
désignation, stock et référence constructeur sont reportés ; l'Eurocode joint
et les prix restent manuels ou calculés.

Détail de chaque champ : [technique/champs/crm-lead.md](../../technique/champs/crm-lead.md).
