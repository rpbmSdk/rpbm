# Champs — `crm.lead`

Modèle porteur de la Piste/Opportunité. Tous les champs `x_studio_*` consommés par `rpbm_agent`, existants ou créés par [`pre_init_hook`](../configuration.md#mécanisme-retenu-pour-un-script-de-pré-installation).

| Champ | Type | Related → | Origine | Obsolète | Rôle |
|---|---|---|---|---|---|
| `x_studio_field_NVioD` | char | — | Studio (existant) | non | Immatriculation — champ historique conservé (lié aux factures/commandes), rendu calculé à partir du véhicule lié |
| `x_studio_field_KyCjB` / `x_studio_field_ZhaeY` | many2one | — | Studio (existant) | **oui, `[Obsolète]`** | Marque/modèle véhicule — doublons/créations sauvages historiques ; volontairement exclus des nouvelles vues |
| `x_studio_vehicle_id` | many2one → `fleet.vehicle` | — | `pre_init_hook` (nouveau) | non | Véhicule Odoo lié (créé ou réutilisé) |
| `x_studio_categorie_xglass` | char | — | `pre_init_hook` (nouveau) | non | Catégorie/calque X'Glass sélectionné (ex : Pare-brise) |
| `x_studio_field_eENQz` ("Pièce concernée") | selection | — | Studio (existant) | non | 4 valeurs (`Pare-Brise`/`Lunette arrière`/`Glace Latérale`/`Autre...`) pilotant le forfait de pose — écrit par le widget via `pieceConcerneeField`, valeur suggérée depuis le calque X'Glass, visible et modifiable |
| `x_studio_field_ORIyy` ("Base Eurocode") | char | — | Studio (existant) | non | 5 premiers caractères de l'eurocode, préfiltrage VSF — ciblé par le widget via `CrmLead.baseEurocodeField` (`agent_widget_dialog_crm_lead.js`) |
| `x_studio_field_NwRik` ("Eurocode Complet") | char | — | Studio (existant) | non | Eurocode complet, saisi manuellement par l'utilisateur une fois la pièce confirmée — **jamais écrit par le widget** |
| `x_studio_eurocode_joint` ("Eurocode Joint") | char | — | Studio (existant) | non | Eurocode du joint, saisi manuellement si nécessaire — **jamais écrit par le widget** |

## Référentiel Fleet

Le véhicule Fleet lié par `x_studio_vehicle_id` est la source canonique pour
les nouveaux dossiers. Le module expose des champs `related` stockés, sans
écrire dans les anciennes relations Studio `x_studio_field_KyCjB` (marque) et
`x_studio_field_ZhaeY` (modèle) :

| Champ | Related → | Rôle |
|---|---|---|
| `x_rpbm_vehicle_brand_id` | `x_studio_vehicle_id.model_id.brand_id` | Marque Fleet |
| `x_rpbm_vehicle_model_id` | `x_studio_vehicle_id.model_id` | Modèle Fleet |
| `x_rpbm_vehicle_vin` | `x_studio_vehicle_id.vin_sn` | VIN |
| `x_rpbm_vehicle_detail_model` | `x_studio_vehicle_id.x_studio_detail_model` | Détail modèle |
| `x_rpbm_vehicle_fuel_type` | `x_studio_vehicle_id.fuel_type` | Énergie |
| `x_rpbm_vehicle_date_mec` | `x_studio_vehicle_id.x_studio_date_mec` | Date de première MEC |

Les alias `x_rpbm_vehicle_brand_name` et `x_rpbm_vehicle_model_name` servent
aux vues et QWeb. Les fiches historiques sans véhicule Fleet ne sont pas
reprises et peuvent donc rester vides dans ces nouveaux affichages.

## Structure des 3 champs Eurocode

Trois champs Eurocode distincts coexistent sur la Piste/Opportunité, correspondant à trois étapes du travail des utilisateurs (convention préexistante à `rpbm_agent`) :

1. **Base Eurocode** (`x_studio_field_ORIyy`) — les 5 premiers caractères, pour préfiltrer les articles VSF. Seul champ eurocode lu/écrit par le widget.
2. **Eurocode (Complet)** (`x_studio_field_NwRik`) — renseigné manuellement une fois la pièce exacte confirmée.
3. **Eurocode (Joint)** (`x_studio_eurocode_joint`) — renseigné manuellement en plus si un joint est nécessaire.

Lorsqu'un article VSF est explicitement défini comme article principal, le
widget écrit son code dans `x_studio_field_NwRik`, sa désignation dans
`x_studio_field_j8eh3`, son stock dans `x_studio_field_BKtpw` et sa référence
constructeur dans `x_studio_field_MNzfJ`. Il ne renseigne jamais les champs de
prix ou de marge calculés.

## Bug corrigé

Le widget ciblait auparavant `x_studio_base_eurocode` par défaut (hérité de `AbstractWidgetRecord`, `utils.js`), un champ qui n'existe pas sur `crm.lead` (il n'existe que sur `sale.order`, en tant que champ `related`). Corrigé par la surcharge `this.baseEurocodeField = 'x_studio_field_ORIyy'` dans le constructeur de `CrmLead` — voir [état des lieux](../../etat-des-lieux.md).

## Vue

Affiché dans l'onglet "Véhicule (X'Glass)" ajouté par `views/crm_lead_views.xml` (hérite de `crm.crm_lead_view_form`) : widget + `x_studio_vehicle_id` + `x_studio_categorie_xglass` uniquement — les champs immatriculation/eurocode sont déjà visibles ailleurs sur ce formulaire (vues Studio existantes), donc volontairement non dupliqués ici.

## Lu/écrit par

- Lecture (auto-restore de la catégorie à l'ouverture) : [3 — Catégorie X'Glass](../../fonctionnel/workflow/03-categorie-xglass.md)
- Écriture : [6 — Confirmation sur Piste/Opportunité](../../fonctionnel/workflow/06-confirmation-crm-lead.md)
