# AG-01 — Audit des champs utiles et de la compatibilité historique

## Statut

**Audit préparé le 14 septembre 2026.** Acquisition Odoo terminée en lecture
seule sur le profil explicite rpbm-preprod. Aucune donnée métier n'a été
exportée, aucune vue, automatisation ou règle Odoo n'a été modifiée, et aucune
implémentation fonctionnelle n'est incluse dans ce document.

Le [manifest AG-01](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/manifest.json)
décrit le snapshot reproductible. Le script d'acquisition est
[prepare_ag01_audit.py](../../../tools/prepare_ag01_audit.py).

## Clarification de périmètre

La planification retire uniquement la création future des doublons Fleet
`x_rpbm_vehicle_brand_id`, `x_rpbm_vehicle_model_id`,
`x_rpbm_vehicle_brand_name`, `x_rpbm_vehicle_model_name`,
`x_rpbm_vehicle_vin`, `x_rpbm_vehicle_detail_model`,
`x_rpbm_vehicle_fuel_type` et `x_rpbm_vehicle_date_mec`.
`x_studio_vehicle_id` est explicitement conservé : il reste le lien vers
`fleet.vehicle` et doit rester couvert par la conception et la recette.
Le champ `x_rpbm_vsf_constructor_reference` n'est pas concerné par cette
clarification et reste à traiter séparément.

Aucun champ existant ne doit être supprimé dans AG-01 : ni les champs
historiques, ni les champs portant un libellé obsolète, ni les alias déjà
déployés sur l'instance. Cette planification traite uniquement les futures
créations et l'alignement des lectures/écritures du module.

## Objectif et méthode

L'objectif est de déterminer, pour chaque information du parcours de la fenêtre
de dialogue, quel champ doit rester alimenté pour préserver les habitudes des
utilisateurs, quel champ est un miroir, et quel champ est réellement obsolète
après vérification de ses usages résiduels.

L'acquisition a couvert crm.lead, sale.order, sale.order.line, fleet.vehicle,
delivery.carrier et les objets stock nécessaires au routage, ainsi que les
champs, vues, vues QWeb, rapports, actions, menus, automatisations, actions
serveur, droits et origines studio_customization. Chaque famille a d'abord fait
l'objet d'un get_model_fields, puis d'une lecture MCP paginée.

| Famille | Observé dans le snapshot AG-01 |
|---|---:|
| Définitions de champs sur les modèles ciblés | 2 076 |
| Vues, dont les QWeb | 2 255 |
| Rapports ciblés | 10 |
| Automatisations | 11 |
| Actions serveur | 252 |
| Origines Studio ciblées | 866 |
| Valeurs de sélection | 537 |

Le dossier data/current/ de l'audit Studio général reste le snapshot complet du
25 juillet. AG-01 utilise volontairement data/ag01-2026-09-14/ pour ne pas
mélanger deux états de l'instance.

Sources locales détaillées : [champs](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/fields/ir.model.fields.json),
[vues et QWeb](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/views/ir.ui.view.json),
[rapports](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/navigation/ir.actions.report.json),
[automatisations](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/automations/base.automation.json),
[actions serveur](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/automations/ir.actions.server.json)
et [sélections](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/fields/ir.model.fields.selection.json).

## Règle de qualification

| Statut | Critère appliqué |
|---|---|
| **Utile — conserver et alimenter** | Le champ intervient dans le dialogue, une automatisation, une vue ou un rapport actif ; sa source et sa sémantique sont identifiables. |
| **Canonique** | Le champ est la source de vérité retenue pour les nouveaux dossiers : Fleet pour l'identité du véhicule, carrier_id pour le transport/logistique, ou le champ historique métier lorsqu'il faut préserver les usages. |
| **Redondant — déprécier** | La même information existe plusieurs fois, souvent en related, mais des références résiduelles imposent une phase de compatibilité. |
| **Obsolète selon l'étiquette — hors périmètre** | Le champ est explicitement marqué obsolète/supprimé ; AG-01 ne planifie ni sa suppression ni sa migration. Le libellé seul ne suffit pas à modifier son usage. |
| **À confirmer** | La valeur métier, le mapping entre référentiels, l'usage réel des données ou le rapport effectivement utilisé ne peut pas être prouvé par des métadonnées seules. |

## Matrice de qualification

Les liens vers les JSON pointent vers les éléments du snapshot local. La
présence dans une vue héritée est une preuve de référence XML ; elle ne prouve
pas à elle seule que le champ est visible dans le rendu final pour tous les
utilisateurs. Les conditions invisible, readonly et les effets de priorité
doivent être rejoués en UI.

