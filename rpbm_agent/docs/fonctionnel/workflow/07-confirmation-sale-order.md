# 7 — Confirmation sur Ordre de Vente (`sale.order`)

- **Déclencheur** : clic sur "Confirmer" dans la fenêtre du widget, ouverte depuis une fiche `sale.order`.
- **Code** : même `getRecordData()` que pour `crm.lead` (`agent_widget_dialog.js:226-258`) — seuls les noms de champs diffèrent, via la classe `SaleOrder` (`agent_widget_dialog_sale_order.js`).

| Champ écrit | Valeur source | Condition |
|---|---|---|
| `x_studio_immatriculation_` | `state.immatriculationValue` | toujours |
| `x_studio_vehicle_id` | véhicule Odoo réutilisé ou créé (cf. [8 — Création du véhicule](08-creation-vehicule.md)) | si un véhicule est sélectionné |
| `x_studio_categorie_xglass` | `selectedCalque.libelle` | si une catégorie est sélectionnée |
| `x_studio_base_eurocode` | `state.baseEurocode` | si un eurocode est renseigné — fonctionne nativement ici, ce champ `related` porte déjà ce nom exact |

- **Persistance** : identique à `crm.lead` — mise à jour en mémoire, écriture effective au clic sur "Enregistrer".
- `SaleOrder.eurocodeField` (`x_studio_eurocode`) et `SaleOrder.OrderlLines` sont des propriétés **mortes**, jamais utilisées dans `getRecordData()` (voir [état des lieux](../../etat-des-lieux.md)).
- L'ajout d'un article au devis (`addToSaleOrder()`) est **indépendant** de cette étape de confirmation — voir [9 — Création du produit](09-creation-produit.md).

Détail de chaque champ : [technique/champs/sale-order.md](../../technique/champs/sale-order.md).
