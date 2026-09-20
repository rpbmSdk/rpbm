# AG-01-04 — Cartographie des rapports PDF et proposition de source par champ

## Statut

**Cartographie préparée le 14 septembre 2026, en lecture seule.** Ce document
couvre uniquement les items 1 et 2 du lot AG01-04 défini dans
[AG-01-champs-utiles.md](AG-01-champs-utiles.md#ag01-04--migrer-et-recetter-les-rapports) :
cartographier la chaîne QWeb complète de chaque rapport et proposer une source
canonique par information. **Aucune vue, aucun rapport et aucun fichier de code
n'a été modifié.** Les items 3 à 5 (migration effective des références,
vérification PDF, non-régression) restent à réaliser par `rpbm-luna-codeur` dans
une tâche ultérieure, à partir de la liste ordonnée en fin de document.

> **Correction apportée à l'implémentation (2026-09-14, même jour).** Les
> relevés d'occurrences des §1 et §2 ci-dessous ont été faits sur l'`arch_db`
> **brute** de chaque vue. Or les personnalisations Studio enchaînent des
> `position="replace"` successifs : une occurrence présente dans l'`arch_db`
> peut avoir été écrasée et ne jamais apparaître au rendu. La lecture de
> l'arch **combinée** (`ir.ui.view.get_combined_arch()`, lecture seule) montre
> que **1499 et 1591 n'ont aucun doublon** d'affichage, et qu'il n'existe pas
> deux blocs véhicule distincts sur 1505/1513 mais deux `span` voisins dans la
> même cellule. Par ailleurs, la source canonique marque/modèle proposée au
> §2bis est **inversée** : `x_studio_marque__1` / `x_studio_modle_` ne sont
> renseignés que sur **2 devis sur 7 353**, contre 7 211 et 7 182 pour
> `x_studio_many2one_field_rP62C` / `_DkgHx` — qui sont aussi les champs
> réellement écrits par AG01-01/02
> (`controllers/main.py`, `HISTORICAL_VEHICLE_FIELD_TARGETS`). Voir
> [roadmap.md](../roadmap.md) pour l'état livré et les questions restées
> ouvertes.

Sources utilisées :
- Snapshot local déjà acquis pour AG-01 (aucun nouvel appel réseau nécessaire) :
  [ir.actions.report.json](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/navigation/ir.actions.report.json)
  et [ir.ui.view.json](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/views/ir.ui.view.json)
  (`arch_db` complet des vues QWeb).
- Matrice de qualification déjà tranchée dans
  [AG-01-champs-utiles.md](AG-01-champs-utiles.md#matrice-de-qualification).
- Champs Fleet confirmés dans
  [ir.model.fields.json](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/fields/ir.model.fields.json)
  (`fleet.vehicle` : `license_plate`, `vin_sn`, `model_id`, `brand_id`, `odometer`,
  `odometer_count`, `fuel_type` ; `delivery.carrier` : `name`, `carrier_description`).

Contrainte reprise de l'audit mère : aucune proposition de ce document ne
supprime un champ existant, historique, obsolète ou déjà déployé. Il s'agit
uniquement de décisions de source pour la lecture des rapports.

## Périmètre

Les 6 familles de rapports déjà identifiées dans la table « Vérification des
rapports » de l'audit AG-01, toutes portant sur `sale.order` (sauf la
personnalisation `delivery`, portée par le module standard Odoo `delivery`) :

| Rapport | Action `ir.actions.report` | `report_name` |
|---|---|---|
| 1499 — RPBM Devis / Commande | id 1499, `binding_model_id` = Sales Order | `sale.report_saleorder_copy_1` |
| 1505 — RPBM - Ordre de Réparation | id 1505, `binding_model_id` = **False** | `studio_customization.studio_report_docume_68c213a6-96ed-4af6-95f7-3cd44f2ea2e9` |
| 1513 — RPBM OR | id 1513, `binding_model_id` = Sales Order | `sale.report_saleorder_copy_1_copy_1` |
| 1519 — RPBM Devis / Commande brouillon | id 1519, `binding_model_id` = **False** | `sale.report_saleorder_copy_1_copy_2` |
| 1591 — DBDG RPBM | id 1591, `binding_model_id` = Sales Order | `studio_customization.studio_report_docume_eea15ec8-ceb2-4a0d-8b71-c3f151eab511` |
| delivery — personnalisation du document natif | pas d'action dédiée ; vue `delivery.delivery_report_saleorder_document` (id 6519) | s'applique à `sale.report_saleorder` (action 467) et `sale.report_saleorder_raw` (action 2017) |

