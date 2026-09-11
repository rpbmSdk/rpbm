# Rapport de qualite des donnees de migration

Date de generation : 2026-09-11
Source : Gestion Stock V4 - Stock Complet.csv (export du 29/01/2025)
Statut : preparation uniquement, aucune ecriture Odoo.

## Source CSV

| Controle | Resultat |
|---|---:|
| Lignes articles avec EUROCODE | 10063 |
| EUROCODE uniques | 3292 |
| References invalides (-, ---, ?) | 3 |
| References candidates import (eurocode normalise) | 3272 |
| Variantes de casse/espacement fusionnees | 17 |
| EUROCODE apparaissant plusieurs fois | 1358 |
| Lignes avec quantite actuelle positive | 768 |
| Quantite positive totale | 767.001 |
| Lignes sans DATE SORTIE | 769 |
| Emplacements source distincts | 568 |
| Types source distincts | 31 |
| EUROCODE au format suspect, exclu de l'import (D3) | 43 |
| **References effectivement importees** | **3229** |
| Fournisseurs (FRS) source distincts | 55 |
| References sans PRIX RV (cout non calculable) | 52 |
| References dont EUROCODE INTERNE diverge de EUROCODE | 51 |
| Sous-categories Autres distinctes | 7 |

Volumes par phase d'import, apres exclusion : 3229 produits,
2749 tarifs VSF + 388 tarifs autres fournisseurs, 3188 couts.

## Odoo preproduction lu via Paradigme MCP (releve du 2026-07-22)

- 13 categories produits existantes.
- 169 produits existants : 58 stockables, 75 consommables, 36 services.
- 1 entrepot actif : RPBM.
- 438 emplacements internes, dont 434 sous RPBM/Stock D1 et RPBM/Stock D2.
- Les categories existantes utilisent des politiques mixtes : average/real_time et standard/manual_periodic.

## Rapprochement catalogue Odoo

Aucun product_reconciliation.csv : le rapprochement du catalogue candidat avec les default_code Odoo reste a produire (phase P0). Sans lui, l'import peut creer un doublon pour chaque reference deja presente dans Odoo.

## Anomalies et risques

- Le CSV est anterieur a l'inventaire du 30/06/2026. Il ne constitue pas une source fiable pour le stock initial final.
- Les couleurs Google Sheets ne sont pas conservees dans le CSV; les statuts vendu/reserve/casse doivent etre confirmes par une colonne ou une source complementaire.
- GALLERIA et GENIPA sont des entrepots source; les valeurs JXX sont des emplacements dont l'entrepot parent reste a confirmer.
- La liste exhaustive des entrepots et le rattachement de chaque emplacement doivent etre fournis par les utilisateurs.
- Les lignes avec reference invalide sont exclues de products_to_import.csv et restent a investiguer.
- Le stock initial doit etre construit depuis l'inventaire valide du 30/06/2026.

## Prix fournisseurs et cout

- Les prix fournisseurs devront etre crees depuis PRIX ACHAT, apres rapprochement de FRS avec les fournisseurs Odoo.
- Decision RPBM du 2026-07-29 : ce rapprochement s'applique a **tous** les fournisseurs (FRS), pas seulement VSF - creer le res.partner Odoo manquant et le product.supplierinfo (PRIX ACHAT) pour chaque fournisseur non-VSF egalement (MPB, BLUE AUTO, A+ Glass, ...). Voir suppliers_mapping.csv.
- PRIX ACHAT est un prix unitaire; VALEUR (Av Fret) est probablement un montant de ligne avant fret : 760 lignes positives sur 768 suivent QTE Act x PRIX ACHAT.
- VALEUR est probablement un montant de ligne base sur PRIX RV : 761 lignes positives sur 768 suivent cette formule; elle ne doit pas devenir directement le cout unitaire Odoo.
- Decision RPBM du 2026-07-23 (D6) : le cout Odoo (standard_price) est la colonne PRIX RV, extraite dans products_to_import.csv (colonne cost_price). 52 references sur 3272 n'ont pas de PRIX RV exploitable et sont exclues de la phase de cout.
- Decision RPBM du 2026-08-05 (D7) : le fret est **inclus dans PRIX RV**. Aucune regle d'allocation a definir, la colonne FRET n'est pas reprise.
- Decision RPBM du 2026-08-05 (D8) : cout **standard** et valorisation **manuelle** - les valeurs par defaut d'Odoo 17, donc aucun compte comptable a parametrer. Ecrire standard_price sur des produits sans stock ne cree ni couche de valorisation ni ecriture comptable (_change_standard_price sort sur quantity_svl <= 0).

## Controle de format EUROCODE (2026-07-29, arbitre le 2026-08-05)

- 43 references sur 3272 (catalogue dedoublonne) ne passent pas le controle de format simple (alphanumerique + tiret, 4 a 15 caracteres) - voir eurocode_format_valide=false dans products_to_import.csv et la note associee sur chaque ligne concernee. Le format suspect indique une annotation, un code constructeur ou une donnee non-produit plutot qu'un vrai eurocode VSF.
- **Decision RPBM du 2026-08-05 (D3) : ces 43 references ne sont pas importees.** Sans x_studio_eurocode valide, elles seraient invisibles au widget rpbm_agent et non synchronisables a vie, tout en occupant une fiche Odoo. Le catalogue migre compte donc 3229 produits.
- Verification live contre le portail VSF ecartee (decision RPBM du 2026-07-29, D15) : risque de se faire reperer par le portail. A documenter si reconsideree plus tard, voir docs/cartographie/reconciliation-stock-rpbm-agent.md.

## Fichiers produits

- categories_mapping.csv : mapping des types sources vers les categories et sous-categories cibles.
- locations_mapping.csv : mapping des emplacements source et anomalies de rattachement.
- suppliers_mapping.csv : fournisseurs (FRS) source distincts, a rapprocher d'un res.partner Odoo existant ou a creer.
- products_to_import.csv : catalogue dedoublonne par EUROCODE, avec fournisseur retenu, cout PRIX RV et controle de format eurocode. La colonne import_status distingue les references importees de celles exclues pour format d'eurocode. Les colonnes d'audit (other_code, internal_eurocode, source_places) restent presentes pour le controle local mais ne sont plus reprises dans Odoo (D4).
- stock_initial_to_import.csv : modele vide volontairement.

Ces fichiers alimentent import_odoo.py, qui execute l'import phase par phase (voir
plan-import-articles.md). Les identifiants externes Odoo sont derives des libelles et des
references par import_odoo.py, ils ne sont pas stockes dans ces CSV.

## Decisions bloquantes

Etat au 2026-08-05 - le detail est dans decisions.md et questions-ouvertes.md.

Tranchees : categories et typologie (tous stockables), rattachement D1/D2 des racks, methode de
cout et valorisation, identite du partenaire VSF (id 5708), sort des eurocodes suspects, fret.

Restent bloquantes :

1. **Forme des entrepots** : 5 entrepots distincts ou 1 entrepot a 5 zones. Conditionne la creation
   des entrepots et le parent des emplacements.
2. **Fournir le fichier corrige de l'inventaire du 30/06/2026** - sans lui, stock_initial_to_import.csv
   reste vide et l'import du stock ne peut pas etre prepare.
3. **Arbitrer l'ecart d'inventaire de 6 448,18 EUR.**

A noter, independamment : le lot_stock_id de l'entrepot RPBM pointe sur RPBM/Stock D1, dont
GALLERIA, GENIPA et Stock D2 sont des freres et non des enfants - seules 67 unites sur 799 sont
aujourd'hui reservables par une commande client. A corriger avant mise en service.
