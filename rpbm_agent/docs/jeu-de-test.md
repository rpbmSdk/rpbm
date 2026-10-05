# Jeu de test — Assistant véhicule RPBM

Jeu de données destiné à rejouer les parcours du module `rpbm_agent` sur une
instance de test. Les valeurs marquées **observée** proviennent des scénarios
et fixtures déjà présents dans le dépôt. Les valeurs **synthétiques** ne
doivent être utilisées qu'avec un mock des portails ou avec des enregistrements
de test explicitement préparés.

## Données de référence

| Élément | Valeur | Statut | Usage |
|---|---|---|---|
| Plaque véhicule | `DS808DZ` | Observée | Recherche X'Glass nominale ; véhicule de test historique |
| Identifiant véhicule X'Glass | `397899` | Observée | Tests techniques de sélection véhicule |
| Base Eurocode | `6539R` | Observée | Recherche VSF nominale |
| Article VSF principal | `6539RGSH5RD` | Observée | Article avec stock et fiche détaillée |
| Article VSF principal alternatif | `6571AGRCHIMVZ` | Observée | Création/synchronisation produit |
| Suggestion VSF | `6571AGRCIMVZ` | Observée | Vérification des suggestions liées |
| Suggestion accessoire | `PP-COLLE310` | Observée | Article suggéré disponible ou indisponible |
| Plaque sans résultat | `ZZ-TEST-00` | Synthétique | Scénario de recherche vide ; nécessite un mock ou une donnée X'Glass dédiée |
| Base sans résultat | `ZZZZZ` | Synthétique | Scénario VSF vide ; nécessite un mock ou une donnée VSF dédiée |

Les valeurs observées ne garantissent pas que les portails externes les
retourneront encore dans le futur. Avant une recette live, contrôler la réponse
réelle de X'Glass et de VSF.

## Scénarios CRM / Opportunité

### CRM-01 — Parcours nominal complet

Préparer une opportunité de test avec la plaque `DS808DZ`, puis ouvrir le
widget et exécuter :