| Information | CRM / champ source | Devis / miroir | Présence dans vues et rapports | Qualification AG-01 |
|---|---|---|---|---|
| Lien avec le véhicule | crm.lead.x_studio_vehicle_id — m2o fleet.vehicle | sale.order.x_studio_vehicle_id — related vers l'opportunité | Visible dans les vues module 7900/7901 ; page devis conditionnée par opportunity_id | **Canonique et utile** |
| Immatriculation | x_studio_field_NVioD | x_studio_immatriculation_ — related vers le CRM | CRM : 397, 417, 418, 426 et QWeb 4861 ; devis : 4858 et plusieurs QWeb | **Utile historique** ; alimenter depuis Fleet |
| Marque | x_studio_field_KyCjB — m2o x_rpbm_marques_voitures | x_studio_many2one_field_rP62C et affichages texte | CRM : 397/426 et QWeb 4861/5325 ; devis : 4858 et variantes QWeb | **Redondant, usage résiduel prouvé** |
| Modèle | x_studio_field_ZhaeY — m2o x_rpbm_modeles_voitures | x_studio_many2one_field_DkgHx, x_studio_modle, x_studio_modle_ | CRM : 397 et QWeb 4861/5325 ; devis : 4858 et variantes QWeb | **Redondant, usage résiduel prouvé** |
| VIN | x_studio_field_PfJlB | x_studio_vin_ — related | CRM : 397 et QWeb 4861 ; devis : 4858 et variantes QWeb ; Fleet vin_sn dans 2319/2320 | **Utile historique**, Fleet vin_sn canonique |
| Énergie | x_studio_field_TAhpP — sélection | x_studio_nergie_moteur — related | CRM/devis 397/4858 ; Fleet fuel_type 2319/2321 ; miroir x_rpbm_vehicle_fuel_type 7900/7901 | **Historique à compatibiliser**, Fleet canonique |
| Détail modèle et date MEC | x_studio_field_i8fWl, x_studio_field_Eh6Wd | x_studio_dtails_modle, x_studio_date_1re_mec | Historiques dans les vues Studio ; champs Fleet x_studio_detail_model/date_mec et miroirs visibles dans 7900/7901/7902 | **Fleet canonique**, historiques à alimenter |
| Catégorie X'Glass | x_studio_categorie_xglass — libellé portail | champ related sur le devis | Visible dans 7900/7901 ; distincte de la pièce métier | **Utile** |
| Pièce concernée | x_studio_field_eENQz — sélection à 4 valeurs | x_studio_pice_concerne — related | CRM/devis 397/4820/4858 ; nombreuses variantes QWeb utilisent le champ CRM | **Utile et structurante** |
| Base Eurocode | x_studio_field_ORIyy | x_studio_base_eurocode — related | CRM 397 ; devis 4858 ; pas de QWeb ciblé identifié | **Utile**, cible d'écriture à conserver |
| Eurocode complet | x_studio_field_NwRik | x_studio_eurocode_complet — related | CRM 397/417/426/7900 ; devis 7901 le cache dans le groupe article | **Utile sous condition**, article VSF principal |
| Eurocode joint | x_studio_eurocode_joint | related sur le devis | Présent dans 4820/4858 ; saisie manuelle | **Utile manuel** |
| Article VSF principal | x_studio_field_j8eh3, x_studio_field_BKtpw, x_studio_field_MNzfJ | related et x_rpbm_vsf_constructor_reference | Caché dans 7900/7901 ; historiques visibles dans 397/4858 et réutilisés par les documents | **Utile pour compatibilité**, écrire les historiques |
| Kilométrage | x_studio_field_aIM13 et x_studio_kilomtrage | x_studio_kilomtrage, x_studio_kilomtrage_1, x_studio_kilomtrage__1 | CRM 397/4820 ; devis 4858 ; les variantes apparaissent dans des rapports | **Redondance à confirmer** ; aucune écriture automatique |
| Lieu d'intervention historique | x_studio_lieu_intervention — sélection | aucun champ homonyme sur sale.order | Visible dans CRM Studio 4820 ; valeurs : GALLERIA, GENIPA, LAVAGE PLACE D'ARMES, DOMICILE, LAVAGE MARIN | **Historique à conserver**, mapping à confirmer |
| Méthode logistique | sale.order.carrier_id — m2o delivery.carrier | champ natif du devis | Présent dans le modèle ; désormais fourni par la vue versionnée AG01-03 ; consommé par la livraison et les routes stock | **Canonique logistique**, préremplissage CRM déterministe ; architecture stock AG-02 requise pour le routage |