**Fait observé.** 1505 et 1519 ont `binding_model_id = False` : ils ne sont pas
rattachés au menu « Imprimer » standard du formulaire `sale.order` de la même
façon que 1499, 1513 et 1591. L'audit AG-01 note déjà qu'il ne peut pas
conclure quel rapport les équipes utilisent réellement quand plusieurs actions
portent des noms proches (limite reprise ci-dessous) ; ce fait renforce le
constat sans le résoudre — **à confirmer avec le métier** avant de prioriser un
rapport plutôt qu'un autre dans l'implémentation.

## 1. Chaîne QWeb complète par rapport

Convention reprise de l'audit mère : « racine » = vue primaire appelée par
`report_name`, « document » = vue primaire appelée par la racine via `t-call`,
« personnalisation » = vue Studio en `mode="extension"` qui hérite du document
par `xpath`. Tous les ids ci-dessous sont vérifiés dans `ir.ui.view.json`
(`arch_db`, `inherit_id`, `mode`, `priority`).

| Rapport | Racine | Document | Personnalisation | Constat sur la chaîne |
|---|---|---|---|---|
| 1499 | **4859** `sale.report_saleorder_copy_1` (`t-call` → 4860) | **4860** `sale.report_saleorder_document_copy_1` — arch vide de champ véhicule | **4861** `mode=extension`, `inherit_id=4860`, `priority=99` — tous les champs véhicule sont injectés ici par `xpath` | Chaîne à 3 niveaux classique |
| 1505 | **4887** `studio_main_report` (`t-call` → 4886) | **4886** — coquille Studio vide (`t-call="web.external_layout"><div class="page"/>`) | **4888** `mode=extension`, `inherit_id=4886`, `priority=99` — champs véhicule injectés, **en double** (voir §2) | Racine et document générés par Studio, tout le contenu vient de la personnalisation |
| 1513 | **4908** `sale.report_saleorder_copy_1_copy_1` (`t-call` → 4909) | **4909** `sale.report_saleorder_document_copy_1_copy_1` — **contient déjà** des champs véhicule en dur | **4910** `mode=extension`, `inherit_id=4909`, `priority=99` — ajoute un **second** bloc véhicule avec des champs différents | Duplication entre document et personnalisation (voir §2) |
| 1519 | **4920** `sale.report_saleorder_copy_1_copy_2` (`t-call` → 4921) | **4921** `sale.report_saleorder_document_copy_1_copy_2` — champs véhicule en dur, bloc unique | **Aucune.** Aucune vue du snapshot n'a `inherit_id=4921`. | Pas de couche de personnalisation Studio séparée |
| 1591 | **5324** `studio_main_report` (`t-call` → 5323) | **5323** — coquille Studio vide (identique au pattern de 4886) | **5325** `mode=extension`, `inherit_id=5323`, `priority=99` — champs véhicule (sous-ensemble) + champs sinistre/assurance hors périmètre véhicule | Racine/document Studio, contenu entièrement dans la personnalisation |
| delivery | — | **1104** `sale.report_saleorder_document` (natif, sans aucun champ `x_studio_*`/`x_rpbm_*`, vérifié) | **6519** `delivery.delivery_report_saleorder_document`, `inherit_id=1104`, insère `doc.carrier_id.carrier_description` avant `order_note` | **Cette vue n'est dans la chaîne d'aucun des 5 rapports ci-dessus.** Elle ne s'applique qu'aux rapports natifs 467 (`sale.report_saleorder` → 1105 → 1104) et 2017 (`sale.report_saleorder_raw` → 1104), tous deux hors du périmètre RPBM opérationnel. |

