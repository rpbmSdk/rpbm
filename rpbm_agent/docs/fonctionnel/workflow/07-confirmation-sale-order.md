# 7 — Confirmation sur Ordre de Vente (`sale.order`)

Le notebook « Véhicule (X'Glass) » est masqué si le devis ne possède pas d'opportunité liée.
Le widget n'est donc jamais ouvert dans un contexte où ses champs `related` seraient perdus.

- **Déclencheur** : clic sur « Confirmer » (ou « Confirmer et enregistrer ») dans la fenêtre du widget, ouverte depuis une fiche `sale.order`.
- **Code** : même `confirmRecord()` → `getRecordData()` que pour `crm.lead` ; les noms de champs diffèrent via la classe `SaleOrder` (`agent_widget_dialog_sale_order.js`).

| Champ écrit | Valeur source | Condition |
|---|---|---|
| `x_studio_immatriculation_` | `state.immatriculationValue` | toujours |
| `x_studio_vehicle_id` | véhicule Odoo réutilisé ou créé (cf. [8 — Création du véhicule](08-creation-vehicule.md)) | si un véhicule est sélectionné |
| `x_studio_categorie_xglass` | `selectedCalque.libelle` | si une catégorie est sélectionnée |
| `x_studio_pice_concerne` (Pièce concernée) | suggestion X'Glass visible et modifiable | si une catégorie est sélectionnée — champ `related` vers l'opportunité |
| `x_studio_base_eurocode` | `state.baseEurocode` | si un eurocode est renseigné — fonctionne nativement ici, ce champ `related` porte déjà ce nom exact |

- **Persistance** : identique à `crm.lead` — mise à jour en mémoire, écriture effective au clic sur « Enregistrer » (bouton « Confirmer ») ou immédiate via `record.save()` (bouton « Confirmer et enregistrer »).
- L'ajout ou le retrait d'un article principal ou suggéré au devis (`addArticleToSaleOrder()` / `removeArticleFromSaleOrder()`) est indépendant de cette étape. Chaque suggestion sélectionnée peut être ajoutée séparément ; seule une ligne créée par le widget dans la dialog courante peut être retirée — voir [9 — Création du produit](09-creation-produit.md).

Les informations Fleet et celles de l'article principal sont écrites sur
l'opportunité via les champs `related` du devis. Sans opportunité liée, le
widget est masqué et aucune synchronisation n'est proposée.

Détail de chaque champ : [technique/champs/sale-order.md](../../technique/champs/sale-order.md).
