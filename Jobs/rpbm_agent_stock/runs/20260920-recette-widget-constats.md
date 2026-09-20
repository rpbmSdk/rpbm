# Recette widget rpbm_agent — constats du 2026-09-20 (build 37939198, run `20260920`)

Exécution hybride : `recette_widget.py` (prepare/migration/verify) + phases navigateur jouées avec
Claude in Chrome dans un onglet du profil (session Odoo d'un administrateur), helper
`recette_widget.js`. Versions déployées pendant la recette : `17.0.260921.5` → `.6` → `.7` → `.8`
→ `.9` (les correctifs ci-dessous ont été poussés au fil de l'eau). Interruption de 13:05 à 14:20 :
portail VSF en maintenance (HTTP 503 après le POST de connexion).

**Verdict final (`20260920-recette-widget.md`) : 37 PASS, 0 WARN, 0 FAIL.**

## Défauts trouvés et corrigés (commits sur `pre-prod`)

| # | Constat | Cause | Correctif |
|---|---|---|---|
| D1 | Build `2e714ee` en échec : `column "x_studio_field_nviod" does not exist` | identifiants Studio non cités dans le SQL de migration (Postgres replie en minuscules) | `0928e0a` — `_copy_column` et backfill marque/modèle citent les colonnes |
| D2 | 44 % des dates de mise en circulation non migrées ; 9 champs de l'ancien module conservés | formats `MM/YY`, `YYYY`, `JJ/MM/AAAA` non gérés ; garde de références bloquée par des champs de la même liste, homonymes d'autres modèles et miroirs `_inherits` | `599f0d3` — convertisseur et SQL élargis, `referenced_elsewhere` filtre par modèle et résout la cible `related`, suppression en passes ; migration `17.0.260921.6` rejoue la `.1` |
| D3 | « Créer » le véhicule : `Expected singleton: fleet.vehicle.model(174, 806)` | deux modèles « MEGANE » (marques « Renault » et « RENAULT ») ; recherche par nom seul | `06fb3c9` — `createVehicule` passe par `NameIndex` (nom normalisé, modèle restreint à sa marque) |
| D4 | Deux véhicules Fleet créés pour `BF857CZ` (ids 5 et 6, même seconde) | « Créer » puis « Confirmer » avant la fin du premier appel ; les deux recherches ne trouvent rien | `d3b9c93` — verrou `pg_advisory_xact_lock` par plaque dans `createVehicule` |
| D5 | Sur le devis, « Retirer » jamais affiché après ajout d'une opération de MO ; 4 lignes T2 identiques ajoutées | `isLaborOperationInOrder` comparait l'objet renvoyé par `addNewRecord` à `records` (identité) | `d3b9c93` — détection par `rpbm_labor_operation_key` |
| D6 | Refus du portail : la dialog reste sur « Authentification des agents en cours… » sans message | `t-if="!agentsInitialized"` affiche le spinner quel que soit l'état ; l'erreur n'était que dans une notification fugace | `8ff940e` — état `authError` + bouton « Réessayer » |
| D7 | Sur le devis, « Rechercher sur VSF » muet après restauration de la base (aucune carte, requête serveur pourtant OK) | garde « même base déjà cherchée » sans vérifier qu'une liste est affichée | (ce lot) — la garde exige aussi `articlesVsf.length` |

## Constats non corrigés (à qualifier)

| # | Constat | Détail |
|---|---|---|
| C1 | Portail VSF en maintenance de ~13:05 à ~14:20 (HTTP 503 après le POST de connexion, page de connexion normale) | Le module l'affiche comme « identifiants refusés » / « portail inaccessible » ; message trompeur mais comportement sûr. Un test HTTP dédié (voir `probe_vsf.py` de session) distinguerait maintenance et identifiants. |
| C2 | Base Eurocode dérivée de la référence de la pièce après-marché sélectionnée (5 premiers caractères) | Avec une référence OE (`4031842`), base « 40318 » et recherche VSF hors sujet ; changer de pièce AM n'a pas recalculé la base lors du premier essai (à reproduire). Le helper privilégie désormais une référence de forme eurocode. |
| C3 | Champs Studio obligatoires sur la vue formulaire (« Moyen 1er Contact », « Comment Connu ? ») | « Confirmer et enregistrer » échoue tant qu'ils sont vides ; `prepare` les renseigne désormais (valeurs arbitraires). |
| C4 | Référentiels Fleet en doublon : marques « Renault » (52) / « RENAULT » (69), modèles « MEGANE » 174 et 806 | Créés par le backfill depuis les référentiels Studio (deux graphies). Fusion à prévoir dans le chantier d'assainissement. |
| C5 | Deux véhicules `BF857CZ` (5 et 6) en base de développement | Produit du défaut D4 ; conservés (pas de nettoyage sur les bases de développement). |
| C6 | Un appel `/getPlanche` par sélection de pièce (attendu : aucun) | À vérifier dans `getSelectedPieceAm` ; sans impact fonctionnel constaté. |
| C7 | « Confirmer » exige véhicule **et** catégorie (`canConfirm`) | Le scénario « véhicule existant » (W3) ne peut pas être enregistré sans choisir une catégorie ; comportement voulu ? À trancher côté métier. |
| C8 | « Retirer du devis » absent après « Ajouter au devis » (ligne pourtant ajoutée) | Même mécanisme d'identité que D5, côté article (`isWidgetArticleInOrder`) ; à corriger de la même façon si confirmé. |
| C9 | Prix affiché dans la liste des lignes du devis avant enregistrement (104,03) ≠ prix en base après automatisation Studio (170,10 = 113,40 × 1,5) | Attendu : l'automatisation « Tarif x glass » s'applique à l'écriture ; le formulaire n'est rafraîchi qu'après enregistrement. |

## Ce qui est validé

Voir `20260920-recette-widget.md` (rapport `verify`). Création d'opportunité, recherche plaque
X'Glass, catégorie, pièce, pièce après-marché, recherche et sélection d'article VSF, article
principal, produit existant retrouvé par eurocode, création du véhicule Fleet (VIN, énergie, MEC,
détail, conducteur = client), report des 19 champs natifs `rpbm_*` sur l'opportunité, double
alimentation des 14 champs Studio historiques, devis lié avec transporteur prérempli
(« Retrait / pose Galleria »), miroirs natifs du devis, restauration des sélections dans la dialog
du devis, ligne article VSF (prix 113,40 → 170,10 par l'automatisation Studio, `rpbm_xglass_price`
et `x_studio_prix_x_glass` alimentés), ligne de main-d'œuvre T2 (1,9 h, 90,32 €, clé d'opération),
vente confirmée (SO7753), livraison `RPBM/GALL/OUT/00001` et transfert `RPBM/DEP-GALL/00001`
portant `rpbm_vehicle_id`, scénario W3 : véhicule `FQ581EN` existant reconnu (« existe en BDD »,
alerte conducteur différent) et lié à l'opportunité sans création.

Captures : `20260920-captures/W1-opportunite.jpg`, `W2-devis-confirme.jpg`, `W3-vehicule-existant.jpg`.
