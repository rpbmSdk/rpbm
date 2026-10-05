# Champs — `crm.lead`

Modèle porteur de la Piste/Opportunité, **source de vérité du dossier** : le devis recopie ces
champs en `related`. Tous sont déclarés dans `models/crm_lead.py`.

## Véhicule (référentiel Fleet)

| Champ | Type | Alimentation | Studio historique synchronisé |
|---|---|---|---|
| `rpbm_vehicle_id` | many2one `fleet.vehicle` | widget (véhicule réutilisé ou créé) | — |
| `rpbm_license_plate` | char | widget ; dérivé du véhicule | `x_studio_field_NVioD` |
| `rpbm_vehicle_brand_id` | many2one `fleet.vehicle.model.brand`, **cherchable et groupable** | dérivé du véhicule, saisissable sans véhicule | `x_studio_field_KyCjB` (référentiel Studio `x_rpbm_marques_voitures`, par nom) |
| `rpbm_vehicle_model_id` | many2one `fleet.vehicle.model` | idem | `x_studio_field_ZhaeY` (référentiel Studio `x_rpbm_modeles_voitures`, par nom + marque) |
| `rpbm_vin` | char | idem (VIN `var = …;` de l'ancien parseur nettoyé) | `x_studio_field_PfJlB` |
| `rpbm_fuel_type` | selection `fleet.FUEL_TYPES` | idem | `x_studio_field_TAhpP` (Diesel / Essence / Électrique / Hybride ; GPL, GNV, hydrogène sans équivalent) |
| `rpbm_vehicle_detail_model` | char | idem | `x_studio_field_i8fWl` |
| `rpbm_first_registration_date` | date | idem | `x_studio_field_Eh6Wd` (char `MM/YYYY`) |

Les champs dérivés sont des `compute` stockés, `readonly=False` : quand un véhicule est lié, Fleet
les complète sans jamais effacer une valeur existante ; sans véhicule (dossiers historiques), ils
restent saisissables.

## Pièce et article

| Champ | Type | Alimentation | Studio historique synchronisé |
|---|---|---|---|
| `rpbm_xglass_category` | char | widget (libellé exact du calque X'Glass) | — |
| `rpbm_part_type` | selection `windshield` / `rear_window` / `side_window` / `other` | widget (suggestion depuis le calque, modifiable) | `x_studio_field_eENQz` (Pare-Brise / Lunette arrière / Glace Latérale / Autre...) — **pilote la cascade de prix Studio** |
| `rpbm_eurocode_base` | char | widget (5 premiers caractères de la pièce après-marché, ou saisie) | `x_studio_field_ORIyy` |
| `rpbm_eurocode` | char, indexé | widget **du devis**, article VSF **principal** (miroir `related` écrivable) ; saisie manuelle possible sur l'opportunité ; plus écrit par le dialog de l'opportunité depuis le lot E1 | `x_studio_field_NwRik` |
| `rpbm_vsf_designation` | char | idem | `x_studio_field_j8eh3` |
| `rpbm_vsf_stock` | integer | idem | `x_studio_field_BKtpw` (char) |
| `rpbm_constructor_reference` | char | idem, si VSF la fournit | `x_studio_field_MNzfJ` |
| `rpbm_intervention_location` | selection `galleria` / `genipa` / `domicile` / `lavage_place_armes` / `lavage_marin` | saisie ; préremplit `sale.order.carrier_id` | `x_studio_lieu_intervention` |
| `rpbm_xglass_piece_id`, `rpbm_piece_oe_id`, `rpbm_piece_am_id` | char, invisibles | widget (restauration des sélections à la réouverture) | — |
| `rpbm_xglass_vehicle_id` | char, invisible | widget (identifiant du véhicule X'Glass sélectionné) ; à la réouverture, ce véhicule est repris s'il figure dans les résultats de l'immatriculation, sinon le premier | — (aucun équivalent Studio, donc aucune migration) |

`x_studio_eurocode_joint` n'est pas consommé par le module.

`rpbm_xglass_vehicle_id` est ajouté en `17.0.261005.3` : il existe après la mise à jour du module. Comme les trois identifiants de pièce, il figure dans un groupe invisible des vues du formulaire ([opportunité](#vue), [devis](sale-order.md#vue)) : un champ modifié par le widget doit être présent dans la vue, sinon l'enregistrement du formulaire échoue.

## Synchronisation avec les champs Studio

Le mixin `rpbm.legacy.sync.mixin` (`models/legacy_fields.py`) recopie chaque écriture d'un champ
natif vers le champ Studio correspondant s'il existe, et une saisie Studio seule vers le natif
(convertisseurs : énergie, date, pièce concernée, lieu, stock, référentiels marque/modèle). Une
valeur non convertible laisse la cible inchangée. Sans champs Studio, le mixin ne fait rien.

## Vue

`views/crm_lead_views.xml` hérite de trois vues standard :

- **formulaire** : l'onglet « Véhicule (X'Glass) » affiche le widget et tous les champs ci-dessus ;
- **recherche** : immatriculation, marque, modèle, VIN, eurocode et un champ combiné « Véhicule »
  (immatriculation, VIN, marque ou modèle en une saisie) ; regroupements par marque, modèle et
  pièce concernée ;
- **liste** : immatriculation avant `country_id`, que la liste Studio remplace par l'ancienne
  immatriculation, donc juste à côté d'elle ; eurocode, puis marque et modèle (masqués par défaut)
  après `activity_user_id`, où la liste Studio place l'ancien eurocode.

Les vues Studio des équipes (section « Informations Véhicule », libellés « (ancien) ») ne sont pas
modifiées par le module mais par le script `studio_views.py` (voir
[`Jobs/rpbm_agent_stock`](../../../../Jobs/rpbm_agent_stock/README.md)) ; règles d'ancrage dans
[configuration](../configuration.md#intégration-dans-les-vues). Le script place les champs natifs
dans la section Studio et déplace les anciens champs doublés dans un onglet « Anciens champs ».

## Lu/écrit par

- Lecture (restauration à l'ouverture) : [2 — Sélection du véhicule](../../fonctionnel/workflow/02-selection-vehicule.md), [3 — Catégorie X'Glass](../../fonctionnel/workflow/03-categorie-xglass.md), [4 — Pièce](../../fonctionnel/workflow/04-piece-piece-am.md)
- Écriture : [6 — Confirmation sur Piste/Opportunité](../../fonctionnel/workflow/06-confirmation-crm-lead.md) (« Confirmer », « Confirmer et enregistrer », « Créer un devis »)
