# Champs — `crm.lead`

Modèle porteur de la Piste/Opportunité. Tous les champs `x_studio_*` consommés par `rpbm_agent`, existants ou créés par [`pre_init_hook`](../configuration.md#mécanisme-retenu-pour-un-script-de-pré-installation).

| Champ | Type | Related → | Origine | Obsolète | Rôle |
|---|---|---|---|---|---|
| `x_studio_field_NVioD` | char | — | Studio (existant) | non | Immatriculation — champ historique conservé (lié aux factures/commandes), renseigné à la confirmation depuis le véhicule lié |
| `x_studio_field_KyCjB` / `x_studio_field_ZhaeY` | many2one | — | Studio (existant) | **oui, `[Obsolète]`** | Marque/modèle véhicule historiques ; conservés et renseignés si la correspondance Fleet est déterministe |
| `x_studio_vehicle_id` | many2one → `fleet.vehicle` | — | `pre_init_hook` (nouveau) | non | Véhicule Odoo lié (créé ou réutilisé) |
| `x_studio_categorie_xglass` | char | — | `pre_init_hook` (nouveau) | non | Catégorie/calque X'Glass sélectionné (ex : Pare-brise) |
| `x_studio_field_eENQz` ("Pièce concernée") | selection | — | Studio (existant) | non | 4 valeurs (`Pare-Brise`/`Lunette arrière`/`Glace Latérale`/`Autre...`) pilotant le forfait de pose — écrit par le widget via `pieceConcerneeField`, valeur suggérée depuis le calque X'Glass, visible et modifiable |
| `x_studio_field_ORIyy` ("Base Eurocode") | char | — | Studio (existant) | non | 5 premiers caractères de l'eurocode, préfiltrage VSF — ciblé par le widget via `CrmLead.baseEurocodeField` (`agent_widget_dialog_crm_lead.js`) |
| `x_studio_field_NwRik` ("Eurocode Complet") | char | — | Studio (existant) | non | Eurocode complet, saisi manuellement par l'utilisateur une fois la pièce confirmée — **jamais écrit par le widget** |
| `x_studio_eurocode_joint` ("Eurocode Joint") | char | — | Studio (existant) | non | Eurocode du joint, saisi manuellement si nécessaire — **jamais écrit par le widget** |

## Référentiel Fleet et rétrocompatibilité historique

Le véhicule Fleet lié par `x_studio_vehicle_id` est la source canonique pour
les nouveaux dossiers. Le lot AG01-01 ne crée plus les huit champs techniques
`x_rpbm_vehicle_*` (ni sur `crm.lead`, ni sur `sale.order`). Les champs de même
nom qui existeraient déjà dans une base restent toutefois intacts : aucun champ
historique, obsolète ou ancien alias n'est supprimé, renommé ou migré.

Lors de la confirmation du dialogue, le backend lit explicitement le véhicule
Fleet puis prépare les champs historiques suivants :

| Champ historique | Source Fleet | Règle |
|---|---|---|
| `x_studio_field_NVioD` | `license_plate` | Immatriculation |
| `x_studio_field_KyCjB` | `model_id.brand_id.name` | Référentiel historique unique, créé s'il est non vide et sans ambiguïté |
| `x_studio_field_ZhaeY` | `model_id.name` | Référentiel historique unique, créé s'il est non vide et sans ambiguïté |
| `x_studio_field_PfJlB` | `vin_sn` | Écrit seulement si Fleet est renseigné |
| `x_studio_field_TAhpP` | `fuel_type` | `Diesel`, `Essence`, `Électrique` ou `Hybride` selon la correspondance supportée |
| `x_studio_field_i8fWl` | `x_studio_detail_model` | Écrit seulement si Fleet est renseigné |
| `x_studio_field_Eh6Wd` | `x_studio_date_mec` | Texte au format `MM/YYYY` |

Une source vide, une valeur ambiguë, une énergie non supportée ou un manque de
droits déclenche un avertissement non bloquant et conserve la valeur historique
existante. Le kilométrage n'est jamais fabriqué ni modifié. Sur un devis,
les champs historiques sont les miroirs de l'opportunité et ne sont préparés
que lorsqu'une opportunité est présente.

Les champs Fleet réels `x_studio_detail_model` et `x_studio_date_mec`, ainsi que
`x_studio_vehicle_id`, restent pris en charge. La référence constructeur
`x_rpbm_vsf_constructor_reference` reste indépendante et inchangée.

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

L'onglet "Véhicule (X'Glass)" ajouté par `views/crm_lead_views.xml` affiche le
widget, `x_studio_vehicle_id` et `x_studio_categorie_xglass`. Les champs
historiques nécessaires à la préparation peuvent être chargés dans un groupe
invisible, mais les groupes d'identité Fleet en doublon ne sont pas affichés.
Les champs immatriculation/eurocode déjà visibles ailleurs sur ce formulaire ne
sont pas dupliqués ici.

## Lu/écrit par

- Lecture (auto-restore de la catégorie à l'ouverture) : [3 — Catégorie X'Glass](../../fonctionnel/workflow/03-categorie-xglass.md)
- Écriture : [6 — Confirmation sur Piste/Opportunité](../../fonctionnel/workflow/06-confirmation-crm-lead.md)
