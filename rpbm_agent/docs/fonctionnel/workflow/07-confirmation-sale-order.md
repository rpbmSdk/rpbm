# 7 — Confirmation sur Ordre de Vente (`sale.order`)

Le notebook « Véhicule (X'Glass) » est masqué si le devis ne possède pas d'opportunité liée.
Le widget n'est donc jamais ouvert dans un contexte où ses champs `related` seraient perdus.

Le lieu logistique ne se saisit pas dans la dialog véhicule : il est porté par le
champ natif `carrier_id`, visible sous le client dans le formulaire du devis.
Sur un nouveau devis lié à une opportunité, le module propose automatiquement
Galleria, Genipa ou Camion lorsque le champ CRM historique
`x_studio_lieu_intervention` permet une correspondance déterministe. Les valeurs
LAVAGE et les correspondances absentes restent manuelles. Le choix explicite de
l'utilisateur est prioritaire.

- **Déclencheur** : clic sur « Confirmer » (ou « Confirmer et enregistrer ») dans la fenêtre du widget, ouverte depuis une fiche `sale.order` (loupe) ou automatiquement après « Créer un devis » (voir [plus bas](#ouverture-automatique-du-dialog-après-création-du-devis)).
- **Code** : même `confirmRecord()` → `writeRecord()` → `getRecordData()` que pour `crm.lead` ; les champs `rpbm_*` portent les mêmes noms sur les deux modèles. La classe `AgentWidgetDialogSaleOrder` (`agent_widget_dialog_sale_order.js`) ajoute la recherche VSF, les lignes d'article et la main-d'œuvre. Depuis le lot E2, elle s'ouvre **sans authentification X'Glass** : voir [Devis sans X'Glass](#devis-sans-xglass-lot-e2).

| Champ écrit | Valeur source | Condition |
|---|---|---|
| mêmes champs natifs `rpbm_*` que sur l'opportunité ([6](06-confirmation-crm-lead.md)), `rpbm_xglass_vehicle_id` compris | mêmes sources | miroirs `related` écrivables : la valeur est portée par l'opportunité liée |
| `rpbm_eurocode`, `rpbm_vsf_designation`, `rpbm_vsf_stock`, `rpbm_constructor_reference` | article VSF désigné **principal** (« Définir comme article principal ») | si un article principal est désigné ; depuis le lot E1, seul le dialog du devis les écrit |
| `rpbm_eurocode_base` | `state.baseEurocode` | toujours (vide efface), avec ou sans X'Glass |
| `rpbm_xglass_piece_label` | libellé de la pièce choisie ([6](06-confirmation-crm-lead.md)) | seulement quand X'Glass est chargé, avec véhicule et catégorie choisis, sous la condition des identifiants de pièce |
| `rpbm_xglass_labor_operations` | main-d'œuvre de la pièce choisie ([6](06-confirmation-crm-lead.md#main-dœuvre-enregistrée-correctif-du-2026-10-07)) | seulement quand X'Glass est chargé, avec véhicule et catégorie choisis, sous la condition des identifiants de pièce ; **jamais** par un « Confirmer » sans X'Glass |

- **Persistance** : identique à `crm.lead` — mise à jour en mémoire, écriture effective au clic sur « Enregistrer » (bouton « Confirmer ») ou immédiate via `record.save()` (bouton « Confirmer et enregistrer »).
- L'ajout ou le retrait d'un article principal ou suggéré au devis (`addArticleToSaleOrder()` / `removeArticleFromSaleOrder()`) est indépendant de cette étape ; seule une ligne créée par le widget dans la dialog courante peut être retirée, par « Retirer du devis », qui remplace « Ajouter au devis » une fois la ligne ajoutée (un produit déjà présent à l'ouverture affiche « Article déjà présent dans le devis. », sans retrait) — voir [9 — Création du produit](09-creation-produit.md#retirer-du-devis-r28).

Les opérations de main-d'œuvre X'Glass cochées sont ajoutées indépendamment de
la confirmation. Chaque opération reconnue (T1, T2 ou T3) crée une ligne de
service dont la quantité vaut sa durée X'Glass. La clé
`rpbm_labor_operation_key` garde la provenance de la ligne, ce qui interdit
les doublons après réouverture et limite le retrait à la ligne du widget.

La confirmation standard de la vente est une étape distincte de la confirmation
de la dialog. Elle exige un `carrier_id` pour toute vente à l'état brouillon ou
envoyée, mais ne crée pas de transporteur et ne modifie pas les lignes de vente.

Pour un véhicule existant, `/enrichVehicule` complète les champs Fleet VIN/date MEC manquants ;
les champs dérivés du véhicule et les champs Studio historiques sont alimentés côté serveur à
l'enregistrement, comme sur l'opportunité. Le kilométrage n'est jamais modifié. Sans opportunité
liée, le widget est masqué.

## Devis sans X'Glass (lot E2)

Lot E2 « VSF d'abord, X'Glass à la demande » (`17.0.261006.2`, commits `afa51df` code et `a562fa7` docs, recette live réussie le 2026-10-06, [SO-10](../../jeu-de-test.md#so-10--vsf-dabord-xglass-à-la-demande-lot-e2)). Le véhicule et la pièce se choisissent déjà sur l'opportunité (lot E1) ; sur le devis, il reste surtout à choisir les articles VSF. La fenêtre du devis s'affiche donc tout de suite, **sans connexion à X'Glass** (l'ancien chemin demandait 15 à 22 s avant le tableau) :

- un encart **« Dossier »**, en lecture seule, reprend les champs de l'opportunité : véhicule, catégorie, pièce concernée, pièce X'Glass (libellé mémorisé, « — » pour un dossier confirmé avant le lot) et article principal ;
- depuis le correctif du 2026-10-07, la section **« 4. Main d'œuvre X'Glass »** s'affiche dès l'ouverture, entre « Dossier » et « 5. Article VSF », quand l'opportunité a une main-d'œuvre enregistrée ([ci-dessous](#main-dœuvre-enregistrée-correctif-du-2026-10-07)) ;
- la recherche VSF part aussitôt sur la base enregistrée, même s'il n'y a qu'une base ou une ligne « Autres marques AM » ;
- **« Confirmer »** est actif dès l'ouverture. Sans X'Glass, il n'écrit que la base Eurocode et l'article principal : le véhicule, la catégorie et les identifiants de pièce mémorisés ne sont jamais effacés, et aucun véhicule n'est créé ni enrichi ;
- **« Charger X'Glass »** lance la chaîne X'Glass actuelle : authentification (avec le verrou), restauration du véhicule mémorisé, de la catégorie, de la pièce et de la pièce après-marché, puis main-d'œuvre (« 4. Main d'œuvre X'Glass », qui passe alors à la liste fraîche de X'Glass) et changement de pièce. L'encart disparaît, la section « 1. Véhicule » apparaît ; **le tableau VSF, la sélection et l'article principal sont conservés**, sans nouvelle recherche tant que la base ne change pas. Un seul chargement à la fois : le bouton est désactivé pendant le chargement. Il sert aussi à réessayer après un échec, dont le message s'affiche dans l'encart. La pièce concernée enregistrée n'est pas écrasée par la suggestion du calque, et la base, le tableau, la sélection et l'article principal survivent même si le dossier n'avait ni base ni pièce enregistrées ; seul un choix explicite d'une autre catégorie les vide, comme avant ;
- une fois X'Glass chargé avec véhicule et catégorie choisis, « Confirmer » écrit comme avant tout le dossier, libellé de la pièce compris ;
- « Annuler » sans « Charger X'Glass » ne ferme aucune session X'Glass (il n'y en a pas) : aucun appel `/rpbm_agent_close`.

**Verrou.** Il ne protège plus que X'Glass (« Annuler » ne déconnecte d'ailleurs pas la session X'Glass d'un autre vendeur qui aurait repris un verrou expiré) : plusieurs vendeurs peuvent chercher sur VSF en même temps, et l'ouverture d'un devis ne prend pas le verrou ([VD-05](../../validations-metier.md#historique-des-décisions)). Un vendeur qui clique sur « Charger X'Glass » pendant qu'un autre utilise X'Glass reçoit le message « actuellement utilisé par … ». Si l'on ferme la fenêtre pendant « Charger X'Glass », la fenêtre détruite libère elle-même le verrou et ferme la session X'Glass dès que l'authentification répond : le verrou ne reste pas pris.

Détail technique : [frontend](../../technique/frontend.md#vsf-dabord-xglass-à-la-demande-lot-e2) et [backend](../../technique/backend.md#vsf-session-à-la-demande-lot-e2).

## Main-d'œuvre enregistrée (correctif du 2026-10-07)

Correctif `17.0.261007.1` (codé le 2026-10-07, à livrer et recetter ; [SO-11](../../jeu-de-test.md#so-11--main-dœuvre-enregistrée-proposée-sans-xglass-correctif-du-2026-10-07-r30)). Depuis le lot E2, la main-d'œuvre n'était proposée qu'après « Charger X'Glass » : un vendeur qui voulait seulement ajouter ou retirer un article de temps devait charger X'Glass (connexion, verrou). La main-d'œuvre est maintenant **enregistrée à l'étape opportunité** et reprise sur le devis (décision du 2026-10-07, [VD-06](../../validations-metier.md#historique-des-décisions)).

Ce que voit le vendeur sur un devis dont l'opportunité a une main-d'œuvre enregistrée :

- à l'ouverture, **sans authentification X'Glass**, la section « 4. Main d'œuvre X'Glass » apparaît entre « Dossier » et « 5. Article VSF ». Chaque opération montre son libellé, sa durée en heures et son taux (T1, T2 ou T3) ; une opération sans durée positive, sans identifiant ou sans taux reconnu reste non cochable, avec son motif ;
- il coche des opérations, puis « Ajouter les opérations sélectionnées » : une ligne de service par opération, quantité égale à la durée, prix et taxes du produit Odoo ; « Retirer » remplace la case d'une opération déjà ajoutée et supprime sa ligne (reconnue par sa clé de provenance, y compris d'une session précédente) ;
- « Confirmer » sans X'Glass n'écrit toujours que la base et l'article principal : la main-d'œuvre enregistrée n'est pas touchée ;
- après « Charger X'Glass », la pièce restaurée fournit sa main-d'œuvre fraîche ; le « Confirmer » qui suit (véhicule et catégorie choisis) la réécrit, et elle remonte à l'opportunité.

**Dossier existant sans main-d'œuvre enregistrée** (confirmé avant `17.0.261007.1`, ou pièce sans opération) : la section n'apparaît pas à l'ouverture. Secours, comme avant : « Charger X'Glass » ; la section apparaît avec la liste de X'Glass ; le « Confirmer » qui suit enregistre la main-d'œuvre, et le devis la propose ensuite sans X'Glass. Un rechargement automatique depuis X'Glass à l'ouverture a été écarté : il exigerait la connexion et le verrou que le lot E2 évite.

**Limites.** Les durées, taux et produits de service sont ceux du dernier enregistrement fait avec X'Glass (instantané). Sur un devis sans opportunité liée, rien ne s'enregistre : « Charger X'Glass » reste nécessaire. Une pièce sans opération n'affiche pas la section sans X'Glass. Détail technique : [frontend](../../technique/frontend.md#main-dœuvre-enregistrée-correctif-du-2026-10-07) ; champ : [crm-lead](../../technique/champs/crm-lead.md).

## Ouverture automatique du dialog après création du devis

Un devis créé par « Créer un devis » depuis l'opportunité ([6](06-confirmation-crm-lead.md#créer-un-devis-lot-e1)) ouvre seul la fenêtre du widget : il n'y a pas de clic sur la loupe. Au lot E1, elle restaurait aussitôt le contexte de l'opportunité. Depuis le lot E2, elle s'ouvre en mode VSF seul (voir [ci-dessus](#devis-sans-xglass-lot-e2)) : encart « Dossier » et recherche VSF immédiate sur la base enregistrée. Le véhicule X'Glass mémorisé (`rpbm_xglass_vehicle_id`) s'il figure dans les résultats de l'immatriculation, sinon le premier, puis la catégorie, la pièce et la pièce après-marché (sections 1 à 3) reviennent par « Charger X'Glass ». « 4. Main d'œuvre » est proposée dès l'ouverture quand l'opportunité a une main-d'œuvre enregistrée ; « 5. Article VSF » est là aussi dès l'ouverture. L'opportunité ayant fermé ses portails et libéré le verrou, la chaîne ne rencontre pas d'obstacle.

L'ouverture n'a lieu qu'une fois, pour ce devis nouveau. Elle n'a pas lieu avec « Nouveau devis » natif, Ventes › Devis › Nouveau, le retour par le fil d'Ariane ou le rechargement de la page ; la loupe reste le moyen d'ouvrir la fenêtre dans ces cas. Le cas limite du lot E1, une opportunité sans pièce OE avec seulement une ligne « Autres marques AM » et une base, qui ouvrait le devis sans recherche VSF automatique, est levé : la recherche part dès qu'il y a une base ([4](04-piece-piece-am.md)).

Détail de chaque champ : [technique/champs/sale-order.md](../../technique/champs/sale-order.md).
