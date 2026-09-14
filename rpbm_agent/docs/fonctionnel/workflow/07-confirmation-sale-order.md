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
| `x_studio_immatriculation_` | `state.immatriculationValue` | toujours |
| `x_studio_vehicle_id` | véhicule Odoo réutilisé ou créé (cf. [8 — Création du véhicule](08-creation-vehicule.md)) | si un véhicule est sélectionné |
| `x_studio_categorie_xglass` | `selectedCalque.libelle` | si une catégorie est sélectionnée |
| `x_studio_pice_concerne` (Pièce concernée) | suggestion X'Glass visible et modifiable | si une catégorie est sélectionnée — champ `related` vers l'opportunité |
| `x_studio_base_eurocode` | `state.baseEurocode` | si un eurocode est renseigné — fonctionne nativement ici, ce champ `related` porte déjà ce nom exact |
| `x_studio_many2one_field_rP62C` / `x_studio_many2one_field_DkgHx` | marque/modèle historiques de l'opportunité, préparés depuis Fleet | si une opportunité est liée et la correspondance est unique ; le référentiel manquant peut être créé à la confirmation |
| `x_studio_vin_` / `x_studio_dtails_modle` | VIN / détail modèle Fleet via l'opportunité | seulement si la source Fleet est renseignée |
| `x_studio_date_1re_mec` | date MEC Fleet via l'opportunité | seulement si renseignée, au format texte `MM/YYYY` |
| `x_studio_nergie_moteur` | énergie Fleet via l'opportunité | seulement pour les valeurs supportées ; variantes hybrides → `Hybride` |

- **Persistance** : identique à `crm.lead` — mise à jour en mémoire, écriture effective au clic sur « Enregistrer » (bouton « Confirmer ») ou immédiate via `record.save()` (bouton « Confirmer et enregistrer »).
- L'ajout ou le retrait d'un article principal ou suggéré au devis (`addArticleToSaleOrder()` / `removeArticleFromSaleOrder()`) est indépendant de cette étape. Chaque suggestion sélectionnée peut être ajoutée séparément ; seule une ligne créée par le widget dans la dialog courante peut être retirée — voir [9 — Création du produit](09-creation-produit.md).

La confirmation standard de la vente est une étape distincte de la confirmation
de la dialog. Elle exige un `carrier_id` pour toute vente à l'état brouillon ou
envoyée, mais ne crée pas de transporteur et ne modifie pas les lignes de vente.

Les informations Fleet sont préparées au moment de la confirmation par la
route interne `/prepareHistoricalVehicleFields`, puis fusionnées dans le même
`record.update()` que les autres champs. Une source vide, ambiguë, non
supportée ou non autorisée produit un avertissement sans bloquer et conserve
la valeur historique. Le kilométrage n'est jamais modifié. Sans opportunité
liée, le widget est masqué et aucune écriture dans les champs `related` n'est
proposée. Les informations de l'article principal restent indépendantes.

Détail de chaque champ : [technique/champs/sale-order.md](../../technique/champs/sale-order.md).
