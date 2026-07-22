# Parcours utilisateur

## Point d'entrée

Le widget `rpbm_agent_widget` est une icône loupe (🔍) placée manuellement (via Odoo Studio) sur une vue formulaire — aujourd'hui utilisé sur **Piste/Opportunité** (`crm.lead`) et **Ordre de Vente** (`sale.order`). Un clic ouvre une fenêtre de dialogue qui pilote toute la recherche.

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
    X --> Z[Écriture immatriculation + véhicule + catégorie + eurocode sur la piste]
    Y --> Z
    Z --> AA[Fermeture de la fenêtre — la piste affiche les nouvelles données]
```

Champs écrits sur la piste (mise à jour en mémoire du formulaire, sauvegardés au clic sur "Enregistrer" comme tout formulaire Odoo standard) :
- `x_studio_field_NVioD` (immatriculation)
- `x_studio_vehicle_id` (véhicule lié)
- `x_studio_categorie_xglass`
- `x_studio_base_eurocode`

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

Champs/actions spécifiques à l'Ordre de Vente :
- Champ immatriculation : `x_studio_immatriculation_`
- L'ajout au devis (`addToSaleOrder`) est **indépendant** du bouton "Confirm" de la fenêtre — on peut ajouter plusieurs articles avant de confirmer.
- Lors de la création d'un article (`Créer`), Odoo enregistre :
  - un `product.product` : nom, référence (`default_code`), prix de vente, référence constructeur, image, description (lien vers la fiche VSF)
  - un `product.supplierinfo` associé (fournisseur VSF, prix d'achat remisé RPBM)

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

Le module ne déclare aucun modèle ni vue (voir [architecture](../technique/architecture.md)) : ces champs doivent être créés manuellement via Odoo Studio avant utilisation.

**Véhicule — `fleet.vehicle`**
| Champ | Rôle |
|---|---|
| `x_studio_detail_model` | Détail du modèle (ex : `KIA PICANTO III PHASE 2 - 5P 2020-09-> 1.2i 85`) |
| `x_studio_date_mec` | Date de mise en circulation |
| `x_studio_autre_infos` | Autres informations (non utilisé actuellement) |
| `x_studio_note` | Champ HTML calculé affichant un résumé du véhicule |

**Piste / Opportunité — `crm.lead`**
| Champ | Rôle |
|---|---|
| `x_studio_field_NVioD` | Immatriculation — champ historique conservé (lié aux factures/commandes), rendu calculé à partir du véhicule lié |
| `x_studio_field_KyCjB` / `x_studio_field_ZhaeY` | Marque/modèle véhicule — **obsolètes** (marqués `[Obsolète]`), non fiables historiquement (doublons, créations sauvages) |
| `x_studio_vehicle_id` | Many2one vers `fleet.vehicle` |
| `x_studio_categorie_xglass` | Catégorie X'Glass sélectionnée (ex : Pare-brise) |
| `x_studio_base_eurocode` | Base Eurocode sélectionnée |

**Ordre de vente — `sale.order`**
| Champ | Rôle |
|---|---|
| `x_studio_vehicle_id` | Many2one vers `fleet.vehicle`, lié à celui de la piste |
| `x_studio_categorie_xglass` | Lié à celui de la piste |
| `x_studio_base_eurocode` | Lié à celui de la piste |

Détails d'installation complets : [configuration technique](../technique/configuration.md).
