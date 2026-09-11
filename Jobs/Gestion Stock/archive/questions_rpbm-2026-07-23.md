# Questions et validations à obtenir de RPBM avant import Odoo

Ce document consolide, par thème, l'ensemble des questions ouvertes et décisions bloquantes identifiées dans `README.md`, `infos.md`, `procédure actuelle stock.md` et `data_quality_report.md`.

Aucune écriture Odoo (catégories, produits, emplacements, stock) ne doit être effectuée tant que les points restants ne sont pas tranchés par RPBM.

**Retour client du 2026-07-23** : l'architecture globale proposée (catégories + arborescence d'emplacements) est validée. Détail des réponses par thème ci-dessous ; les points encore ouverts restent à trancher.

## 1. Catégories produits

- [x] Architecture de catégories proposée → **validée** par le client.
- [x] Regroupement `CAMERA` → reste dans la catégorie `Autres`, **sans sous-catégorie dédiée** (article rare, exception explicite maintenue).
- [x] **Décision du 2026-07-23 (revient sur le choix initial)** : les regroupements `Rétroviseur EXT`, `Rétroviseur INT`, `Cache rétro`, `Lève-vitre`, `Toit panoramique`, `Optique`, `Baie de pare-brise` deviennent de **vraies sous-catégories Odoo** imbriquées sous `Autres` (et non plus de simples libellés de produit normalisés). Répercuté dans `categories_mapping.csv` et `categories_odoo_proposition.csv`.
- [ ] Confirmer que `Accessoires` et `Main d'Oeuvre` (déjà présentes sous `All / Saleable` en préproduction) doivent être réutilisées telles quelles, sans les recréer.

## 2. Typologie produit

- [ ] Pour les consommables (kit colle, gel capteur, agrafes kit, cale pare-brise, produit connexe) : suivi en stock réel strict, en consommable non valorisé, ou achat/consommation simplifié sans suivi unitaire ?
- [ ] Confirmer la distinction stockable / consommable / service pour les cas limites restants.

## 3. Emplacements et dépôts

- [x] Existe-t-il d'autres entrepôts que `GALLERIA` et `GENIPA` ? → Oui : `Galleria` et `Genipa` sont les **entrepôts principaux** ; il existe aussi des **entrepôts déportés** `Dépôt 1` et `Dépôt 2`.
- [x] **Décision du 2026-07-23** : `Galleria`, `Genipa`, `Dépôt 1`, `Dépôt 2` et `Camion` seront **5 entrepôts Odoo distincts** (`stock.warehouse`), pas de simples emplacements imbriqués sous l'entrepôt `RPBM` existant.
  - ⚠️ **Point d'attention nouveau** : en préproduction, `Dépôt 1`/`D1` et `Dépôt 2`/`D2` existent déjà comme **emplacements** sous l'entrepôt unique `RPBM` (434 emplacements sous `RPBM/Stock D1` et `RPBM/Stock D2`, cf. `README.md`/`data_quality_report.md`). Les promouvoir en entrepôts autonomes implique une restructuration de l'existant, pas une simple création — à traiter avec précaution, pas en écriture directe non contrôlée.
- [x] Répartition des racks entre Dépôt 1 et Dépôt 2 → **tranchée le 2026-08-05** : `R101` à `R336` → Dépôt 1 ; `R401` à `R937`, `J…` et `T…` → Dépôt 2. Les bornes tombent exactement sur la frontière réelle des blocs. La numérotation `R` compte **9 blocs** (`R1xx` 101-136, `R2xx` 201-236, `R3xx` 301-336, `R4xx` 401-436, `R5xx` 501-538, `R6xx` 601-642, `R7xx` 701-739, `R8xx` 801-837, `R9xx` 900-937) et non 7 s'arrêtant à `R728` comme indiqué précédemment.
  - Couverture : 489 emplacements rattachés (109 Dépôt 1, 380 Dépôt 2), **49 laissés sous `A controler`**.