## Vérification des vues

- La vue CRM 7900 expose le widget, le véhicule Fleet, la catégorie X'Glass et
  les six champs d'identité Fleet x_rpbm_*. Les champs Eurocode complet,
  désignation, stock et référence constructeur sont dans un groupe invisible=1.
- La vue devis 7901 expose les mêmes éléments, mais la page entière porte
  invisible=not opportunity_id. Un devis sans opportunité est donc un état prévu
  de l'interface ; les champs related ne sont pas une seconde saisie.
- La vue Fleet 7902 affiche les deux champs Studio additionnels de détail modèle
  et de date MEC.
- Les vues Studio historiques 397, 4820 et 4858 contiennent encore les champs
  historiques. Leur présence explique pourquoi leur suppression serait
  régressive pour les utilisateurs et les documents.

Le détail des architectures est conservé dans
[ir.ui.view.json](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/views/ir.ui.view.json).

## Vérification des rapports

Le snapshot contient 10 actions de rapport sur sale.order. Les chaînes QWeb
actives montrent plusieurs familles qui ne partagent pas encore une cible
canonique :

| Action rapport | Chaîne QWeb observée | Références historiques observées |
|---|---|---|
| 1499 — RPBM Devis / Commande | racine 4859, document 4860, personnalisation 4861 | immatriculation, marque, modèle, VIN, kilométrage, pièce concernée |
| 1505 — RPBM - Ordre de Réparation | racine 4886/4887, personnalisation 4888 | miroirs historiques du devis, marque/modèle et kilométrage |
| 1513 — RPBM OR | racine 4908/4909, personnalisation 4910 | miroirs historiques du devis et kilométrage |
| 1519 — RPBM Devis / Commande brouillon | racine 4920/4921 | immatriculation, VIN, modèle, kilométrage, pièce concernée |
| 1591 — DBDG RPBM | racine 5324/5323, personnalisation 5325 | anciens champs marque, modèle, immatriculation et modèle devis |
| delivery — document de livraison | vue 6519 | carrier_id |

Les autres rapports de vente et de facture comportent également des copies QWeb
qui réutilisent des champs historiques du devis. La liste complète est dans
[ir.actions.report.json](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/navigation/ir.actions.report.json).

## Constats prioritaires

### AG01-F01 — P0 — Le module crée des alias Fleet au lieu de modifier les champs historiques

**Fait observé.** Le code local déclare les huit champs x_rpbm_vehicle_* de
doublon Fleet ainsi que x_rpbm_vsf_constructor_reference dans FIELDS_TO_ENSURE,
puis les crée dans pre_init_hook avec with_context(studio=True). Le snapshot
live confirme ces champs sur crm.lead et sale.order, avec une origine Odoo
présentée comme studio_customization. Ils sont des related stockés vers Fleet
ou vers les champs historiques.

**Impact.** Une seconde famille porte la même information que les anciens
champs. Les rapports et les utilisateurs peuvent donc lire des sources
différentes. Le remplacement des références de vue dans le hook risque de
masquer les usages historiques au lieu de les maintenir.

**Décision proposée.** Faire de cette correction la première tâche
d'implémentation : ne plus créer les huit doublons Fleet listés dans la
clarification de périmètre ; conserver explicitement x_studio_vehicle_id et
alimenter les champs historiques existants, après validation du mapping
marque/modèle. Le cas x_rpbm_vsf_constructor_reference reste hors de cette
modification ciblée. Les champs déjà déployés, y compris les alias et les
champs historiques, restent en place.

Références : [hooks.py](../../hooks.py), [vue CRM](../../views/crm_lead_views.xml),
[vue devis](../../views/sale_order_views.xml),
[champs live](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/fields/ir.model.fields.json),
[origines live](../../../.paradigme/audits/rpbm-preprod/data/ag01-2026-09-14/models/ir.model.data.json).

### AG01-F02 — P1 — Les champs historiques ont encore des usages résiduels

**Fait observé.** Le snapshot live compte 273 champs personnalisés sur crm.lead,
dont 54 libellés contenant « obsolète », « obsolete » ou « supprimer ». Les
champs marque/modèle historiques sont explicitement traités comme obsolètes dans
la documentation du module, mais restent référencés par les vues 397/426 et les
QWeb 4861/5325.

**Impact.** Le libellé et l'usage technique ne concordent pas. Un retrait ou un
renommage immédiat pourrait casser une vue, une impression ou une automatisation.

**Décision proposée.** Ne pas planifier de suppression ni de migration de ces
champs dans AG-01. Documenter seulement leurs références et leurs contraintes
de compatibilité afin de ne pas perturber les utilisateurs.

