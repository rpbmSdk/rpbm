# Recette widget rpbm_agent — constats du 2026-09-20 (build 37939198, run `20260920`)

Exécution hybride : `recette_widget.py` (prepare/verify) + phases navigateur jouées avec Claude in
Chrome dans un onglet du profil (session Odoo d'un administrateur), helper `recette_widget.js`.
Versions déployées successivement pendant la recette : `17.0.260921.5` → `.6` → `.7` → `.8`.

## Défauts trouvés et corrigés (commits sur `pre-prod`)

| # | Constat | Cause | Correctif |
|---|---|---|---|
| D1 | Build `2e714ee` en échec : `column "x_studio_field_nviod" does not exist` | identifiants Studio non cités dans le SQL de migration (Postgres replie en minuscules) | `0928e0a` — `_copy_column` et backfill marque/modèle citent les colonnes |
| D2 | 44 % des dates de mise en circulation non migrées ; 9 champs de l'ancien module conservés | formats `MM/YY`, `YYYY`, `JJ/MM/AAAA` non gérés ; garde de références bloquée par des champs de la même liste, homonymes d'autres modèles et miroirs `_inherits` | `599f0d3` — convertisseur et SQL élargis, `referenced_elsewhere` filtre par modèle et résout la cible `related`, suppression en passes ; migration `17.0.260921.6` rejoue la `.1` |
| D3 | « Créer » le véhicule : `Expected singleton: fleet.vehicle.model(174, 806)` | deux modèles « MEGANE » (marques « Renault » et « RENAULT ») ; recherche par nom seul | `06fb3c9` — `createVehicule` passe par `NameIndex` (nom normalisé, modèle restreint à sa marque) |
| D4 | Deux véhicules Fleet créés pour `BF857CZ` (ids 5 et 6, même seconde) | « Créer » puis « Confirmer » avant la fin du premier appel ; les deux recherches ne trouvent rien | `d3b9c93` — verrou `pg_advisory_xact_lock` par plaque dans `createVehicule` |
| D5 | Sur le devis, « Retirer » jamais affiché après ajout d'une opération de MO ; 4 lignes T2 identiques ajoutées | `isLaborOperationInOrder` comparait l'objet renvoyé par `addNewRecord` à `records` (identité) | `d3b9c93` — détection par `rpbm_labor_operation_key` |
| D6 | Refus du portail VSF : la dialog reste sur « Authentification des agents en cours… » sans message | `t-if="!agentsInitialized"` affiche le spinner quel que soit l'état ; l'erreur n'était que dans une notification fugace | (ce lot) — état `authError` + bouton « Réessayer » |

## Constats non corrigés (à qualifier)

| # | Constat | Détail |
|---|---|---|
| C1 | Portail VSF : connexion refusée à partir de 13:20 (« identifiants refusés ou page inattendue ») après ~6 ouvertures de dialog en 30 min | Page de connexion VSF normale (jeton CSRF, champs login/password/customer_id) ; blocage côté compte probable. Une seule session VSF à la fois ? À confirmer avec VSF. Bloque la ligne article, la vente et le scénario W3 tant que le portail refuse. |
| C2 | Base Eurocode dérivée de la référence de la pièce après-marché sélectionnée (5 premiers caractères) | Avec une référence OE (`4031842`), base « 40318 » et recherche VSF hors sujet ; changer de pièce AM n'a pas recalculé la base lors du premier essai (à reproduire). Le helper privilégie désormais une référence de forme eurocode. |
| C3 | Champs Studio obligatoires sur la vue formulaire (« Moyen 1er Contact », « Comment Connu ? ») | « Confirmer et enregistrer » échoue tant qu'ils sont vides ; `prepare` les renseigne désormais (valeurs arbitraires). |
| C4 | Référentiels Fleet en doublon : marques « Renault » (52) / « RENAULT » (69), modèles « MEGANE » 174 et 806 | Créés par le backfill depuis les référentiels Studio (deux graphies). Fusion à prévoir dans le chantier d'assainissement. |
| C5 | Deux véhicules `BF857CZ` (5 et 6) en base de développement | Produit du défaut D4 ; conservés (pas de nettoyage sur les bases de développement). |
| C6 | Un appel `/getPlanche` par sélection de pièce (attendu : aucun) | À vérifier dans `getSelectedPieceAm` ; sans impact fonctionnel constaté. |

## Ce qui est validé

Voir `20260920-recette-widget.md` (rapport `verify`). Résumé : création d'opportunité, recherche
plaque X'Glass, catégorie, pièce, pièce après-marché, recherche et sélection d'article VSF, article
principal, produit existant retrouvé par eurocode, création du véhicule Fleet (VIN, énergie, MEC,
détail, conducteur = client), report des 19 champs natifs `rpbm_*` sur l'opportunité, double
alimentation des 14 champs Studio historiques, devis lié avec transporteur prérempli
(« Retrait / pose Galleria »), miroirs natifs du devis, restauration des sélections dans la dialog
du devis, ligne de main-d'œuvre T2 (1,9 h, 90,32 €, clé d'opération).
