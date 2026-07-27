# Parcours utilisateur

## Point d'entrée

Le widget `rpbm_agent_widget` est une icône loupe (🔍) ajoutée par les vues versionnées du module (`views/crm_lead_views.xml`, `views/sale_order_views.xml` — voir [configuration](../technique/configuration.md#intégration-dans-les-vues)) sur **Piste/Opportunité** (`crm.lead`) et **Ordre de Vente** (`sale.order`). Un clic ouvre une fenêtre de dialogue qui pilote toute la recherche.

> Le comportement dépend du modèle sur lequel le widget est placé : voir [Finalisation](#finalisation-selon-le-modèle) plus bas pour les différences entre Piste/Opportunité et Ordre de Vente.

## Recherche et sélection (commun aux deux modèles)

```mermaid
flowchart TD
    A([Ouverture du widget]) --> B[Connexion aux portails X'Glass et VSF]
    B --> C{Immatriculation déjà renseignée sur l'enregistrement ?}
    C -->|Oui| D[Récupération automatique de la valeur]
    C -->|Non| E[Saisie manuelle + clic Search]
    D --> F[Recherche du véhicule sur X'Glass]
    E --> F
    F --> G[Affichage des véhicules trouvés]
    G --> H[Clic sur un véhicule pour le sélectionner]
    H --> I{Le véhicule existe déjà dans Odoo ?}
    I -->|Oui| J["Bouton 'Voir' → ouvre la fiche véhicule dans un nouvel onglet"]
    I -->|Non| K["Bouton 'Créer' → crée le véhicule dans Odoo"]
    H --> L["Clic sur 'Rechercher les Catégories'"]
    L --> M[Affichage des catégories / calques X'Glass disponibles pour le véhicule]
    M --> N[Clic sur une catégorie]
    N --> O[Affichage des pièces X'Glass de la catégorie]
    O --> P[Clic sur une pièce]
    P --> Q{Des pièces après-marché sont trouvées pour cette pièce ?}
    Q -->|Oui| R["Eurocode déduit automatiquement (5 premiers caractères de la référence)"]
    Q -->|Non| S["Champ Eurocode laissé vide : saisie manuelle possible"]
    R --> T[Recherche des articles sur VSF à partir de l'eurocode]
    S -.->|saisie + clic Chercher| T
    T --> U[Affichage des articles VSF disponibles]
```

Notes :
- Le premier véhicule de la liste est **sélectionné automatiquement** dès que la recherche renvoie des résultats.
- Si le conducteur (`driver_id`) du véhicule déjà présent dans Odoo diffère du client de l'enregistrement en cours, une alerte s'affiche.
- Si le champ "Catégorie X'Glass" est déjà renseigné sur l'enregistrement, la catégorie correspondante est présélectionnée automatiquement dès que la planche est chargée.
- La recherche VSF se relance automatiquement dès que le champ Eurocode change (saisie manuelle ou déduction automatique).

> ⚠️ Le diagramme visuel existant (`Readme.png`, généré via draw.io) libellait par erreur cette étape "Recherche du véhicule sur VSF" — la recherche véhicule se fait bien sur **X'Glass** ; VSF n'intervient qu'à l'étape de recherche par eurocode. Corrigé ci-dessus.

## Finalisation selon le modèle

### Piste / Opportunité (`crm.lead`)

```mermaid
flowchart TD
    U[Articles VSF affichés] --> V[Clic sur Confirmer]
    V --> W{Le véhicule sélectionné existe-t-il déjà dans Odoo ?}
    W -->|Non| X[Création du véhicule dans fleet.vehicle]
    W -->|Oui| Y[Réutilisation du véhicule existant]
    X --> Z[Écriture immatriculation + véhicule + catégorie + pièce concernée + eurocode sur la piste]
    Y --> Z
    Z --> AA[Fermeture de la fenêtre — la piste affiche les nouvelles données]
```

Champs écrits sur la piste (mise à jour en mémoire du formulaire, sauvegardés au clic sur "Enregistrer" — ou immédiatement via "Confirmer et enregistrer") : immatriculation, véhicule lié, catégorie X'Glass, Pièce concernée, Base Eurocode — détail exact des champs et de leurs conditions d'écriture dans [6 — Confirmation sur Piste/Opportunité](workflow/06-confirmation-crm-lead.md).

### Ordre de Vente (`sale.order`)

En plus du flux véhicule/catégorie/eurocode ci-dessus (identique), chaque article VSF affiché propose des actions supplémentaires :

```mermaid
flowchart TD
    U[Articles VSF affichés] --> W2{L'article existe-t-il déjà en tant que produit dans Odoo ?}
    W2 -->|Non| W3["Bouton 'Créer' → crée le product.product + prix fournisseur VSF"]
    W2 -->|Oui| W4["Bouton 'Voir' → ouvre la fiche article dans un nouvel onglet"]
    W3 --> W5["Bouton 'Ajouter' → ajoute une ligne au devis"]
    W4 --> W5
    W5 --> W6[Clic sur Confirmer pour finaliser véhicule/catégorie/eurocode sur le devis]
```

Champs/actions spécifiques à l'Ordre de Vente : immatriculation, véhicule lié, catégorie X'Glass, Pièce concernée, Base Eurocode — détail dans [7 — Confirmation sur Ordre de Vente](workflow/07-confirmation-sale-order.md). Le notebook du widget est masqué sur un devis sans opportunité liée. L'ajout au devis (`addToSaleOrder`) est **indépendant** du bouton "Confirm" de la fenêtre — on peut ajouter plusieurs articles avant de confirmer ; détail de la création de produit dans [9 — Création du produit](workflow/09-creation-produit.md).

## Prérequis avant utilisation

### Paramètres système

À créer dans `Réglages > Technique > Paramètres > Paramètres système` (`ir.config_parameter`) :

| Clé | Rôle |
|---|---|
| `XGLASS_USER` | Identifiant du portail X'Glass |
| `XGLASS_PASS` | Mot de passe du portail X'Glass |
| `VSF_LOGIN` | Identifiant du portail VSF |
| `VSF_PASSWORD` | Mot de passe du portail VSF |

### Champs Odoo Studio à créer

Les champs `x_studio_*` requis par le widget sont créés automatiquement à l'installation par `pre_init_hook` (voir [configuration technique](../technique/configuration.md#champs-odoo-studio-requis)). Inventaire complet par modèle (nom, type, rôle, champs obsolètes, structure des 3 champs Eurocode sur `crm.lead`) : [technique/champs/](../technique/champs/README.md).