### AG01-F03 — P1 — Les rapports de vente n'ont pas de source véhicule unique

**Fait observé.** Plusieurs variantes QWeb actives lisent encore directement les
champs historiques CRM/devis marque, modèle, VIN, kilométrage et pièce.
Certaines affichent aussi des miroirs de devis qui ne sont pas alimentés de la
même façon.

**Impact.** Une correction du dialogue vers Fleet seule ne garantit pas que les
documents existants changeront ; remplacer les QWeb sans alimenter les
historiques rendrait les dossiers anciens incomplets.

**Décision proposée.** Migrer les rapports par famille, avec un choix explicite
entre Fleet et les champs historiques de compatibilité. Recetter un dossier avec
opportunité et un devis sans opportunité.

### AG01-F04 — P1 — carrier_id est présent mais absent de l'UI active du devis

**Fait observé.** sale.order.carrier_id est un champ natif many2one vers
delivery.carrier, mais aucune vue formulaire active de sale.order du snapshot
AG-01 ne contient carrier_id. Le champ est toutefois consommé par les vues de
livraison/QWeb.

**Impact.** Les utilisateurs ne peuvent pas sélectionner le lieu/mode logistique
au même endroit que le devis, tandis que l'ancien champ CRM reste visible.

**Décision proposée.** Créer une vue Odoo versionnée pour réintroduire le champ sur
sale.order, puis traiter séparément le pré-remplissage depuis
crm.lead.x_studio_lieu_intervention. Le mapping des cinq valeurs historiques
vers les transporteurs doit être validé avant tout automatisme.

### AG01-F05 — P2 — Le kilométrage reste ambigu

**Fait observé.** Le CRM porte au moins x_studio_field_aIM13 et
x_studio_kilomtrage. Le devis porte x_studio_kilomtrage,
x_studio_kilomtrage_1 et x_studio_kilomtrage__1, dont les sources diffèrent.
Les trois familles apparaissent dans des rapports.

**Décision proposée.** Mesurer les remplissages sur un échantillon métier autorisé,
choisir une cible, puis conserver les anciennes valeurs sans migration de masse
implicite. Le parcours X'Glass ne fournit pas ce champ.

## Backlog d'implémentation issu de l'audit

### AG01-01 — Corriger la stratégie de champs du module — priorité critique

1. Établir la table définitive information → champ historique cible pour
   crm.lead, avec les exceptions de type et de relation.
2. Retirer de la conception cible uniquement les créations des huit doublons
   Fleet `x_rpbm_vehicle_*` listés ci-dessus. Conserver explicitement
   `x_studio_vehicle_id` ; le cas `x_rpbm_vsf_constructor_reference` reste
   séparé. Pour les huit doublons, le hook doit signaler proprement un champ
   historique manquant au lieu d'inventer un champ de remplacement.
3. Adapter la préparation des données de la dialog pour écrire les champs
   historiques utiles : immatriculation, VIN, énergie, détail modèle, date MEC,
   pièce, Base Eurocode et informations de l'article principal.
4. Décider et implémenter le mapping Fleet vers les référentiels historiques
   x_rpbm_marques_voitures et x_rpbm_modeles_voitures, avec comportement explicite
   si aucune correspondance fiable n'existe.
5. Ne pas fabriquer de kilométrage : préserver la valeur historique si aucune
   source de confiance n'est fournie.
6. Maintenir les champs sale.order related existants qui servent de compatibilité ;
   ne pas créer une copie indépendante pour contourner un mauvais chemin related.
7. Adapter les vues/rapports du module pour qu'ils ne dépendent pas de la
   création de ces huit doublons Fleet. Ne supprimer aucun champ existant,
   historique, obsolète ou alias déjà déployé.

### AG01-02 — Aligner le workflow de confirmation de la dialog

1. Vérifier le payload exact de getRecordData() pour CRM et devis.
2. Vérifier que « Confirmer » et « Confirmer et enregistrer » écrivent les mêmes
   champs historiques, avec seulement une différence de persistance.
3. Tester un véhicule existant, la création d'un véhicule et un véhicule sans
   certaines métadonnées.
4. Vérifier que l'article VSF principal écrit seulement NwRik, j8eh3, BKtpw et
   MNzfJ, sans modifier les prix ou marges calculés.
5. Rejouer le cas devis avec opportunité et le cas devis sans opportunité.

### AG01-03 — Assainir les vues sans perturber les utilisateurs

1. Conserver temporairement les champs historiques utiles tant que les rapports
   ne sont pas migrés.