- [ ] Sort des 49 emplacements non rattachés (cellules multi-racks, libellés non codifiés, statuts, entrepôts sans emplacement précis) → **ignorés pour l'instant** par décision du 2026-08-05, à arbitrer plus tard. Liste imprimée par la phase `locations`.
- [x] Règle de création des emplacements → **un emplacement Odoo par référence distincte** de la colonne `Place` (pas de regroupement par plage).
- [ ] Créer un entrepôt `Camion` pour les opérations sur site → **décision actée** (entrepôt Odoo distinct), reste à définir son usage précis (quels mouvements y transitent).
- [ ] Définir le processus de réapprovisionnement des entrepôts principaux (`Galleria`, `Genipa`) depuis les dépôts déportés (`Dépôt 1` / `Dépôt 2`) lors d'une vente : puisque ce sont maintenant des entrepôts distincts, il faudra des **routes de transfert inter-entrepôts** Odoo (règle de réapprovisionnement automatique vs transfert manuel). Détail des mécanismes Odoo disponibles et questions précises dans `routes_transferts_entrepots.md` :
  - [ ] Quel dépôt (`Dépôt 1` ou `Dépôt 2`) réapprovisionne quel entrepôt principal (`Galleria` ou `Genipa`) ?
  - [ ] Règles de stock min/max vs route MTO (« à la commande ») : quelle logique par catégorie de produit ?
  - [x] Pour le camion (opérations de pose sur site) : RPBM ne souhaite pas adopter l'application Field Service, et fonctionne par le circuit de vente classique (devis → commande). Proposition révisée : ligne de service « Pose sur site » avec suivi de tâche via Project (sans Field Service) + lignes stockables routées vers `Camion` via une route spécifique de ligne de commande (voir `routes_transferts_entrepots.md` §4).
  - [ ] Valider ce principe révisé (commande = ligne de service/tâche + lignes d'articles routées via `Camion`) et confirmer si un projet/suivi des interventions existe déjà à RPBM.
  - [ ] Règle de priorité quand un article est disponible dans plusieurs entrepôts sources (le plus proche ? choix manuel ?).
  - [ ] Qui prépare le chargement du camion et à quelle fréquence (manuel chaque matin vs règle automatique) ?
  - [ ] Que faire d'un article chargé mais finalement non posé chez le client (retour vers quel entrepôt) ?
- [ ] Quel traitement appliquer aux valeurs encore ambiguës `CASSE`, `Tringle`, `Centre` de la colonne `PLACE` ? *(toujours ouvert)*

## 4. Stock initial et inventaire

- [ ] Quelle source fait foi pour le stock initial : inventaire réel du 30/06/2026, stock théorique corrigé, ou CSV V4 corrigé ?
- [ ] Comment arbitrer l'écart d'inventaire de 6 448,18 € (stock théorique 106 745,23 € vs stock réel 100 297,05 €) ?
- [ ] Fournir le fichier corrigé de l'inventaire réel du 30/06/2026 (nécessaire pour remplir `stock_initial_to_import.csv`, actuellement vide).
- [ ] Traitement des lignes marquées `Pas là`, `ERREUR`, vendu, réservé ou cassé : exclusion pure ou investigation au cas par cas avant import ?

## 5. Prix et valorisation comptable

- [x] Source du coût unitaire Odoo → **`PRIX RV`** (décision client ; remplace l'hypothèse provisoire précédente basée sur `PRIX ACHAT`). La signification exacte de `PRIX RV` (revient/revente) n'a plus besoin d'être tranchée : il est retenu comme coût quel que soit son nom.
- [ ] Prix de vente (`list_price`) : **vérifier les formules/règles de tarification déjà utilisées dans Odoo** avant de définir la règle d'import (le client renvoie sur l'existant Odoo plutôt que sur une colonne du fichier source).
- [ ] Si le fret doit entrer dans le coût : quelle règle d'allocation par article ? *(à reconfirmer, la question se posait surtout dans l'hypothèse `PRIX ACHAT` ; à revoir maintenant que le coût retenu est `PRIX RV`)*
- [ ] Méthode de coût de stock : FIFO ou AVCO ?
- [ ] Valorisation manuelle ou automatisée ? (une valorisation automatique génère une écriture comptable à chaque mouvement de stock)
- [ ] Comptes comptables à créer ou confirmer : compte de valorisation, compte d'entrée stock, compte de sortie stock.
- [x] Faut-il créer un prix fournisseur pour les fournisseurs non-VSF (`MPB`, `BLUE AUTO`, `A+ Glass`, etc.) ? → **décision du 2026-07-29** : oui, au même titre que VSF — créer le `product.supplierinfo` (prix = `PRIX ACHAT`) et le `res.partner` Odoo correspondant s'il n'existe pas déjà. *Réserve du 2026-07-30 : cette règle de création de partenaire ne doit pas s'appliquer à `VSF Centre`/`VSF Ouest` — le partenaire `VSF - VITRO SERVICE FRANCE` (id `5708`) existe déjà en préprod et le module `rpbm_agent` s'y réfère par son id (voir question bloquante ci-dessous).*
- [ ] Fournisseur Odoo correspondant à chaque valeur `FRS` du fichier source (55 valeurs distinctes, voir `suppliers_mapping.csv` généré le 2026-07-29) — rapprochement effectif encore à faire.
- [ ] 🚧 **Bloquant** — `VSF Centre` et `VSF Ouest` désignent-ils le même partenaire Odoo que `rpbm_agent.vsf_partner_id` (id `5708`), ou des comptes distincts ? *Requalifié en bloquant le 2026-07-30 : depuis la synchronisation VSF du module (`sync_vsf_information()`), un `res.partner` « VSF Centre » distinct de `5708` produirait deux prix fournisseur VSF concurrents que le mécanisme d'historisation ne réconcilie jamais. Concerne 8 943 lignes source (89 %) et 2 893 eurocodes.*

