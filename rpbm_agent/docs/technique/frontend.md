# Frontend (OWL)

## Articles VSF et suggestions

`AgentWidgetDialog` garde les sélections dans `selectedArticleCodes`, indexé par code VSF, et les produits Odoo dans `articleProducts`, également par code. Une carte sélectionnée possède donc son propre chargement, sa recherche/création produit et, sur un devis, son ajout ou retrait.

La sélection d'un article principal charge sa fiche et hydrate ses suggestions à un seul niveau. Les suggestions ne rejoignent jamais `articlesVsf` : elles restent sous leur principal. Une carte principale sélectionnée et son groupe de suggestions occupent toute la largeur de la grille, afin qu'aucun résultat voisin ne les intercale. Les aperçus d'images et les caractéristiques techniques restent compacts. Désélectionner le principal retire les sélections de ce groupe. `AgentWidgetDialogSaleOrder` mémorise uniquement les lignes qu'il a ajoutées pendant la dialog et appelle `order_line.delete(line)` pour les retirer sans toucher aux lignes préexistantes.

| Méthode JS | Composant | Usage |
|---|---|---|
| `toggleVsfArticle()` | `AgentWidgetDialog` | Sélection/désélection d'une carte et désélection du groupe parent |
| `findProductForArticle()` / `createProductForArticle()` | `AgentWidgetDialog` | Recherche ou création du produit de la carte concernée |
| `addArticleToSaleOrder()` / `removeArticleFromSaleOrder()` | `AgentWidgetDialogSaleOrder` | Ajout/retrait sûr d'une ligne créée par le widget |