2. Modifier les nouvelles vues du module pour afficher la source canonique
   retenue, sans réintroduire de champs d'affichage redondants.
3. Vérifier invisible, readonly, required, la priorité des héritages et la
   présence du champ dans le rendu final, pas seulement dans arch_db.
4. Ajouter `carrier_id` dans une vue sale.order versionnée et fiabiliser son
   préremplissage depuis le lieu historique CRM ; l'architecture stock AG-02
   reste responsable des transporteurs et des routes.

### AG01-04 — Migrer et recetter les rapports

1. Cartographier chaque action de rapport vers sa chaîne QWeb complète, incluant
   racine, document et personnalisations héritées.
2. Choisir la source pour chaque information : Fleet pour l'identité véhicule,
   historiques pour la compatibilité et carrier_id pour le lieu logistique.
3. Migrer les références marque/modèle/VIN/kilométrage/immatriculation sans
   supprimer aucun champ historique.
4. Vérifier les variantes RPBM, OR, DBDG, brouillon et delivery sur PDF.
5. Ajouter un contrôle de non-régression pour un dossier ancien et un dossier
   créé avec le nouveau dialogue.

### AG01-05 — Qualifier les doublons et champs obsolètes

1. Produire la liste complète des 54 champs CRM marqués obsolètes ou supprimables
   et rechercher chaque référence dans vues, QWeb, automatisations, actions
   serveur et code local.
2. Distinguer champ jamais utilisé, champ seulement historique et champ encore
   actif dans un rapport.
3. Pour les doublons de kilométrage, marque/modèle, modèle de devis et libellés
   génériques, choisir une cible par décision métier.
4. Documenter les doublons et leurs usages pour sécuriser l'interface et les
   rapports ; ne planifier la suppression d'aucun champ, même marqué obsolète.
5. Ne réaliser aucune migration de masse de valeurs sans mesurer le périmètre et
   obtenir la décision métier correspondante.

## Critères de recette AG-01

### Fenêtre CRM

- Le véhicule Fleet sélectionné est visible et reste lié au dossier.
- La confirmation renseigne les champs historiques ciblés, pas seulement des
  champs x_rpbm_*.
- L'immatriculation, le VIN, l'énergie et la date MEC sont cohérents avec le
  véhicule ; une donnée absente n'efface pas une donnée historique sans règle
  explicite.
- La pièce concernée et la Base Eurocode reprennent les champs historiques
  attendus, avec la sélection X'Glass distinguée de la pièce métier.
- Un article VSF principal renseigne les quatre champs historiques prévus ; les
  prix et marges calculés restent hors de cette confirmation.
- Les champs portant un libellé obsolète ne sont pas introduits dans le nouveau
  parcours, mais restent présents et les dossiers historiques restent lisibles.

### Fenêtre devis

- Le comportement avec et sans opportunity_id est explicite.
- Les champs related du devis reflètent l'opportunité sans devenir une seconde
  source de saisie.
- La confirmation véhicule ne crée pas de ligne produit et ne déclenche pas une
  écriture tarifaire inattendue.
- carrier_id est visible dans l'UI après AG01-03, prérempli seulement lorsqu'une
  correspondance CRM déterministe existe, et sa valeur est conservée après
  sauvegarde ; la confirmation standard est bloquée s'il est vide.

### Rapports

- Les rapports RPBM, OR, DBDG, brouillon et delivery affichent la source choisie
  pour l'immatriculation, marque, modèle, VIN, pièce et lieu.
- Un dossier ancien sans véhicule Fleet conserve un rendu lisible via les champs
  historiques.
- Un dossier nouveau avec véhicule Fleet reste lié par `x_studio_vehicle_id` et
  ne dépend pas de la création des huit doublons `x_rpbm_vehicle_*` ; aucun
  champ existant n'est supprimé.
- Les copies de rapports réellement inutilisées sont identifiées avant toute
  désactivation.

## Limites et décisions encore requises

- L'audit ne lit pas les enregistrements CRM/devis : il ne mesure donc pas le
  taux de remplissage ni les divergences de valeurs entre doublons.
- Il ne conclut pas quel rapport les équipes utilisent réellement lorsque
  plusieurs actions portent des noms proches.
- La présence d'un champ dans arch_db ne remplace pas une recette du rendu final
  avec les droits, priorités et conditions de vue effectifs.
- Le mapping des cinq valeurs du lieu historique vers delivery.carrier n'est pas
  déduit automatiquement.
- La relation entre les modèles Fleet et les anciens modèles Studio de marque et
  de modèle nécessite une décision technique et métier avant écriture.