## 5 bis. Synchronisation VSF du module `rpbm_agent`

*Section ouverte le 2026-07-30 suite aux commits `0d24ff3` et `7e053a4` (re-synchronisation des produits depuis VSF). Analyse détaillée : [`reconciliation-stock-rpbm-agent.md`](../../docs/cartographie/reconciliation-stock-rpbm-agent.md).*

- [ ] Les **43 références sur 3 289** (1,3 %) dont l'`EUROCODE` ne respecte pas le format attendu (annotations entre parenthèses, suffixes `-PERDU`, texte libre comme `17/03 : COTTET Eric`) ne recevront pas de `x_studio_eurocode` à l'import, et seront donc **définitivement hors synchronisation VSF** (la synchro lève une erreur sans ce champ). Faut-il les reprendre manuellement avant l'import, ou accepter cette limite ? *La liste est extractible de `products_to_import.csv` via la colonne `eurocode_format_valide`.*

## 6. Statuts opérationnels (réservé / cassé / vendu)

- [ ] Statut `Réservé` : réservation de stock via commande client, emplacement interne dédié, statut custom, ou processus standard devis → commande → livraison ?
- [ ] Statut `Cassé` : sortie via rebut, emplacement `Casse` dédié, ou conservation en stock non disponible ? Valorisé ou dévalorisé comptablement ?

## 7. Droits et processus cible

- [ ] Droits utilisateurs sur les mouvements de stock : qui peut ajuster un stock, valider un inventaire ?
- [ ] Règle pour rendre l'étape livraison obligatoire sur les articles stockables, sans bloquer les factures composées uniquement de main-d'œuvre.

## 8. Hors périmètre (mentionné par le client, non traité dans ce projet)

- Conditions de paiement client : les clients hors assurance versent un acompte de 40 % du prix de vente, solde à l'installation ; les clients assurance paient intégralement après l'installation, sans acompte. **Explicitement signalé par le client comme hors du cadre du projet stock actuel** — noté ici pour mémoire, à ne pas traiter dans cette migration.