**Fait observé central.** Aucune des 5 racines RPBM/DBDG ne `t-call` vers
`sale.report_saleorder_document` (1104). Chacune duplique intégralement sa
propre vue « document ». La personnalisation `delivery` (6519), qui affiche
`carrier_id.carrier_description`, ne peut donc **jamais** s'afficher sur les
rapports 1499, 1505, 1513, 1519 ou 1591, quel que soit le contenu de
`sale.order.carrier_id`. C'est indépendant de la visibilité du champ dans le
formulaire (déjà traitée par AG01-03) : c'est une chaîne QWeb complètement
séparée.

## 2. Champs véhicule/logistique lus, par rapport

Relevé par recherche exhaustive de motifs (`x_studio_field_*`,
`x_studio_many2one_field_*`, `x_studio_vehicle*`, `x_rpbm_vehicle*`,
`carrier_id`, `vin_sn`, `license_plate`, champs marque/modèle/immatriculation/
VIN/kilométrage/pièce nommément) dans les `arch_db` extraits. Aucune occurrence
de `x_studio_vehicle_id`, `x_rpbm_vehicle_*`, `fleet.vehicle` ou `carrier_id`
n'a été trouvée dans les 5 personnalisations/documents RPBM — **le rendu PDF
actuel est entièrement déconnecté de Fleet et de `carrier_id`.**

### 1499 — RPBM Devis / Commande (vue 4861)

