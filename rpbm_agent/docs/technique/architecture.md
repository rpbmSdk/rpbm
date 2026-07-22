# Architecture

## Stack

- **Odoo 17** (`__manifest__.py` : `version: "17.0.250623.1"`), module `rpbm_agent`, dépend de `crm`, `fleet`, `sale_crm`.
- **Backend** : un seul controller Odoo (`AgentController`, `controllers/main.py`), toutes les routes en JSON-RPC (`type='json'`, `auth='user'`). Pas de modèle Python custom, pas de vue XML, pas de règle de sécurité (`ir.model.access.csv`) dans le module.
- **Intégration portails externes** : `requests.Session()` + `BeautifulSoup4` (scraping HTML/formulaires + quelques endpoints AJAX internes renvoyant du JSON). **Aucune API officielle**, aucun Selenium/Playwright.
- **Frontend** : composants OWL (framework de vues Odoo), déclarés en `web.assets_backend` (glob `rpbm_agent/static/src/*`). Le widget est injecté dans les vues formulaire **via Odoo Studio**, pas via des vues XML versionnées dans ce module.

## Vue d'ensemble des composants

```mermaid
flowchart LR
    subgraph Odoo["Odoo — backend"]
        Controller["AgentController<br/>controllers/main.py"]
        VSFAgent["VSFAgent<br/>controllers/vsf.py"]
        XGlassAgent["XGLASS<br/>controllers/xglass.py"]
        Controller --> VSFAgent
        Controller --> XGlassAgent
        Controller --> Models[("fleet.vehicle, crm.lead,<br/>sale.order, product.product,<br/>product.supplierinfo")]
    end

    subgraph Frontend["Odoo Web — OWL (assets_backend)"]
        Widget["AgentWidget<br/>(bouton loupe)"]
        Dialog["AgentWidgetDialog<br/>+ variantes CrmLead / SaleOrder"]
        Components["VehiculeComponent, CalqueComponent,<br/>PieceComponent, PieceAMComponent,<br/>ArticleComponent"]
        Widget --> Dialog --> Components
    end

    subgraph Externe["Portails externes"]
        XGlassPortal["portail-xglass.com"]
        VSFPortal["client.myvsf.fr"]
    end

    Dialog -- "JSON-RPC (service rpc)" --> Controller
    Components -- "JSON-RPC (service rpc)" --> Controller
    XGlassAgent -- "requests + BeautifulSoup<br/>scraping HTML/formulaires" --> XGlassPortal
    VSFAgent -- "requests + BeautifulSoup<br/>scraping HTML/formulaires" --> VSFPortal
```

Détail de chaque bloc : [backend](backend.md), [frontend](frontend.md).

## Séquence complète (cas Ordre de Vente)

```mermaid
sequenceDiagram
    actor U as Utilisateur
    participant FE as AgentWidgetDialog (OWL)
    participant BE as AgentController (Odoo)
    participant XG as Portail X'Glass
    participant VSF as Portail VSF
    participant ORM as Odoo ORM

    U->>FE: Clic sur le widget loupe
    FE->>BE: /rpbm_agent_auth
    BE->>XG: Authentification (formulaire + cookies)
    BE->>VSF: Authentification (formulaire + jeton CSRF)
    FE->>BE: /searchImmatriculation
    BE->>XG: POST /ajax/searchImmat.html
    XG-->>BE: JSON véhicules
    BE-->>FE: liste de véhicules
    U->>FE: Sélection d'un véhicule
    FE->>BE: /getOdooVehicule
    BE->>ORM: search fleet.vehicle (par immatriculation)
    ORM-->>BE: véhicule existant ou rien
    BE-->>FE: véhicule Odoo ou False
    FE->>BE: /getPlanche
    BE->>XG: POST /selectVehicule.html
    XG-->>BE: HTML (planche embarquée dans un <script>)
    BE-->>FE: planche (catégories/calques)
    U->>FE: Sélection d'une catégorie
    FE->>BE: /getPieces
    BE->>XG: GET /affichagePieces.html
    XG-->>BE: HTML (pièces embarquées dans un <script>)
    BE-->>FE: liste de pièces
    U->>FE: Sélection d'une pièce
    FE->>BE: /getPieceAm
    BE->>XG: POST /ajax/findSelectionsPiecesAmView.html
    XG-->>BE: JSON pièces après-marché
    BE-->>FE: pièces AM (contiennent l'eurocode)
    FE->>BE: /searchBaseEurocode
    BE->>VSF: GET /catalogue/vitrage + POST /catalogue/articles-client
    VSF-->>BE: HTML + JSON articles
    BE-->>FE: liste d'articles VSF
    U->>FE: Clic "Créer" sur un article (sale.order)
    FE->>BE: /createProduct
    BE->>ORM: create product.product + product.supplierinfo
    U->>FE: Clic "Confirm"
    FE->>BE: /rpbm_agent_close
    BE->>XG: GET /logout.html
    FE->>FE: record.update(data) — écriture en mémoire du formulaire
    U->>FE: Enregistrement du formulaire (bouton standard Odoo)
    FE->>ORM: write (sauvegarde effective en base)
```

## Points d'attention transverses

- **Aucune persistance de configuration versionnée** : les champs `x_studio_*` consommés par le code (frontend et backend) sont créés via Odoo Studio, donc dans la base de données de chaque instance Odoo, pas dans ce dépôt. Le module ne fonctionne pas "out of the box" sur une instance vierge sans avoir recréé ces champs (voir [configuration](configuration.md)).
- **Aucune sécurité applicative dédiée** : les routes sont ouvertes à tout utilisateur connecté (`auth='user'`), sans groupe ni `ir.model.access.csv` propre au module.
- **État de session partagé** : `vsfAgent`/`xglassAgent` sont des instances Python **au niveau module** (pas par utilisateur Odoo, pas par requête) — voir [backend](backend.md#état-de-session-partagé) et l'[état des lieux](../etat-des-lieux.md) pour l'implication en usage concurrent.
