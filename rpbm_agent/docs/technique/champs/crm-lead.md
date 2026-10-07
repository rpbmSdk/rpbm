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
| `rpbm_xglass_piece_id`, `rpbm_piece_oe_id`, `rpbm_piece_am_id` | char, invisibles | widget (restauration des sélections à la réouverture) ; réécrits seulement si la sélection est retrouvée à la restauration ou changée par une action explicite, sinon conservés (lot E1.1, voir [workflow 6](../../fonctionnel/workflow/06-confirmation-crm-lead.md#pièce-mémorisée-lot-e11)) | — |
| `rpbm_xglass_vehicle_id` | char, invisible | widget (identifiant du véhicule X'Glass sélectionné) ; à la réouverture, ce véhicule est repris s'il figure dans les résultats de l'immatriculation, sinon le premier | — (aucun équivalent Studio, donc aucune migration) |
| `rpbm_xglass_piece_label` | char, invisible (« Pièce X'Glass sélectionnée ») | widget (lot E2, `17.0.261006.2`) : libellé de la pièce choisie, écrit avec les identifiants de pièce et sous la même règle de conservation ; lu par l'encart « Dossier » du devis, qui s'ouvre sans X'Glass | — (aucun équivalent Studio, donc aucune migration) |
| `rpbm_xglass_labor_operations` | json, invisible (« Main-d'œuvre X'Glass de la pièce ») | widget (correctif `17.0.261007.1`) : liste `laborOperations` de la pièce choisie, telle que `/getPieces` la renvoie, écrite avec les identifiants de pièce et sous la même règle de conservation ; liste vide si la pièce est retirée ; lue par le devis, qui propose ces opérations sans X'Glass | — (aucun équivalent Studio, donc aucune migration) |

`x_studio_eurocode_joint` n'est pas consommé par le module.

`rpbm_xglass_vehicle_id` est ajouté en `17.0.261005.3`, `rpbm_xglass_piece_label` en `17.0.261006.2` et `rpbm_xglass_labor_operations` en `17.0.261007.1` : ils existent après la mise à jour du module. Comme les trois identifiants de pièce, ils figurent dans un groupe invisible des vues du formulaire ([opportunité](#vue), [devis](sale-order.md#vue)) : un champ modifié par le widget doit être présent dans la vue, sinon l'enregistrement du formulaire échoue.

**Libellé de la pièce (lot E2).** Quand le widget écrit la pièce (véhicule et catégorie choisis, voir [workflow 6](../../fonctionnel/workflow/06-confirmation-crm-lead.md)), il écrit aussi le libellé, sous une condition voisine de celle des identifiants de pièce (`!_keepStoredPiece && (selectedPiece || !_keepStoredPieceAm)`) : libellé et référence de la pièce OE (« *libellé* — réf. *référence* »), ou à défaut, pour une pièce après-marché seule, sa référence et son fournisseur (« AM *référence* (*fournisseur*) »), sinon vide. Une pièce mémorisée non retrouvée ou non modifiée garde donc son libellé, comme ses identifiants, y compris une pièce « Autres marques AM » mémorisée seule, qui n'est jamais retrouvée à la restauration. L'opportunité le renseigne dès « Créer un devis » ; les dossiers confirmés avant `17.0.261006.2` n'en ont pas, et l'encart affiche « — ».

**Main-d'œuvre de la pièce (correctif du 2026-10-07, `17.0.261007.1`).** Depuis le lot E2, le devis s'ouvre sans X'Glass, et la main-d'œuvre n'existait qu'après « Charger X'Glass » : le vendeur ne pouvait ni l'ajouter ni la retirer avant. Le widget enregistre donc sur l'opportunité la liste `laborOperations` de la pièce choisie, telle que `/getPieces` la renvoie. Par opération : `key` (« *id pièce* : *id opération* », la clé de provenance des lignes de devis), `label`, `nature`, `rate` (T1, T2, T3 ou absent), `duration` (heures), `productId` (produit de service résolu d'après `rpbm_agent.labor_product_t1/t2/t3` lors de l'enregistrement ; le devis sans X'Glass n'utilise pas ce produit : à l'ajout, il le résout par taux avec les paramètres courants (`/rpbm_labor_products`)) et `unavailableReason`.

- **Écriture silencieuse.** Le champ est invisible : rien ne change à l'écran de l'opportunité. « Confirmer », « Confirmer et enregistrer » et « Créer un devis » l'écrivent.
- **Condition.** Celle des identifiants de pièce X'Glass et OE (`!_keepStoredPiece`), sans la nuance « Autres marques AM » du libellé : la liste est écrite quand la pièce est retrouvée à la restauration, choisie, remplacée ou retirée (liste vide s'il n'y a plus de pièce) ; une pièce mémorisée ni retrouvée ni changée garde sa main-d'œuvre. Une pièce « Autres marques AM » seule, sans pièce OE, donne une liste vide.
- **Devis.** « Confirmer » sans X'Glass n'écrit que la base et l'article principal : la main-d'œuvre enregistrée n'est pas touchée. Après « Charger X'Glass », la pièce restaurée fournit une main-d'œuvre fraîche, que le « Confirmer » suivant réécrit (elle remonte à l'opportunité par le miroir `related`, comme les autres champs).
- **Instantané.** Durées, taux et motifs d'indisponibilité sont ceux du dernier enregistrement fait avec X'Glass. Un changement chez X'Glass n'est visible sans X'Glass qu'après un nouveau « Charger X'Glass » puis « Confirmer ». Le produit de service, lui, suit les paramètres `labor_product_*` courants (résolu à l'ajout).
- **Dossiers existants.** Ceux confirmés avant `17.0.261007.1` n'ont pas de main-d'œuvre enregistrée (champ vide) : le devis n'affiche la section « 4. Main d'œuvre X'Glass » qu'après « Charger X'Glass », et le « Confirmer » qui suit l'enregistre.

Détail : [workflow 7](../../fonctionnel/workflow/07-confirmation-sale-order.md#main-dœuvre-enregistrée-correctif-du-2026-10-07) et [frontend](../frontend.md#main-dœuvre-enregistrée-correctif-du-2026-10-07).

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