Le placement du widget dans les formulaires (`<widget name="rpbm_agent_widget" />`) se fait par les **vues XML versionnées** du module (`views/crm_lead_views.xml`, `views/sale_order_views.xml`, etc. — voir [configuration](configuration.md#intégration-dans-les-vues)), chacune héritant de la vue formulaire de base du modèle.

## Arborescence des composants

```mermaid
flowchart TD
    AW["AgentWidget<br/>(bouton loupe, view_widgets)"] -->|"resModel == 'crm.lead'"| DCL[AgentWidgetDialogCrmLead]
    AW -->|"resModel == 'sale.order'"| DSO[AgentWidgetDialogSaleOrder]
    AW -->|autre modèle| DG[AgentWidgetDialog générique]
    DCL --> Base[AgentWidgetDialog]
    DSO --> Base
    Base --> VC[VehiculeComponent]
    Base --> CC[CalqueComponent]
    Base --> PC[PieceComponent]
    PC --> PAC[PieceAMComponent]
    Base --> AC["ArticleComponent<br/>(utilisé tel quel sur les deux modèles)"]
```

## Hiérarchie des classes

```mermaid
classDiagram
    class Component
    class asyncWidget
    class AgentWidgetDialog
    class AgentWidgetDialogCrmLead
    class AgentWidgetDialogSaleOrder
    class VehiculeComponent
    class ArticleComponent
    class CalqueComponent
    class PieceComponent
    class PieceAMComponent

    Component <|-- asyncWidget
    asyncWidget <|-- AgentWidgetDialog
    AgentWidgetDialog <|-- AgentWidgetDialogCrmLead
    AgentWidgetDialog <|-- AgentWidgetDialogSaleOrder
    asyncWidget <|-- VehiculeComponent
    asyncWidget <|-- ArticleComponent
    Component <|-- CalqueComponent
    Component <|-- PieceComponent
    Component <|-- PieceAMComponent
```

`asyncWidget` (`utils.js`) est la classe de base fournissant le service `rpc`, l'accès à
`record`, et `runAsync(fn, message)` — wrapper try/catch qui bascule un état de chargement
**propre à chaque composant** avant/après l'appel et affiche une notification Odoo en cas
d'erreur.

## Détails discriminants des pièces OE

Les pièces après-marché ne sont affichées que sous la pièce OE active, dans un encadré portant
explicitement son libellé. Cliquer de nouveau sur cette pièce la désélectionne et efface les
données qui en dépendent (pièce après-marché, eurocode, résultats et article VSF).

`PieceComponent` affiche les données déjà reçues par `/getPieces`, sans nouvel appel vers
X'Glass : référence OE, détail technique ou complément de libellé, couleur et caractéristiques
typées marquées discriminantes par le portail. L'affichage est limité à quatre lignes pour
préserver la lisibilité des cartes ; ces éléments distinguent notamment les capteurs, teintes,
chauffage, acoustique et états de livraison.

Dans la liste VSF, chaque article sélectionné possède son propre encart de création ou de
consultation Odoo. Une sélection par code permet de conserver plusieurs cartes en parallèle ;
retirer un principal retire aussi les suggestions de son groupe.

`ArticleComponent` expose un slot Owl optionnel `actions`, rendu dans le corps de la carte.
La dialog principale y injecte l'encart produit ; la dialog devis l'enrichit par héritage avec
l'ajout ou le retrait de la ligne. Le conteneur d'actions arrête la propagation du clic afin
qu'une action interne ne modifie pas la sélection de la carte. `h-100` est réservé aux cartes
non sélectionnées : une carte sélectionnée contenant ses actions garde une hauteur naturelle.

Au clic sur un article principal, le widget lit sa fiche VSF et hydrate les cartes de son
carrousel « références complémentaires » sans les ajouter aux résultats principaux. Les cartes
principales et suggérées partagent le même contenu (photo, référence, prix, stock et
caractéristiques) ; les suggestions ne sont pas développées récursivement. Les miniatures avec
une URL pleine taille signée par VSF ouvrent une prévisualisation dans une dialog Odoo.

### Hiérarchie des classes "record" (champs Odoo par modèle porteur)

```mermaid
classDiagram
    class AbstractRecord {
        +recordData
        +odooId
    }
    class AbstractWidgetRecord {
        +partnerField
        +categorieXglassField
        +vehiculeField
        +immatriculationField
        +baseEurocodeField
        +pieceConcerneeField
    }
    class CrmLead
    class SaleOrder
    AbstractRecord <|-- AbstractWidgetRecord
    AbstractWidgetRecord <|-- CrmLead
    AbstractWidgetRecord <|-- SaleOrder
```

`CrmLead` et `SaleOrder` surchargent certaines de ces propriétés avec des noms de champs `x_studio_*` différents selon le modèle (ex. `immatriculationField`, `baseEurocodeField`). Détail des noms de champs par classe/modèle : voir [technique/champs/](champs/README.md).

## Chaîne réactive (`useEffect`) de `AgentWidgetDialog`

Toute la progression du parcours (véhicule → planche → catégorie → pièces → pièce AM → eurocode → VSF) est pilotée par une cascade de `useEffect`, pas par des appels séquentiels explicites :

```mermaid
flowchart TD
    V[selectedVehicule change] --> P{selectedVehicule défini ?}
    P -->|Oui| GP["onGetPlanche() → GET /getPlanche"]
    P -->|Non| RP[planche = undefined]
    GP --> PL[planche change]
    PL --> C{"categorieXglass déjà renseignée sur le record ?"}
    C -->|Oui, calque trouvé| SC["onClickCalque() déclenché automatiquement"]
    C -->|Non| NC[selectedCalque = undefined]
    SC --> CA[selectedCalque change]
    CA --> GPi["getPieces() → GET /getPieces"]
    GPi --> PI[pieces change]
    PI --> SP["selectedPiece re-matché dans la nouvelle liste (ou réinitialisé)"]
    SP --> SPC[selectedPiece change]
    SPC --> GPA["getSelectedPieceAm() → GET /getPieceAm"]
    GPA --> PA[selectedPieceAm change]
    PA --> EU["baseEurocode = 5 premiers caractères de selectedPieceAm.pieceAm.reference"]
    EU --> EUC[baseEurocode change]
    EUC --> SB["onSearchBaseEurocode() → GET /searchBaseEurocode"]
```

Un `useEffect` séparé recalcule `state.canConfirm` à chaque changement de véhicule ou de
catégorie. Les boutons « Confirmer » et « Confirmer et enregistrer » restent désactivés tant
que ces deux sélections ne sont pas présentes.

## Table des appels serveur

| Méthode JS | Composant | Route | Usage |
|---|---|---|---|
| `auth_agents()` | `AgentWidgetDialog` | `/rpbm_agent_auth` | Connexion X'Glass + VSF |
| `closeAgents()` | `AgentWidgetDialog` | `/rpbm_agent_close` | Fermeture session X'Glass |
| `searchImmatriculation()` | `AgentWidgetDialog` | `/searchImmatriculation` | Recherche véhicule(s) par plaque |
| `getOdooVehicule()` | `AgentWidgetDialog` **et** `VehiculeComponent` | `/getOdooVehicule` | Véhicule Odoo existant (appelé en double, voir [état des lieux](../etat-des-lieux.md)) |
| `createOdooVehicule()` / `onClickCreateVehicule()` | `AgentWidgetDialog` et `VehiculeComponent` | `/createVehicule` | Création du véhicule |
| `getVehiculeMeta()` | `AgentWidgetDialog` pour le seul véhicule sélectionné | `/rpbm_agent/getVehiculeMeta` | VIN/CNIT/date MEC |
| `getPlanche()` | `AgentWidgetDialog` | `/getPlanche` | Catégories/calques disponibles |
| `getPieces()` | `AgentWidgetDialog` | `/getPieces` | Pièces d'une catégorie |
| `getPieceAm()` | `AgentWidgetDialog` | `/getPieceAm` | Pièces après-marché d'une pièce |
| `onSearchBaseEurocode()` | `AgentWidgetDialog` | `/searchBaseEurocode` | Articles VSF par eurocode |
| `findProductForArticle()` | `AgentWidgetDialog` | `/doesProductExists` | Recherche le produit existant pour une carte VSF donnée |
| `createProductForArticle()` | `AgentWidgetDialog` | `/createProduct` | Crée le produit + prix fournisseur pour cette carte |
| `addArticleToSaleOrder()` / `removeArticleFromSaleOrder()` | `AgentWidgetDialogSaleOrder` | — (pas de route, `record.data.order_line.addNewRecord` / `delete`) | Ajoute ou retire une ligne créée par le widget |

## Écriture finale

`AgentWidgetDialog.onConfirm()` / `onConfirmAndSave()` délèguent à `confirmRecord(save)`, qui
construit un objet `data` (via `getRecordData()`) et appelle
**`this.props.record.update(data)`** — mise à jour en mémoire du `Record` Odoo standard —
**avant** de fermer la session portail (`closeAgents()`, cf. correctif L1.0).
L'écriture effective en base se fait ensuite via le mécanisme de sauvegarde standard du
formulaire Odoo (bouton « Enregistrer »), ou directement avec « Confirmer et enregistrer ».
Le module n'utilise pas de `orm.write` : tous ses échanges serveur passent par `rpc` vers les
routes custom de `main.py`.
