# 7 — Confirmation sur Ordre de Vente (`sale.order`)

Le notebook « Véhicule (X'Glass) » est masqué si le devis ne possède pas d'opportunité liée.
Le widget n'est donc jamais ouvert dans un contexte où ses champs `related` seraient perdus.

Le lieu logistique ne se saisit pas dans la dialog véhicule : il est porté par le
champ natif `carrier_id`, visible sous le client dans le formulaire du devis.
Sur un nouveau devis lié à une opportunité, le module propose automatiquement
Galleria, Genipa ou Camion lorsque le champ CRM historique
`x_studio_lieu_intervention` permet une correspondance déterministe. Les valeurs
LAVAGE et les correspondances absentes restent manuelles. Le choix explicite de
l'utilisateur est prioritaire.

- **Déclencheur** : clic sur « Confirmer » (ou « Confirmer et enregistrer ») dans la fenêtre du widget, ouverte depuis une fiche `sale.order`.
- **Code** : même `confirmRecord()` → `getRecordData()` que pour `crm.lead` ; les noms de champs diffèrent via la classe `SaleOrder` (`agent_widget_dialog_sale_order.js`).

| Champ écrit | Valeur source | Condition |
|---|---|---|
| mêmes champs natifs `rpbm_*` que sur l'opportunité ([6](06-confirmation-crm-lead.md)) | mêmes sources | miroirs `related` écrivables : la valeur est portée par l'opportunité liée |

- **Persistance** : identique à `crm.lead` — mise à jour en mémoire, écriture effective au clic sur « Enregistrer » (bouton « Confirmer ») ou immédiate via `record.save()` (bouton « Confirmer et enregistrer »).
- L'ajout ou le retrait d'un article principal ou suggéré au devis (`addArticleToSaleOrder()` / `removeArticleFromSaleOrder()`) est indépendant de cette étape ; seule une ligne créée par le widget dans la dialog courante peut être retirée — voir [9 — Création du produit](09-creation-produit.md).

Les opérations de main-d'œuvre X'Glass cochées sont ajoutées indépendamment de
la confirmation. Chaque opération reconnue (T1, T2 ou T3) crée une ligne de
service dont la quantité vaut sa durée X'Glass. La clé
`rpbm_labor_operation_key` garde la provenance de la ligne, ce qui interdit
les doublons après réouverture et limite le retrait à la ligne du widget.

La confirmation standard de la vente est une étape distincte de la confirmation
de la dialog. Elle exige un `carrier_id` pour toute vente à l'état brouillon ou
envoyée, mais ne crée pas de transporteur et ne modifie pas les lignes de vente.

Pour un véhicule existant, `/enrichVehicule` complète les champs Fleet VIN/date MEC manquants ;
les champs dérivés du véhicule et les champs Studio historiques sont alimentés côté serveur à
l'enregistrement, comme sur l'opportunité. Le kilométrage n'est jamais modifié. Sans opportunité
liée, le widget est masqué.

Détail de chaque champ : [technique/champs/sale-order.md](../../technique/champs/sale-order.md).