| Champ | Field name lu | Occurrences | Chemin |
|---|---|---|---|
| Marque | `x_studio_marque__1` | 1 | `doc.x_studio_marque__1` |
| Modèle | `x_studio_modle_` | 1 | `doc.x_studio_modle_` |
| Immatriculation | `x_studio_immatriculation_` | 1 | `doc.x_studio_immatriculation_` |
| VIN | `x_studio_vin_` | 5 (répété à plusieurs points d'insertion) | `doc.x_studio_vin_` |
| Kilométrage | `x_studio_kilomtrage__1` | 2 | `doc.x_studio_kilomtrage__1` |
| Pièce concernée | `x_studio_field_eENQz` | 5 (répété) | `doc.opportunity_id.x_studio_field_eENQz` — lu **directement sur le CRM**, pas via le related devis `x_studio_pice_concerne` |
| Lieu / carrier | — | 0 | absent |

### 1505 — RPBM - Ordre de Réparation (vue 4888)

Ce rapport affiche le véhicule via **deux familles de champs différentes** à
des endroits distincts du même document :

| Champ | Field name lu | Occurrences | Bloc |
|---|---|---|---|
| Marque | `x_studio_marque__1` | 4 | bloc texte (mirroir devis) |
| Marque | `x_studio_many2one_field_rP62C.x_name` | 1 | second bloc (m2o devis) |
| Modèle | `x_studio_modle_` | 1 | bloc texte |
| Modèle | `x_studio_many2one_field_DkgHx.x_name` | 1 | second bloc (m2o devis) |
| Immatriculation | `x_studio_immatriculation_` | 1 | bloc texte |
| VIN | `x_studio_vin_` | 1 | bloc texte |
| Kilométrage | `x_studio_kilomtrage__1` | 2 | bloc texte |
| Kilométrage | `x_studio_kilomtrage_1` | 1 | second bloc — **variante différente**, un seul underscore |
| Pièce concernée | `x_studio_field_eENQz` | 5 | `doc.opportunity_id.x_studio_field_eENQz` |
| Lieu / carrier | — | 0 | absent |

Autres champs hors périmètre véhicule repérés dans la même vue, sans lien
avec marque/modèle/VIN/immatriculation/kilométrage/pièce/lieu :
`x_studio_many2one_field_xiuBA` (modèle de devis produit),
`doc.user_id.user_id.x_studio_field_vBzC6`, `doc.opportunity_id.x_studio_field_37HTF`.

### 1513 — RPBM OR (document 4909 + personnalisation 4910)

Même schéma de duplication qu'en 1505, réparti entre document et
personnalisation :

| Champ | Field name lu | Vue | Occurrences |
|---|---|---|---|
| Marque | `x_studio_marque__1` | document 4909 | 1 |
| Marque | `x_studio_many2one_field_rP62C.x_name` | personnalisation 4910 | 1 |
| Modèle | `x_studio_modle_` | document 4909 | 1 |
| Modèle | `x_studio_many2one_field_DkgHx.x_name` | personnalisation 4910 | 1 |
| Immatriculation | `x_studio_immatriculation_` | document 4909 | 1 |
| VIN | `x_studio_vin_` | document 4909 | 1 |
| Kilométrage | `x_studio_kilomtrage__1` | document 4909 | 2 |
| Kilométrage | `x_studio_kilomtrage_1` | personnalisation 4910 | 1 |
| Pièce concernée | `x_studio_field_eENQz` | document 4909 | 1 |
| Lieu / carrier | — | — | 0 |

### 1519 — RPBM Devis / Commande brouillon (document 4921, sans personnalisation)

| Champ | Field name lu | Occurrences |
|---|---|---|
| Marque | `x_studio_marque__1` | 1 |
| Modèle | `x_studio_modle_` | 1 |
| Immatriculation | `x_studio_immatriculation_` | 1 |
| VIN | `x_studio_vin_` | 1 |
| Kilométrage | `x_studio_kilomtrage__1` | 2 |
| Pièce concernée | `x_studio_field_eENQz` | 1 (`doc.opportunity_id.x_studio_field_eENQz`) |
| Lieu / carrier | — | 0 |

C'est le seul des 5 rapports avec un bloc véhicule unique, sans duplication de
champ — cohérent avec son statut de brouillon, probablement créé avant les
ajouts manuels de bloc m2o constatés sur 1505/1513.

### 1591 — DBDG RPBM (vue 5325)

| Champ | Field name lu | Occurrences | Remarque |
|---|---|---|---|
| Marque | `x_studio_field_KyCjB` | 2 | lu **directement sur le CRM** via `doc.opportunity_id.x_studio_field_KyCjB` |
| Marque | `x_studio_marque__1` | 1 | lu sur le devis |
| Modèle | `x_studio_field_ZhaeY` | 1 | CRM, via `opportunity_id` |
| Modèle | `x_studio_modle_` | 1 | devis |
| Immatriculation | `x_studio_immatriculation_` | 1 | devis |
| VIN | — | 0 | absent de ce rapport |
| Kilométrage | — | 0 | absent de ce rapport |
| Pièce concernée | `x_studio_field_eENQz` | 1 | `doc.opportunity_id.x_studio_field_eENQz` |
| Lieu / carrier | — | 0 | absent |

**Point d'attention distinct.** Ce rapport lit aussi
`doc.x_studio_lieu_de_sinistre_` et `doc.x_studio_lieu_sinistre_` (2
variantes). **Ce n'est pas le lieu logistique/carrier** : au vu du contexte
(« DBDG Eurodommages », champs voisins `x_studio_circonstance` et
`x_studio_date_fin_contrat`), il s'agit du lieu du sinistre pour la déclaration
d'assurance. À ne pas confondre avec `x_studio_lieu_intervention` (lieu
d'intervention logistique historique, matrice AG-01) ni avec `carrier_id`. Ce
champ reste hors périmètre de la décision logistique d'AG01-04 ; il est
signalé ici pour éviter une confusion lors de l'implémentation.

### delivery (vue 6519)

| Champ | Field name lu | Portée réelle |
|---|---|---|
| Lieu / carrier | `doc.carrier_id.carrier_description` | Rapports natifs 467 (`sale.report_saleorder`) et 2017 (`sale.report_saleorder_raw`) uniquement — **aucun des 5 rapports RPBM/DBDG**. |

## Écart constaté avec la matrice de qualification AG-01

La matrice de [AG-01-champs-utiles.md](AG-01-champs-utiles.md#matrice-de-qualification)
catalogue pour « Marque » côté devis : `x_studio_many2one_field_rP62C` et
« affichages texte ». La lecture des `arch_db` des rapports confirme qu'un de
ces « affichages texte » est le champ `x_studio_marque__1`, utilisé dans
**les 5 rapports** (1499, 1505, 1513, 1519, 1591). Ce champ n'était pas nommé
explicitement dans la matrice mère. **Décision proposée : ajouter
`x_studio_marque__1` à l'inventaire AG01-05** (qualification des doublons),
au même titre que les trois variantes déjà cataloguées de kilométrage. Aucun
champ n'est visé pour suppression ; il s'agit seulement de compléter
l'inventaire.

## 2bis. Source canonique proposée par information

Application au niveau rapport de la règle de l'audit mère : *Fleet pour
l'identité véhicule, historique pour la compatibilité, `carrier_id` pour le
lieu logistique*. Les décisions ci-dessous s'appuient sur le fait qu'AG01-01/
AG01-02 (déjà livrés) font désormais écrire les données Fleet **dans les
champs historiques du devis** au moment de la confirmation de la dialog —
donc, pour les rapports, la migration proposée n'est pas « lire Fleet en
direct », mais « lire le champ historique unique que la dialog alimente
désormais », en remplaçant les variantes concurrentes.

| Information | Source canonique proposée pour les rapports | Justification |
|---|---|---|
| Lien véhicule | Pas de champ à afficher directement (aucun rapport n'imprime `x_studio_vehicle_id` aujourd'hui) | Hors périmètre d'affichage ; le lien Fleet sert à alimenter les champs ci-dessous, pas à être imprimé tel quel |
| Marque | `sale.order.x_studio_marque__1` (à défaut, `x_studio_many2one_field_rP62C`) — **un seul des deux à retenir, pas les deux dans le même document** | AG01-02 garantit que ce champ est renseigné depuis Fleet à la confirmation ; il couvre aussi les dossiers anciens. Le mapping Fleet → `x_rpbm_marques_voitures` reste une décision technique ouverte (AG01-01 item 4) — la consolidation du champ affiché ne dépend pas de cette décision, seule l'exactitude de sa valeur en dépend |
| Modèle | `sale.order.x_studio_modle_` (à défaut, `x_studio_many2one_field_DkgHx`) — même règle d'unicité | Idem marque |
| Immatriculation | `sale.order.x_studio_immatriculation_` (champ déjà unique dans tous les rapports, aucune consolidation nécessaire) | Related vers le CRM, alimenté par AG01-02 ; aucune variante concurrente trouvée dans les rapports |
| VIN | `sale.order.x_studio_vin_` (déjà unique) | Idem — alimenté par AG01-02, aucune variante concurrente dans les rapports |
| Kilométrage | **À confirmer avant migration (AG01-F05, non résolu)** — deux variantes vivent aujourd'hui dans les rapports (`x_studio_kilomtrage__1` et `x_studio_kilomtrage_1`) sans preuve de laquelle est la source de vérité | L'audit mère qualifie déjà ce champ « Redondance à confirmer ; aucune écriture automatique ». Migrer les rapports sur une valeur non tranchée risquerait de figer le mauvais choix. Recommandation : traiter AG01-F05 (mesure de remplissage + décision métier) avant l'item 3 de ce lot pour ce champ précis |
| Pièce concernée | `crm.lead.x_studio_field_eENQz`, lu via `opportunity_id` (déjà le choix uniforme dans les 5 rapports) | Champ structurant propre au métier, sans équivalent Fleet ; déjà cohérent partout, aucun changement de source nécessaire — mais le rapport reste vide sur un devis sans opportunité (cas déjà documenté par AG-01) |
| Lieu / carrier | `sale.order.carrier_id` (nom et/ou `carrier_description`), avec repli explicite sur `crm.lead.x_studio_lieu_intervention` pour les dossiers créés avant l'introduction de `carrier_id` | `carrier_id` est le champ natif désormais rendu visible et préremplissable par AG01-03 ; c'est la cible logistique canonique de l'audit mère. Le repli est nécessaire pour ne pas laisser un dossier ancien sans aucune indication de lieu (contrainte de non-régression du lot) |

## 3. Liste ordonnée des changements QWeb concrets pour l'implémentation (item 3)

Cette liste est un plan d'attaque pour `rpbm-luna-codeur`, pas une
implémentation. Chaque étape est bornée à une vue.

1. **Trancher AG01-F05 (kilométrage) avant de toucher aux rapports** — sans
   quoi l'étape 5 ci-dessous ne peut pas choisir entre `x_studio_kilomtrage__1`
   et `x_studio_kilomtrage_1`. Ce n'est pas une tâche QWeb ; c'est un
   préalable métier bloquant pour ce champ seulement (les autres champs
   peuvent avancer indépendamment).
2. **Vue 4861** (personnalisation de 1499) — dédupliquer les 5 insertions de
   `doc.x_studio_vin_` et les 2 de `doc.x_studio_kilomtrage__1` : conserver un
   seul point d'affichage par information dans le bloc véhicule, sans changer
   le champ source (déjà unique pour VIN/immatriculation dans ce rapport).
3. **Vue 4888** (personnalisation de 1505) — supprimer le second bloc
   véhicule qui lit `x_studio_many2one_field_rP62C.x_name`,
   `x_studio_many2one_field_DkgHx.x_name` et `x_studio_kilomtrage_1` ; ne
   conserver que le bloc qui lit `x_studio_marque__1`, `x_studio_modle_` et
   `x_studio_kilomtrage__1` (ou l'inverse, selon la décision de consolidation
   ci-dessus — les deux blocs ne doivent jamais survivre ensemble).
4. **Vue 4909 (document) + vue 4910 (personnalisation) de 1513** — même
   consolidation que l'étape 3 : un seul champ marque, un seul champ modèle,
   un seul champ kilométrage entre les deux vues.
5. **Vue 4921 (document de 1519)** — déjà un bloc unique ; vérifier
   uniquement que le champ kilométrage retenu correspond à la décision de
   l'étape 1, sans autre changement structurel.
6. **Vue 5325 (personnalisation de 1591)** — remplacer les lectures directes
   `doc.opportunity_id.x_studio_field_KyCjB` / `x_studio_field_ZhaeY` par les
   champs devis `x_studio_marque__1` / `x_studio_modle_` déjà présents dans la
   même vue, pour aligner ce rapport sur la même source que les 4 autres ; ne
   pas toucher à `x_studio_lieu_de_sinistre_` / `x_studio_lieu_sinistre_`
   (hors périmètre logistique, voir §2).
7. **Ajouter `carrier_id` dans les 5 documents/personnalisations** (4860/4861,
   4886/4888, 4909/4910, 4921, 5323/5325) — un ajout explicite par `xpath`
   dans chacun, calqué sur le motif de la vue 6519
   (`t-if="doc.carrier_id.carrier_description"`), avec repli sur
   `doc.opportunity_id.x_studio_lieu_intervention` quand `carrier_id` est vide
   (dossiers antérieurs à AG01-03). Cet ajout ne peut pas être mutualisé via
   héritage de 6519/1104 : la constatation du §1 montre que ces 5 vues ne
   passent jamais par cette chaîne.
8. **Compléter l'inventaire AG01-05** avec `x_studio_marque__1` (écart
   constaté ci-dessus), pour que la future qualification des doublons ne
   l'ignore pas.
9. **Recette PDF (item 4 du backlog AG01-04)** — une fois les étapes 2 à 7
   posées, générer les 5 PDF (RPBM, OR, DBDG, brouillon, delivery) pour un
   dossier ancien et un dossier créé avec le nouveau dialogue, et vérifier
   visuellement l'absence de doublon et la présence du lieu logistique.

## Limites et décisions encore requises

- Ce document ne mesure pas le taux de remplissage réel de
  `x_studio_marque__1` vs `x_studio_many2one_field_rP62C` vs les champs CRM —
  il constate seulement que les 5 rapports RPBM les lisent tous, avec des
  répartitions différentes selon le rapport.
- La consolidation marque/modèle proposée en §2bis suppose qu'un seul des
  champs concurrents suffit pour tous les usages actuels ; ce n'est pas
  démontré par les métadonnées seules et doit être vérifié sur un échantillon
  de dossiers réels avant l'implémentation (même limite que l'audit mère).
- Le mapping Fleet → `x_rpbm_marques_voitures` / `x_rpbm_modeles_voitures`
  (AG01-01 item 4) n'est pas résolu par ce document ; il conditionne
  uniquement l'exactitude future de la valeur des champs historiques, pas le
  choix du champ à afficher sur les rapports.
- Ce document ne confirme pas non plus quel rapport (1499, 1505, 1513, 1519)
  les équipes impriment réellement en pratique — `binding_model_id = False`
  sur 1505 et 1519 est un indice, pas une preuve.
- Le comportement d'impression d'un devis sans `opportunity_id` (pièce
  concernée vide, `opportunity_id.x_studio_lieu_intervention` inatteignable
  pour le repli logistique) doit être rejoué en recette, pas seulement déduit
  des `arch_db`.
