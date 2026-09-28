# Champs — `account.move`

Facture et avoir client. Les champs sont déclarés dans `models/account_move.py`. Tous sont
**calculés et stockés** depuis les devis facturés (`invoice_line_ids.sale_line_ids.order_id`), et
gardent leur valeur si le devis n'est plus lié. Le widget ne les écrit jamais. Aucun n'est
synchronisé avec un champ Studio : les anciens champs Studio de la facture sont des `related` vers
le devis, qui continuent de fonctionner seuls.

| Champ | Type | Source |
|---|---|---|
| `rpbm_vehicle_id` | many2one `fleet.vehicle`, indexé, saisissable | premier véhicule renseigné parmi les devis facturés |
| `rpbm_license_plate` | char | `rpbm_license_plate` du premier devis facturé |
| `rpbm_vehicle_brand_id` | many2one `fleet.vehicle.model.brand`, indexé | idem, marque |
| `rpbm_vehicle_model_id` | many2one `fleet.vehicle.model`, indexé | idem, modèle |
| `rpbm_eurocode` | char | idem, eurocode (related de l'opportunité sur le devis) |
| `rpbm_part_type` | selection (valeurs de [`crm.lead`](crm-lead.md#pièce-et-article)) | idem, pièce concernée |

Hors `rpbm_vehicle_id`, ces champs sont en lecture seule, comme les anciens `related` Studio.

## Recalcul

Les dépendances traversent les `related` non stockés du devis : une modification de l'opportunité
(véhicule, eurocode, pièce concernée) se propage aux factures liées, y compris comptabilisées. Le
recalcul écrit en base sans passer par `write()` : ni le verrouillage de période ni le hash
d'inaltérabilité ne le bloquent.

À la mise à jour vers `17.0.260928.4`, les colonnes sont créées et calculées pour toutes les
pièces comptables (environ 20 400 par champ, dont 7 292 factures et avoirs client en pre-prod) ;
`write_date` et `write_uid` changent sur toutes. Aucune migration n'est nécessaire.

## Vue

`views/account_move_views.xml` hérite de deux vues standard :

- **recherche** (`account.view_account_invoice_filter`) : immatriculation, marque, modèle, eurocode
  et le champ combiné « Véhicule » (immatriculation, marque ou modèle ; pas de VIN sur la
  facture) ; regroupements par marque et modèle ;
- **liste des factures client** (`account.view_out_invoice_tree`) : immatriculation (affichée),
  marque et modèle (masqués par défaut) après la colonne « Client ».

Les champs du formulaire facture (section Studio) sont ajoutés par le script `studio_views.py`
(voir [`Jobs/rpbm_agent_stock`](../../../../Jobs/rpbm_agent_stock/README.md)). La facture n'a pas
de widget : aucune dialog n'existe pour `account.move` (voir [frontend](../frontend.md)).
