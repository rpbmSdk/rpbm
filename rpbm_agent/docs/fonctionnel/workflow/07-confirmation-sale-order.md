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

- **Déclencheur** : clic sur « Confirmer » (ou « Confirmer et enregistrer ») dans la fenêtre du widget, ouverte depuis une fiche `sale.order` (loupe) ou automatiquement après « Créer un devis » (voir [plus bas](#ouverture-automatique-du-dialog-après-création-du-devis)).
- **Code** : même `confirmRecord()` → `writeRecord()` → `getRecordData()` que pour `crm.lead` ; les champs `rpbm_*` portent les mêmes noms sur les deux modèles. La classe `AgentWidgetDialogSaleOrder` (`agent_widget_dialog_sale_order.js`) ajoute la recherche VSF, les lignes d'article et la main-d'œuvre.

| Champ écrit | Valeur source | Condition |
|---|---|---|
| mêmes champs natifs `rpbm_*` que sur l'opportunité ([6](06-confirmation-crm-lead.md)), `rpbm_xglass_vehicle_id` compris | mêmes sources | miroirs `related` écrivables : la valeur est portée par l'opportunité liée |
| `rpbm_eurocode`, `rpbm_vsf_designation`, `rpbm_vsf_stock`, `rpbm_constructor_reference` | article VSF désigné **principal** (« Définir comme article principal ») | si un article principal est désigné ; depuis le lot E1, seul le dialog du devis les écrit |

- **Persistance** : identique à `crm.lead` — mise à jour en mémoire, écriture effective au clic sur « Enregistrer » (bouton « Confirmer ») ou immédiate via `record.save()` (bouton « Confirmer et enregistrer »).
- L'ajout ou le retrait d'un article principal ou suggéré au devis (`addArticleToSaleOrder()` / `removeArticleFromSaleOrder()`) est indépendant de cette étape ; seule une ligne créée par le widget dans la dialog courante peut être retirée, par « Retirer du devis », qui remplace « Ajouter au devis » une fois la ligne ajoutée (un produit déjà présent à l'ouverture affiche « Article déjà présent dans le devis. », sans retrait) — voir [9 — Création du produit](09-creation-produit.md#retirer-du-devis-r28).

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

## Ouverture automatique du dialog après création du devis

Un devis créé par « Créer un devis » depuis l'opportunité ([6](06-confirmation-crm-lead.md#créer-un-devis-lot-e1)) ouvre seul la fenêtre du widget : il n'y a pas de clic sur la loupe. Elle restaure le contexte de l'opportunité comme à toute réouverture : le véhicule X'Glass mémorisé (`rpbm_xglass_vehicle_id`) s'il figure dans les résultats de l'immatriculation, sinon le premier, puis la catégorie, la pièce, la pièce après-marché et la base Eurocode. La recherche VSF se lance seule quand une pièce ou une pièce après-marché est retrouvée, et la main-d'œuvre est proposée (« 4. Main d'œuvre », « 5. Article VSF »). Les portails sont reconnectés à cette occasion, la fenêtre de l'opportunité les ayant fermés.

L'ouverture n'a lieu qu'une fois, pour ce devis nouveau. Elle n'a pas lieu avec « Nouveau devis » natif, Ventes › Devis › Nouveau, le retour par le fil d'Ariane ou le rechargement de la page ; la loupe reste le moyen d'ouvrir la fenêtre dans ces cas. Le cas d'une opportunité sans pièce OE, avec seulement une ligne « Autres marques AM », est décrit en [4](04-piece-piece-am.md).

Détail de chaque champ : [technique/champs/sale-order.md](../../technique/champs/sale-order.md).
