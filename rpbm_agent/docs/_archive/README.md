# Archive documentaire — sections erronées

Journal de suivi des **sections de documentation rendues fausses par des évolutions du code**,
archivées ici au lieu d'être supprimées sans trace. Chaque entrée cite le texte erroné, le
motif, et la correction appliquée dans le document vivant.

Ne pas rééditer ce fichier comme documentation courante : c'est un historique. La doc à jour
est dans [`../README.md`](../README.md).

Passe d'archivage : **2026-07-27** (revue de cohérence doc ↔ codebase).

---

## `technique/architecture.md`

### §Stack — version figée du manifest
> - **Odoo 17** (`__manifest__.py` : `version: "17.0.250623.1"`), module `rpbm_agent`, dépend de `crm`, `fleet`, `sale_crm`.

**Motif** : numéro de version figé, périmé (manifest réel `17.0.260727.1`) et voué à dériver à
chaque déploiement (le manifest est bumpé à chaque livraison).
**Correction** : la doc renvoie désormais à `__manifest__.py` sans citer le numéro exact.

### §Stack — absence de vues XML
> - **Backend** : un seul controller Odoo (`AgentController`, `controllers/main.py`), toutes les routes en JSON-RPC (`type='json'`, `auth='user'`). Pas de modèle Python custom, pas de vue XML, pas de règle de sécurité (`ir.model.access.csv`) dans le module.
> - **Frontend** : composants OWL (framework de vues Odoo), déclarés en `web.assets_backend` (glob `rpbm_agent/static/src/*`). Le widget est injecté dans les vues formulaire **via Odoo Studio**, pas via des vues XML versionnées dans ce module.

**Motif** : faux depuis l'ajout de `views/crm_lead_views.xml`, `views/sale_order_views.xml`,
`views/fleet_vehicle_views.xml`, `views/product_product_views.xml` (déclarées dans le manifest,
`data`). Le widget et les champs `x_studio_*` sont placés par ces vues, plus par Studio.
**Correction** : mention des vues versionnées, renvoi à `configuration.md#intégration-dans-les-vues`.

### §Séquence complète — ordre de `onConfirm`
> ```
>     U->>FE: Clic "Confirm"
>     FE->>BE: /rpbm_agent_close
>     BE->>XG: GET /logout.html
>     FE->>FE: record.update(data) — écriture en mémoire du formulaire
>     U->>FE: Enregistrement du formulaire (bouton standard Odoo)
> ```

**Motif** : ordre inversé. Le correctif L1.0 (`agent_widget_dialog.js::confirmRecord`) crée le
véhicule et écrit les champs **avant** de fermer la session : `getRecordData` → `record.update`
→ (`save` optionnel) → `closeAgents`. Fermer d'abord faisait échouer `createVehicule`. Le bouton
« Confirmer et enregistrer » (`onConfirmAndSave`) manquait aussi.
**Correction** : diagramme réordonné (update avant close) + branche « Confirmer et enregistrer ».

---

## `technique/frontend.md`

### Ligne 3 — absence de vues XML
> Aucune vue XML n'est versionnée dans le module : le placement du widget dans les formulaires (`<widget name="rpbm_agent_widget" />`) se fait via Odoo Studio, en base de données de chaque instance.

**Motif** : idem architecture.md — les vues sont désormais versionnées dans `views/*.xml`.
**Correction** : phrase remplacée par la description des vues versionnées.

### Diagrammes + prose — `SaleOrderArticleComponent`
> ```
>     Base --> AC["ArticleComponent<br/>(SaleOrderArticleComponent en sale.order)"]
> ```
> ```
>     class SaleOrderArticleComponent
>     ArticleComponent <|-- SaleOrderArticleComponent
> ```

**Motif** : `SaleOrderArticleComponent` n'existe plus dans le code (0 occurrence). Sur les deux
modèles, `ArticleComponent` est utilisé directement ; la logique produit/devis vit dans
`AgentWidgetDialog` (base) et `AgentWidgetDialogSaleOrder`.
**Correction** : classe retirée des diagrammes et de la prose.

### Diagramme des classes "record" — classes/props disparues
> ```
>     class SaleOrderLine {
>         +productId
>     }
>     AbstractRecord <|-- SaleOrderLine
> ```
> `CrmLead` et `SaleOrder` surchargent certaines de ces propriétés […] (certains, comme `SaleOrder.eurocodeField`, sont morts) : voir [technique/champs/] […]

**Motif** : `SaleOrderLine` et `SaleOrder.eurocodeField` n'existent plus (propriétés mortes
retirées, L3.4). Le diagramme omettait aussi `pieceConcerneeField`, ajouté à
`AbstractWidgetRecord`.
**Correction** : `SaleOrderLine`/`eurocodeField` retirés, `pieceConcerneeField` ajouté.

### Table des appels serveur — méthodes mal attribuées
> | `doesProductExists()` | `SaleOrderArticleComponent` | `/doesProductExists` | Vérifie l'existence du produit |
> | `createProduct()` | `SaleOrderArticleComponent` | `/createProduct` | Crée le produit + prix fournisseur |
> | `addToSaleOrder()` | `SaleOrderArticleComponent` | — (pas de route, manipulation directe de `record.data.order_line.addNewRecord`) | Ajoute une ligne au devis |

**Motif** : méthodes et composant erronés. Réel : `findSelectedProduct()` (`/doesProductExists`)
et `createSelectedProduct()` (`/createProduct`) dans la base `AgentWidgetDialog` ;
`addSelectedProductToSaleOrder()` dans `AgentWidgetDialogSaleOrder`.
**Correction** : lignes réécrites avec les vrais noms/composants.

---

## `fonctionnel/workflow/07-confirmation-sale-order.md`

### Ligne 17 — propriétés mortes inexistantes
> - `SaleOrder.eurocodeField` (`x_studio_eurocode`) et `SaleOrder.OrderlLines` sont des propriétés **mortes**, jamais utilisées dans `getRecordData()` (voir [état des lieux](../../etat-des-lieux.md)).

**Motif** : ces propriétés ont été supprimées (L3.4). La classe `SaleOrder`
(`agent_widget_dialog_sale_order.js`) ne définit plus que `immatriculationField`.
**Correction** : bullet supprimé.

### Ligne 18 — méthode renommée
> - L'ajout d'un article au devis (`addToSaleOrder()`) est **indépendant** de cette étape […]

**Motif** : `addToSaleOrder()` → `addSelectedProductToSaleOrder()`.
**Correction** : nom de méthode corrigé + table des champs complétée (`x_studio_field_eENQz`).

---

## `fonctionnel/workflow/06-confirmation-crm-lead.md`

### Ligne 4 — référence de code périmée
> - **Code** : `AgentWidgetDialog.onConfirm()` → `getRecordData()` (`agent_widget_dialog.js:226-258`) […]

**Motif** : le flux passe désormais par `onConfirm()` → `confirmRecord()` → `getRecordData()`
(`getRecordData` = lignes 241-267) ; le bouton « Confirmer et enregistrer » (`onConfirmAndSave`)
n'était pas mentionné.
**Correction** : chemin et persistance mis à jour.
