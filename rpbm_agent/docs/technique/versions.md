# Historique des versions

[Index](../README.md) › Technique › Historique des versions

Versions du manifeste ([`__manifest__.py`](../../__manifest__.py)) depuis le passage aux champs natifs `rpbm_*`,
relevées dans l'historique git (`git log -- rpbm_agent/__manifest__.py`). Le format est `17.0.AAMMJJ.N` : le
numéro suit la date de déploiement, qui peut précéder ou suivre d'un jour la date du commit. Chaque ligne reprend
l'objet du commit. L'avant-`17.0.260921.1` est dans l'historique git.

La version est bumpée à chaque modification déployée, sinon Odoo.sh ne recharge pas les assets du module
(consigne du [`CLAUDE.md`](../../CLAUDE.md) du module).

| Version | Commit (date) | Objet |
|---|---|---|
| `17.0.261022.2` | non commité (2026-10-22) | Fiche article : largeur, longueur et référence constructeur affichées sous l'eurocode, avant le code-barres ; `product.template.rpbm_constructor_reference` calculé depuis la variante unique, avec inverse (schéma de `default_code`, voir [champs](champs/product-product.md)). |
| `17.0.261022.1` | `79c2a77` (2026-10-22) | Eurocode en référence interne et prix fournisseur VSF au prix public avec remise : `/createProduct` écrit `default_code` = eurocode (la référence constructeur reste dans `rpbm_constructor_reference`) ; le tarif VSF porte `price` = prix public (`prixVente`) et `discount` = `rpbm_agent.vsf_discount` × 100 (20 %), le net reste celui d'Odoo (`price_discounted`) ; `_sync_vsf_supplierinfo` compare prix **et** remise. Eurocode affiché sous « Référence interne » sur les formulaires article et variante. Migration `post-vsf-public-price-eurocode.py` (voir [prix public et remise](configuration.md#prix-fournisseur-vsf-au-prix-public-avec-remise-1702610221)). |
| `17.0.261021.2` | `ef8f4bd` (2026-10-21) | Prix d'achat à 0 € sur une demande de prix datée avant le premier tarif VSF (PO00025) : ce premier tarif est créé sans date de début (`/createProduct`, `_sync_vsf_supplierinfo`) ; migration `post-vsf-first-price-date.py` qui retire la date de début du premier tarif VSF de chaque article (voir [premier tarif VSF](configuration.md#premier-tarif-vsf-sans-date-de-début-1702610212)). Journal de la recopie Studio → natif : nombres comparés arrondis, valeur Studio à 0 ignorée (voir [installation](configuration.md#installation--post_init_hook-et-migration-1702610152)). |
| `17.0.261021.1` | `4d33f45` (2026-10-21) | Réception refusée tant qu'une ligne reste sur un emplacement qui contient des racks (M4, `stock.picking._action_done`, voir [champs](champs/README.md)). Date et lieu de naissance sur la fiche client et l'opportunité (M7, [`res.partner`](champs/res-partner.md)). |
| `17.0.261016.1` | `6b17333` (2026-10-16) | L'assistant ne plante plus à la création d'un véhicule sans client (`partner_id` manquant à `/createVehicule`). |
| `17.0.261015.2` | `4fc39e3` (2026-10-16) | Eurocode, désignation et stock VSF de l'opportunité conservés à l'enregistrement d'un devis neuf : les miroirs Studio du devis renvoyés à leur valeur d'ouverture ne les effacent plus (voir [miroirs Studio du devis](configuration.md#miroirs-studio-du-devis-1702610152)). `post_init_hook` (`hooks.py`) qui rejoue la recopie Studio → natif et les rôles achats à l'installation, et migration `17.0.261015.2` qui rejoue la recopie sur la pré-prod installée à neuf ; natif renseigné jamais remplacé, écarts journalisés ; champs de facture repris du devis remplis quand ils sont vides (voir [installation](configuration.md#installation--post_init_hook-et-migration-1702610152)). |
| `17.0.261015.1` | `993a93d` (2026-10-15) | Barème X'Glass = prix de la pièce d'origine (IMP-1, VD-08 remplace VM-10) : `crm.lead.rpbm_xglass_piece_price` et son miroir sur le devis ; colonnes natives « Barème X'Glass HT » et « Prix fournisseur (net) » / « Fournisseur » (`rpbm_supplier_price`, `rpbm_supplier_id`) sur les lignes ; prix fournisseur VSF enregistré sur un article existant à l'ajout au devis (IMP-3) ; base Eurocode dérivée d'un eurocode seulement. Migration **pré** `pre-rpbm-supplier-columns.py` : colonnes créées sans recalcul des lignes historiques. Puis `Jobs/rpbm_agent_stock/studio_views.py apply` masque la colonne Studio « Prix XGlass ». |
| `17.0.261013.1` | `1768846` (2026-10-13) | Le Prix X'Glass saisi à la main sur une ligne de devis neuve n'est plus remis à 0 : un natif vide cède à la valeur Studio saisie. Voir [priorité en cas de double saisie](configuration.md#priorité-en-cas-de-double-saisie) et [`rpbm_pricing`](rpbm-pricing.md). |
| `17.0.261007.1` | `3706630` (2026-10-07) | Main-d'œuvre X'Glass enregistrée à l'opportunité et proposée sur le devis sans X'Glass (R30). Recette live réussie le 2026-10-07 (SO-11). |
| `17.0.261006.2` | `afa51df` (2026-10-06) | Devis ouvert en VSF d'abord, X'Glass à la demande (lot E2). |
| `17.0.261006.1` | `44b86e0` (2026-10-06) | Ligne ajoutée retrouvée par produit (R28) et page VSF sans résultat reconnue (R24). |
| `17.0.261005.4` | `98f70c2` (2026-10-05) | Articles VSF rattachés par code, pièce mémorisée conservée (lot E1.1). |
| `17.0.261005.3` | `9b4060c` (2026-10-05) | Création d'un devis depuis l'opportunité, véhicule X'Glass mémorisé (lot E1). |
| `17.0.261005.2` | `7bbe689` (2026-10-05) | Articles VSF en tableau et dialog plein écran (R21, R22). |
| `17.0.261005.1` | `67cfcdc` (2026-10-05) | Pièces X'Glass groupées, « Autres marques AM » repliées par famille. |
| `17.0.261002.5` | `c9714d9` (2026-10-02) | Navigation dans les images VSF (R16, R17). |
| `17.0.261002.4` | `28f506f` (2026-10-02) | Recherche VSF simplifiée (R13 à R15). |
| `17.0.261002.3` | `2ab66d1` (2026-10-02) | « Autres marques AM » par véhicule, reconnexion X'Glass avec contexte. |
| `17.0.261002.2` | `af79290` (2026-10-02) | Encart « Autres marques AM » sous la pièce sélectionnée. |
| `17.0.261002.1` | `844bf88` (2026-10-02) | Base Eurocode restaurée à la réouverture du widget. |
| `17.0.260929.1` | `c0ba714` (2026-09-29) | Fiches des suggestions VSF lues en parallèle. |
| `17.0.260928.4` | `f293a90` (2026-09-28) | Champs véhicule sur les factures, recherches et listes natives. |
| `17.0.260928.3` | `1e9e233` (2026-09-28) | Migration des rôles achats renumérotée (la version `.1` était déjà déployée). Voir [droits et rôles](configuration.md#droits-et-rôles). |
| `17.0.260928.2` | `90b18f5` (2026-09-28) | Devis rechargé après un enregistrement depuis le widget. |
| `17.0.260928.1` | `91fc116` (2026-09-28) | Droits Fleet des commerciaux sans groupe Parc automobile. |
| `17.0.260921.10` | `cd2aa05` (2026-09-20) | Recherche VSF relancée quand aucune liste n'est affichée. |
| `17.0.260921.9` | `8ff940e` (2026-09-20) | Erreur d'authentification des portails affichée dans la dialog. |
| `17.0.260921.8` | `d3b9c93` (2026-09-20) | Verrou par plaque à la création du véhicule, lignes de main-d'œuvre détectées par clé. |
| `17.0.260921.7` | `06fb3c9` (2026-09-20) | Véhicule Fleet créé par nom normalisé de marque et de modèle (recette du build 37939198). |
| `17.0.260921.6` | `599f0d3` (2026-09-20) | Migration rejouée pour les dates de mise en circulation et les champs conservés à tort. Voir [migrations](configuration.md#migrations-1702609216-et-1702609283). |
| `17.0.260921.5` | `0928e0a` (2026-09-20) | Colonnes Studio citées dans la migration des champs natifs. |
| `17.0.260921.4` | `2e714ee` (2026-09-20) | Documentation sur les champs natifs et la synchronisation Studio (lot 5). |
| `17.0.260921.3` | `436a50e` (2026-09-20) | Vues sur les champs natifs (lot 3). |
| `17.0.260921.2` | `86ed079` (2026-09-20) | Widget sur les champs natifs (lot 2). |
| `17.0.260921.1` | `87a8b85` (2026-09-20) | Champs natifs `rpbm_*` et migration depuis Studio (lot 1). Voir [migration `17.0.260921.1`](configuration.md#migration-1702609211). |

Les droits achats (`security/rpbm_groups.xml`, migration `17.0.260928.3`) sont décrits dans
[configuration](configuration.md#droits-et-rôles). Le commit `3dfe988` les avait introduits sous
`17.0.260928.1` avant la renumérotation en `.3`.

---
Précédent : [Interaction avec rpbm_pricing](rpbm-pricing.md) · Suivant : [Champs Odoo par modèle](champs/README.md)

Voir aussi : [Directives — module rpbm_agent](../../CLAUDE.md) · [Configuration & déploiement](configuration.md)