1. rechercher la plaque ;
2. sélectionner le véhicule `397899` ou le candidat correspondant ;
3. sélectionner le calque `PARE-BRISE` ;
4. sélectionner une pièce OE puis une pièce après-marché ;
5. vérifier ou saisir la base `6539R` (section « 4. Base Eurocode », sans recherche VSF : depuis
   le lot E1, l'article se choisit sur le devis, voir SO-01) ;
6. utiliser **Confirmer**, puis enregistrer le formulaire nativement.

Résultats attendus :

- le véhicule Fleet est créé ou retrouvé puis lié par `rpbm_vehicle_id` ;
- la catégorie X'Glass et la pièce concernée sont visibles ;
- la base Eurocode est `6539R` ;
- l'identifiant du véhicule X'Glass sélectionné est mémorisé (`rpbm_xglass_vehicle_id`) ;
- aucun article VSF n'est cherché ni écrit depuis l'opportunité : `rpbm_eurocode`,
  `rpbm_vsf_designation`, `rpbm_vsf_stock` et `rpbm_constructor_reference` restent inchangés ;
- les champs VIN/date MEC/historiques sont complétés uniquement lorsqu'une
  valeur fiable est disponible ;
- aucune erreur `RPC_ERROR` et aucune écriture tarifaire inattendue.

### CRM-02 — Confirmation avec sauvegarde immédiate

Reprendre CRM-01 sur une nouvelle opportunité et utiliser **Confirmer et
enregistrer**.

Résultats attendus : les mêmes valeurs sont envoyées que dans CRM-01, mais
elles sont persistées immédiatement. Une validation Odoo standard doit rester
active si un autre champ requis manque.

### CRM-03 — Réouverture et restauration des sélections

Sur une opportunité ayant déjà les valeurs de CRM-01, fermer puis rouvrir le
widget.

Résultats attendus :

- `DS808DZ` est préremplie ;
- le véhicule et la catégorie sont restaurés ;
- la pièce OE et la pièce après-marché sont restaurées si leurs identifiants
  sont encore présents ;
- `6539R` reste restaurée ;
- le véhicule X'Glass mémorisé est repris s'il figure dans les résultats de l'immatriculation,
  sinon le premier ;
- aucune recherche VSF ne se lance sur l'opportunité (lot E1) ; elle se rejoue sur le devis sans
  repartir d'un état incohérent.

### CRM-04 — Recherche vide et saisie manuelle

Avec la plaque synthétique `ZZ-TEST-00`, vérifier le comportement d'une
recherche sans résultat. Puis utiliser une plaque de test retournant au moins
un véhicule et saisir manuellement `6539R` sans sélectionner de pièce AM.

Résultats attendus : la recherche vide affiche une information exploitable,
ne crée aucun véhicule et ne lève pas d'exception non gérée. La base saisie
manuellement est conservée ; elle permet de rechercher les articles VSF sur le devis (l'opportunité
n'a pas de recherche VSF depuis le lot E1).

### CRM-05 — Autres marques AM sans équivalence AM

Sur un véhicule dont les pare-brises OE n'ont aucune « Équivalence AM » (cas observé : Nissan
X-Trail IV T33, 2022-09 →, pare-brise OE `G27006RA3E`), sélectionner la pièce puis déplier
« Autres marques AM ».

Résultats attendus :

- l'encart est présent et replié tant qu'on ne le déplie pas ;
- au dépliage, un seul appel `/getPieceAm` sans `pieceId` ; replier, déplier ou choisir une
  autre pièce de la même famille n'en relance pas ;
- les lignes suivent l'ordre X'Glass, doublons de fournisseurs compris (cas observé : 13 lignes,
  ARGIC puis PILKINGTON, `6108AGACMU` en premier, validité « A partir de 11/2022 ») ;
- chaque référence tient sur une ligne compacte, comme X'Glass : fournisseur au-dessus de la
  référence à gauche ; libellé, validité et description à droite ; prix en bout de ligne pour
  les seules lignes PILKINGTON ; les cartes « Équivalence AM » restent des cartes ;
- un clic n'importe où sur une ligne la met en évidence, remplit la base (`6108A`) et, sur le
  devis, lance la recherche VSF (sur l'opportunité, depuis le lot E1, aucune recherche) ;
- une famille sans entrée affiche « Aucune autre référence après-marché. », sans erreur.

### CRM-06 — Groupage et Autres AM par famille (lot D, build A)

Scénario de recette du build `17.0.261005.1` : **recette réussie le 2026-10-05 sur le build
`ab31793`**. Les résultats attendus ci-dessous viennent du plan du 2026-10-05 et des
qualifications du 2026-10-01. Depuis le lot E1 (`17.0.261005.3`), l'opportunité n'a plus de
recherche VSF ni de tableau : les étapes 3 et 8 sont adaptées ci-dessous (mention « E1 », non
rejouée) et la recherche VSF se rejoue sur le devis (SO-05). Protocole sans écriture : ne pas confirmer, créer de
produit, définir d'article principal ni ajouter de ligne ; fermer par **Annuler**. Relever par
RPC `write_date` et les champs `rpbm_*` du dossier, de son opportunité et du véhicule lié avant
et après : ils doivent rester inchangés (seule écriture tolérée : le verrou technique
`rpbm_agent.session_lock`, vide en fin de recette).

Véhicule : Nissan X-Trail IV T33 (2022-09 →), plaque `GS600HH`, catégorie `PARE-BRISE`.
Second véhicule pour l'étape 6 : un véhicule X'Glass partageant la même planche et la même
famille principale (immatriculation dans le document de travail local).

1. Rechercher `GS600HH`, sélectionner le véhicule puis la catégorie `PARE-BRISE`, **sans
   sélectionner de pièce**.
   - Attendu : un groupe « Pièces principales » (4 cartes, `RA0E`, `RA1E`, `RA3E`, `RA2E`) puis
     un groupe « Pièces complémentaires » (cales inférieure et supérieure, joint, nécessaire de
     collage, rétroviseur ×2), soit 10 cartes dans l'ordre du portail, regroupées par famille
     avec un bandeau de famille.
   - Attendu : 5 encarts « Autres marques AM » repliés (1 famille principale et 4 familles
     complémentaires), **0 appel** `/getPieceAm` à l'ouverture.
2. Déplier l'encart de la famille `PARE-BRISE`.
   - Attendu : 1 appel `/getPieceAm` sans `pieceId`, 13 lignes (9 ARGIC puis 4 PILKINGTON,
     comme X'Glass). Replier puis déplier : 0 nouvel appel. Les autres encarts restent repliés.
3. Sans sélectionner de pièce, cliquer sur la première ligne.
   - Attendu : ligne mise en évidence, base `6108A`. Sur le devis, section « 5. Article VSF »
     visible et une seule recherche VSF lancée ; sur l'opportunité (E1), « 4. Base Eurocode »
     seulement et aucune recherche VSF.
4. Déplier chacune des quatre familles complémentaires et lire leurs lignes. **Observation sans
   verdict** : noter le nombre d'appels, la présence éventuelle d'une réponse vide ou dégradée,
   puis cliquer sur une ligne de chaque famille et noter la base obtenue. Le plan assume le
   risque d'une base peu pertinente pour les cales, joints, collage et rétroviseurs ; ces
   relevés décident s'il faut reconsidérer le clic « toujours remplir la base ».
5. Sélectionner une pièce principale (par exemple `RA3E`).
   - Attendu : seule la famille de la pièce reste affichée ; « Afficher les autres » rétablit
     tous les groupes. L'état ouvert ou replié des encarts n'a pas changé. Relever la base après
     sélection (le code actuel réinitialise les données dépendantes d'une pièce) ; une
     sélection puis annulation de la pièce ne replie aucun encart.
6. Dans le même dialogue, rechercher le second véhicule puis déplier la famille principale.
   - Attendu (cas connu) : 13 lignes pour le premier véhicule, puis 3 lignes pour le second ;
     1 appel par véhicule, aucune liste resservie d'un véhicule à l'autre ; retour au premier
     véhicule : aucun nouvel appel.
7. Provoquer une expiration de session comme dans ROB-02 avec un encart ouvert.
   - Attendu : reconnexion silencieuse, **aucun encart ouvert et vide** ; au dépliage suivant,
     un nouvel appel et les mêmes 13 lignes qu'avant la reconnexion.
8. Ouvrir un dossier de test dont seule une base Eurocode est mémorisée, sans pièce (cas
   connu : catégorie `PHARE`, base `7310A`).
   - Attendu : les familles de la catégorie et leurs encarts sont affichés sans cartes de
     pièces ; la base `7310A` reste affichée et **aucune recherche** ne se lance seule (R12) ;
     sur le devis, « Rechercher sur VSF » la lance (l'opportunité n'a pas ce bouton, E1) ;
     « Afficher les autres » affiche les cartes.

Dernier contrôle hors protocole : lire dans les logs serveur Odoo.sh les lignes `INFO` par
famille (clés, drapeaux, nombre de pièces) pour tracer les calques et familles non encore
observés ; elles ne contiennent aucune donnée client.

Contrôles hors réseau avant tout push, depuis la racine du dépôt :

- `node rpbm_agent/test_widget_vsf.mjs` ([script](../test_widget_vsf.mjs)). Lot E1 : véhicule
  X'Glass mémorisé (présent dans la liste, inconnu, liste vide), aucune recherche VSF sur
  l'opportunité, séquence de « Créer un devis » (écriture, enregistrement, fermeture des portails
  puis du dialog, action native, dialog du devis), double clic sans doublon, drapeau à usage
  unique, aucun dialog pour un formulaire `crm.lead`, un devis sans opportunité, un devis qui
  n'est pas nouveau ou qui relève d'une autre opportunité, enregistrement refusé ou action rejetée
  sans fuite du drapeau ;
- `python rpbm_agent/test_portal_auth.py` ([script](../test_portal_auth.py)) : chaque XPath des
  dialogs héritiers (2 pour le devis, 4 pour l'opportunité) cible un seul nœud du dialog de base
  (`test_xpath_des_dialogs_ciblent_un_seul_noeud`) ; depuis le build B, le template principal porte le littéral
  `size="'fullscreen'"` (`test_dialog_principal_en_plein_ecran`, garde-fou R22) et l'URL de fiche
  d'un résultat de recherche est absolue (assertion ajoutée à
  `test_vsf_recherche_apparie_les_images_signees`) ;
- `py_compile` des fichiers Python modifiés ;
- rendu Owl local, avec Chromium et l'`owl.js` du code Odoo (scripts locaux, non versionnés) :
  lien direct VSF (R15), vignettes et aperçu (R16, R17) et, au build B, `ArticleComponent` monté
  dans un `<table><tbody>` : en-têtes dans l'ordre, chaque enfant de `tbody` est une ligne, la
  sélection affiche le détail, la légende et les suggestions, un clic sur la ligne appelle
  `onSelect` une fois alors que la vignette, le lien « Fiche technique », Ctrl/Cmd+clic et le clic
  milieu ne l'appellent pas ; au lot E1, les deux dialogs héritiers montés après application de
  leurs XPath par DOM (opportunité sans tableau ni bouton de recherche, « Créer un devis » seulement avec
  un client ; devis avec « 4. Main d'œuvre », « 5. Article VSF » et le tableau) ; les trois modes
  de pièces ne sont pas couverts ici mais par CRM-06 ;
- `git diff --check`.

Le miroir `rpbm_xglass_vehicle_id` du devis vers l'opportunité est couvert par
`tests/test_legacy_sync.py`, qui s'exécute dans le lanceur Odoo (`--test-enable`).

La recette « Tableau VSF en plein écran » plus bas remplace l'ancienne recette R13 à R17 ; elle
vaut pour le build B (`17.0.261005.2`).

### CRM-07 — Créer un devis (lot E1)

Scénario de recette du build `17.0.261005.3`, **non exécuté**. Il **écrit** dans Odoo : le jouer
uniquement sur une opportunité de recette dédiée, avec un client de test, jamais sur un dossier
réel. Le devis brouillon est annulé à la fin et chaque écriture est listée dans le rapport.

1. Relever `write_date` et les champs `rpbm_*` de l'opportunité de test.
2. Ouvrir la fenêtre du widget sur l'opportunité.
   - Attendu : « 4. Base Eurocode » (champ base et lien « Ouvrir dans un nouvel onglet »), sans
     tableau ni bouton « Rechercher sur VSF », et **aucun** appel `/searchBaseEurocode` dans le
     journal réseau.
   - Attendu : « Créer un devis » visible après « Confirmer et enregistrer », actif une fois le
     véhicule et la catégorie choisis.
   - Attendu : Ctrl+Entrée déclenche « Confirmer », pas « Créer un devis » (contrôle sans
     enregistrer : abandonner ensuite les modifications du formulaire).
   - Attendu : le bouton est absent sur une opportunité sans client et sur une piste.
3. Parcourir `GS600HH` › `PARE-BRISE` › une pièce › une ligne « Autres marques AM », base `6108A` ;
   si possible, choisir le second véhicule d'une immatriculation qui en renvoie plusieurs. Faire un
   **double clic** sur « Créer un devis ».
   - Attendu : une seule sauvegarde de l'opportunité, avec `rpbm_xglass_vehicle_id` renseigné ;
     `rpbm_eurocode`, `rpbm_vsf_designation`, `rpbm_vsf_stock` et `rpbm_constructor_reference`
     inchangés.
   - Attendu : un seul devis, non enregistré, lié à l'opportunité.
   - Attendu : la fenêtre du devis s'ouvre seule avec la même restauration : véhicule mémorisé,
     pièce, recherche `6108A` automatique, « 4. Main d'œuvre » puis « 5. Article VSF ».
4. Sur le devis, ajouter un article (créer le produit si besoin : écriture à lister) et une
   opération de main-d'œuvre, puis « Confirmer et enregistrer ».
   - Attendu : le devis brouillon est enregistré ; les champs de l'opportunité sont cohérents avec
     le devis (miroirs `related`).
5. Annuler le devis de test, puis lister toutes les écritures : opportunité, devis, lignes,
   produit, véhicule et verrou technique `rpbm_agent.session_lock`.

Cas limite accepté : sur une opportunité sans pièce OE, avec seulement une ligne « Autres marques
AM » et une base, le devis s'ouvre sans recherche VSF automatique (R12) ; il faut un clic sur
« Rechercher sur VSF ».

## Scénarios devis

### SO-01 — Devis avec opportunité

Créer un devis lié à une opportunité de test issue de CRM-01. Ouvrir la
fenêtre par la loupe du devis (le chemin « Créer un devis » relève de CRM-07 et
SO-06), rejouer la recherche `DS808DZ`, sélectionner `PARE-BRISE`, puis
l'article `6539RGSH5RD`.

Résultats attendus :

- les champs `related` du devis reflètent l'opportunité ;
- aucune seconde source indépendante n'est créée sur `sale.order` ;
- l'article peut être recherché/créé puis ajouté comme ligne de devis ;
- deux articles distincts peuvent être ajoutés sans supprimer les lignes
  préexistantes ;
- `carrier_id` reste à renseigner ou est prérempli uniquement si le lieu CRM
  fournit une correspondance déterministe.

### SO-02 — Devis sans opportunité

Créer un devis de test sans `opportunity_id`.

Résultat attendu : la page de l'assistant véhicule est masquée et aucune
écriture X'Glass, Fleet ou Eurocode n'est tentée.

### SO-03 — Création produit et doublon

Sur un devis avec opportunité, tester successivement :

- `6571AGRCHIMVZ`, absent du catalogue produit de test ;
- le même article une seconde fois ;
- la suggestion `PP-COLLE310`.

Résultats attendus :

- le premier clic crée un seul produit et sa ligne fournisseur ;
- le second clic retrouve le produit sans doublon ;
- la suggestion dispose des mêmes actions que l'article principal ;
- le retrait ne supprime qu'une ligne créée par le widget pendant la dialog.

### SO-04 — Opérations de main-d'œuvre X'Glass

Sur un devis de test avec opportunité, sélectionner une pièce qui renvoie des
opérations T1, T2 ou T3, cocher plusieurs opérations puis les ajouter.

Résultats attendus :

- une ligne de service par opération, avec quantité égale à la durée X'Glass ;
- le produit et ses taxes viennent du tarif Odoo T1/T2/T3, sans calcul Studio ;
- le rechargement du devis ne crée aucun doublon et permet de retirer seulement
  la ligne portant la provenance de l'opération ;
- une opération sans durée, identifiant ou taux reconnu reste indisponible ;
- les lignes manuelles, le champ Studio agrégé et le produit « Pose à Domicile »
  restent inchangés.

### SO-05 — Dialog devis après découplage de la section VSF (lot D, build A)

Sur un devis lié à une opportunité (même protocole sans écriture que CRM-06 ; recette réussie le 2026-10-05 sur le build `ab31793`) :

1. Sélectionner une pièce : les sections « 4. Main d'œuvre » et « 5. Article VSF » sont
   toutes deux présentes, dans cet ordre.
2. Rouvrir sans pièce, déplier un encart « Autres marques AM » et cliquer sur une ligne :
   « 5. Article VSF » apparaît, la recherche VSF se lance, « 4. Main d'œuvre » reste absente
   (elle suit la pièce sélectionnée ; la numérotation saute de 3 à 5, constat déjà présent pour
   une base restaurée seule).
3. Aucune action de devis (ajout, retrait) n'est exécutée.

### SO-06 — Ouverture automatique du dialog sur le devis (lot E1)

Scénario du build `17.0.261005.3`, **non exécuté**, à jouer sur l'opportunité de recette de CRM-07.
Il crée des devis brouillons : les lister, puis les annuler.

1. Ouverture : après « Créer un devis » (CRM-07), la fenêtre du widget s'ouvre seule sur le
   nouveau devis, une seule fois. La fermer (**Annuler**) : elle ne se rouvre pas d'elle-même ;
   la loupe la rouvre.
2. Aller-retour : revenir à l'opportunité par le fil d'Ariane, puis rouvrir le devis : la fenêtre
   ne s'ouvre pas.
3. « Nouveau devis » natif, depuis l'opportunité : le formulaire s'ouvre sans fenêtre du widget.
4. Ventes › Devis › Nouveau : le formulaire s'ouvre sans fenêtre du widget.
5. Recharger la page sur un devis enregistré : aucune ouverture.
6. Un nouveau clic sur « Créer un devis » ouvre un nouveau devis ; les devis existants de
   l'opportunité ne sont ni réutilisés ni modifiés.

## Tableau VSF en plein écran (R21, R22, reprise de R15 à R17)

Recette sans écriture du tableau VSF en plein écran (build `17.0.261005.2`) : **recette réussie le
2026-10-05 sur le build `6cbecd3`**, sans écriture métier. Elle remplace la recette R13 à R17
(cartes sur une colonne) : le tableau remplace R13 et R14, et R15 à R17 sont repris aux étapes 8 à
10. Depuis le lot E1 (`17.0.261005.3`), le tableau n'existe plus sur l'opportunité : pour la
rejouer, les étapes 2 à 11 se font sur un devis lié à une opportunité ; seules l'étape 1 (plein
écran) et l'étape 12 (non-régression) concernent aussi l'opportunité.

Lire d'abord la version du module par RPC. Ouvrir un dossier de test ayant une base Eurocode
mémorisée : un devis lié à une opportunité, sauf mention contraire. Ne pas confirmer le dialogue, créer un produit, définir un article principal ni ajouter de ligne ;
fermer par **Annuler**. Relever par RPC `write_date` et les champs `rpbm_*` avant et après sur le
dossier, son opportunité et le véhicule lié : toutes ces valeurs doivent rester inchangées (seule
écriture tolérée : le verrou technique `rpbm_agent.session_lock`, vide en fin de recette).

1. **Plein écran (R22).** Ouvrir le dialogue, sur le devis puis sur l'opportunité.
   - Attendu : `.modal-dialog` porte la classe `modal-fullscreen` (et non plus `modal-lg`) ; la
     fenêtre prend toute la largeur de l'écran, avec des coins carrés.
   - Observation sans verdict : relever la largeur de la fenêtre et l'aspect des sections 1 à 3
     (véhicules, catégories, pièces) en pleine largeur ; les écrans du client sont estimés à
     1333 px, non vérifiés.
2. **Boutons visibles avec un long tableau.** Rechercher `6108A` (21 articles observés le
   2026-10-02 ; sinon réduire la hauteur de la fenêtre), puis faire défiler jusqu'au bas du
   tableau.
   - Attendu : seul le corps du dialogue défile ; l'en-tête et le pied restent fixes, et
     « Confirmer », « Confirmer et enregistrer » et « Annuler » restent dans la fenêtre à toutes
     les positions de défilement.
3. **Colonnes.**
   - Attendu : un tableau `vsf_articles` avec sept en-têtes, dans cet ordre : Eurocode,
     Désignation, Réf. constructeur, Stock, Prix, Coût, Photo ; une ligne par article et un groupe
     (`tbody`) par article principal ; aucune carte dans la section VSF ; le lien « Fiche
     technique » suit la désignation ; le stock est une quantité, ou « Indisponible ».
4. **Eurocodes alignés (R14).** Rechercher `6108A` puis `6574A` et comparer des codes de longueurs
   différentes.
   - Attendu : la colonne Eurocode est en police à chasse fixe, sans retour à la ligne ; tous les
     codes commencent à la même abscisse et chaque rang (marque, modèle, emplacement, couleur,
     option) tombe dans la même colonne verticale d'une ligne à l'autre ; aucune séparation
     ajoutée entre les rangs.
5. **Une vignette par ligne.**
   - Attendu : la colonne Photo n'affiche que la première vignette, même pour un article qui en a
     plusieurs ; une ligne sans image garde une cellule vide, sans erreur JavaScript (ROB-05).
6. **Sélection et détail.** Cliquer sur une ligne, hors vignette et hors lien.
   - Attendu : la ligne est surlignée et une ligne de détail s'ouvre juste en dessous, avec toutes
     les vignettes de l'article (sans les photos du modèle), ses caractéristiques techniques (ou
     « Détails VSF indisponibles ») puis ses actions : « Définir comme article principal »,
     produit Odoo (« Voir le produit » ou « Créer le produit ») et, sur un devis, « Ajouter au
     devis » quand le produit existe. Ne cliquer sur aucun de ces boutons.
   - Attendu : un second clic sur la ligne la désélectionne et referme son détail ; deux articles
     peuvent rester sélectionnés ensemble ; un clic dans la ligne de détail (zone vide, texte,
     vignette) ne désélectionne pas l'article.
7. **Suggestions.** Sélectionner un article qui en a (par exemple `6571AGRCHIMVZ`).
   - Attendu : sous sa ligne de détail, une ligne de légende « Articles suggérés par VSF » puis
     une ligne par suggestion, dans le même groupe ; chaque suggestion se sélectionne de la même
     façon (surlignage, ligne de détail avec ses propres actions) ; désélectionner l'article
     principal retire la légende, les suggestions et leurs sélections.
8. **Lien « Ouvrir dans un nouvel onglet » (reprise de R15).**
   - Remplacer la base par une valeur réelle (par exemple `6574A`) sans quitter le champ : le
     lien suit la valeur saisie, également par Ctrl+clic ou clic central avant validation du
     champ. La saisie ne lance pas un RPC par caractère.
   - Ne pas saisir de valeur synthétique (`+`, `&`, espace) dans le champ du devis : la perte de
     focus, même celle de la fenêtre, valide le champ et l'envoie au portail, qui répond par un
     message trompeur (« portail VSF inaccessible »). L'encodage est couvert hors réseau
     (`test_widget_vsf.mjs`).
   - Vider le champ : le lien est désactivé au clavier comme à la souris (le cas des espaces seuls
     n'est pas rejoué en direct, pour la même raison). Renseigner une base valide : il redevient
     utilisable.
   - Ouvrir une base valide dans le nouvel onglet : VSF affiche la recherche, après connexion si
     nécessaire ; le contexte du widget reste disponible dans l'onglet d'origine.
9. **Clics modifiés sans sélection (reprise de R16).** Sur une ligne non sélectionnée :
   - Attendu : le lien « Fiche technique » a une URL VSF complète
     (`https://client.myvsf.fr/catalogue/article/…`), jamais une URL du domaine Odoo ; clic simple,
     Ctrl/Cmd+clic et clic milieu l'ouvrent dans un nouvel onglet, sans sélectionner la ligne ;
   - Attendu : sur la vignette, Ctrl/Cmd+clic et clic milieu ouvrent l'image VSF signée dans un
     nouvel onglet, sans aperçu interne ni sélection ; un clic simple ouvre l'aperçu interne et
     laisse la sélection inchangée.
10. **Aperçu (reprise de R17).** Ouvrir l'aperçu depuis la vignette de la colonne Photo, puis
    depuis une vignette de la ligne de détail.
    - Attendu : la même liste de photos de l'article, sans les photos du modèle de véhicule ; ←/→
      font défiler en boucle (après la dernière, la première ; avant la première, la dernière) ;
      avec une seule photo, l'aperçu reste stable ; il s'ouvre au-dessus du dialogue plein écran
      et « Fermer » ne ferme que lui.
11. **Devis et opportunité (lot E1).**
    - Sur le devis (SO-05) : « 4. Main d'œuvre X'Glass » (avec une pièce sélectionnée) puis « 5.
      Article VSF », avec le tableau et ses lignes de détail. « Retirer du devis » n'apparaît
      qu'après un ajout : il relève de SO-03, hors protocole sans écriture.
    - Sur l'opportunité : « 4. Base Eurocode » sans tableau ni bouton « Rechercher sur VSF » ; le
      lien « Ouvrir dans un nouvel onglet » reste.
12. **Non-régression.** Rejouer CRM-03 et CRM-05 : base restaurée avec et sans pièce AM, aucune
    recherche automatique sans pièce mémorisée, « Autres marques AM » chargé une seule fois par
    véhicule et famille, puis base remplie au clic.

Les références de dossiers et les preuves live restent dans le document de travail local.

## Scénarios de robustesse

| ID | Précondition | Action | Résultat attendu |
|---|---|---|---|
| ROB-01 | Deux véhicules candidats | Changer rapidement de véhicule | Une seule planche et une seule métadonnée correspondent au véhicule finalement sélectionné |
| ROB-02 | Session X'Glass expirée | Déclencher une recherche ou une sélection | Reconnexion proposée, contexte conservé, action rejouée au plus une fois. Après reconnexion, mêmes pièces AM qu'avant (GS600HH, pièce `G27006RA3E` : aucune « Équivalence AM », 13 « Autres marques AM » avec validité) |
| ROB-03 | VIN Fleet déjà renseigné | Confirmer avec une valeur X'Glass différente | Le VIN Fleet valide n'est pas écrasé |
| ROB-04 | VIN Fleet de forme `var = <VIN>;` | Confirmer avec une valeur X'Glass valide | Le VIN malformé est nettoyé et remplacé par le VIN valide |
| ROB-05 | Devis ; article sans image ou stock | Sélectionner l'article | La ligne reste utilisable, sans erreur JavaScript |
| ROB-06 | Catégorie non couverte | Sélectionner un calque comme `PHARE` ou `ESSUIE-GLACE AV` | `Autre...` est suggéré, reste modifiable et le libellé X'Glass exact est conservé |

## Preuve à consigner

Pour chaque scénario, noter séparément :

- l'instance, la base et le commit testé ;
- l'identifiant de l'opportunité/devis de test ;
- les appels réseau principaux et leur résultat ;
- les valeurs visibles avant et après sauvegarde ;
- la relecture après rechargement complet ;
- les erreurs de console ou serveur ;
- le verdict `PASS`, `FAIL` ou `BLOCKED` et sa justification.

Ne pas utiliser de données client réelles dans ce jeu de test et ne pas
consigner de secrets de portail.
