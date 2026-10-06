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
| Suggestion VSF sans produit propre | `6108AXSR` « GEL CAPTEUR SILICONE » | Observée (2026-10-05) | Faux rattachement par le nom (SO-07) |
| Produit Odoo de même nom, d'un autre article | code `6574AXSH` | Observée (2026-10-05) | Ne doit pas être rattaché à `6108AXSR` (SO-07) |
| Article VSF dont le produit Odoo existe déjà | `6574AGACIMVZ` (base `6574A`) | Observée (2026-10-06) | « Ajouter au devis » puis « Retirer du devis » (SO-08) |
| Plaque sans résultat | `ZZ-TEST-00` | Synthétique | Scénario de recherche vide ; nécessite un mock ou une donnée X'Glass dédiée |
| Base sans résultat | `9999Z` | Observée (2026-10-06) | VSF répond 200, sans liste d'articles, par la page « Aucun résultat ne correspond à votre recherche. » ; même réponse pour `61-08A` et `A+B &C D` (trace). Aucun mock nécessaire (SO-09) |

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
rejouée) et la recherche VSF se rejoue sur le devis (SO-05). Depuis le lot E2 (`17.0.261006.2`), le
devis s'ouvre sans X'Glass : pour rejouer les étapes X'Glass de ce scénario sur un devis, cliquer
d'abord sur « Charger X'Glass » (voir SO-10), et la recherche VSF y part dès l'ouverture, ce qui
change l'attendu de l'étape 8 sur le devis (aucune recherche seule au lot D ; recherche immédiate
depuis le lot E2). Protocole sans écriture : ne pas confirmer, créer de
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
  sans fuite du drapeau. Lot E1.1 : `getRecordData()` sur un dialog dont les trois identifiants de
  pièce sont mémorisés :
  - confirmation avant le chargement des pièces, pièce introuvable et effets automatiques : rien
    n'est écrit ;
  - pièce retrouvée : écrite ; pièce AM absente des équivalences (« Autres marques AM ») :
    conservée ; pièce AM retrouvée : écrite ;
  - autre pièce, désélection, autre catégorie, ligne AM (pièce AM seulement), autre véhicule et
    recherche d'immatriculation de l'utilisateur : valeurs remplacées ou vidées ;
  - effet sur `vehicules`, recherche automatique de l'ouverture (`init`), clic sur le véhicule ou
    la catégorie déjà affichés : rien n'est libéré ;
- le même script, lot correctif `17.0.261006.1` : R24, `vsfNoResultFor` retient la base d'une
  recherche aboutie sans article et s'efface par un résultat, par une erreur ou par
  `clearSelectedPiece()` ; R28, la ligne ajoutée est retrouvée par son produit même quand `records`
  contient un autre objet (« Retirer du devis », puis retrait de la bonne ligne), et un produit déjà
  présent à l'ouverture reste « déjà présent », sans ajout possible ;
- le même script, lot E2 (`17.0.261006.2`) : devis avec une base, une recherche `/searchBaseEurocode`
  sans authentification ni `/rpbm_agent_close` ; `getRecordData()` sans X'Glass (base et quatre champs
  d'article seulement) et avec véhicule et catégorie (écriture complète, libellé de pièce compris) ;
  `clearSelectedPiece(true)` qui garde tableau et sélection ; le passage de `agentsInitialized` à vrai
  qui ne relance pas la recherche ; la pièce concernée enregistrée qui survit à la restauration ; une
  réponse de recherche périmée ignorée ; l'opportunité inchangée (le harnais force `agentsInitialized`
  à vrai : ces tests le remettent à faux) ; bloc « Revue E2 » : devis avec catégorie mais sans base ni
  pièce qui garde base, tableau et article principal à travers « Charger X'Glass » et la vraie chaîne,
  libellé d'une pièce « Autres marques AM » mémorisée seule conservé, base sans résultat que les effets
  ne relancent pas et que le bouton relance, deux « Charger X'Glass » rapprochés pour une seule
  authentification, dialog fermé pendant « Charger X'Glass » (un seul `/rpbm_agent_close`, aucun autre appel ni état modifié) ;
- `python rpbm_agent/test_portal_auth.py` ([script](../test_portal_auth.py)) : chaque XPath des
  dialogs héritiers (2 pour le devis, 4 pour l'opportunité) cible un seul nœud du dialog de base
  (`test_xpath_des_dialogs_ciblent_un_seul_noeud`) ; depuis le build B, le template principal porte le littéral
  `size="'fullscreen'"` (`test_dialog_principal_en_plein_ecran`, garde-fou R22) et l'URL de fiche
  d'un résultat de recherche est absolue (assertion ajoutée à
  `test_vsf_recherche_apparie_les_images_signees`) ; au lot correctif `17.0.261006.1`, la page VSF
  « aucun résultat » (image `no-result.png`, texte, ou les deux) renvoie `[]` sans requête POST
  (`test_vsf_recherche_sans_resultat_sans_post`), et une page sans liste d'articles ni message
  « aucun résultat » lève une `VSFError` qui ne parle pas de session
  (`test_vsf_recherche_page_inattendue`) ; au lot E2, la session VSF à la demande : une seule
  connexion pour deux appels, une expiration suivie d'une reconnexion puis d'un succès, un second
  `VSFAuthError` propagé, une connexion refusée qui laisse `logged_in` faux, deux threads de la même
  génération pour une seule reconnexion ;
- `py_compile` des fichiers Python modifiés ;
- rendu Owl local, avec Chromium et l'`owl.js` du code Odoo (scripts locaux, non versionnés) :
  lien direct VSF (R15), vignettes et aperçu (R16, R17) et, au build B, `ArticleComponent` monté
  dans un `<table><tbody>` : en-têtes dans l'ordre, chaque enfant de `tbody` est une ligne, la
  sélection affiche le détail, la légende et les suggestions, un clic sur la ligne appelle
  `onSelect` une fois alors que la vignette, le lien « Fiche technique », Ctrl/Cmd+clic et le clic
  milieu ne l'appellent pas ; au lot E1, les deux dialogs héritiers montés après application de
  leurs XPath par DOM (opportunité sans tableau ni bouton de recherche, « Créer un devis » après
  « Confirmer et enregistrer », absent sur une piste ; devis avec « 4. Main d'œuvre », « 5. Article
  VSF » et le tableau) ; au lot E1.1, « Créer un devis » grisé sans client avec l'info-bulle sur son
  enveloppe et actif avec un client, boutons d'écriture désactivés pendant un chargement (opportunité
  et devis), clic sur une carte véhicule câblé sur `onClickVehicule` ; les trois modes de pièces ne
  sont pas couverts ici mais par CRM-06 ;
- `git diff --check`.

Le miroir `rpbm_xglass_vehicle_id` du devis vers l'opportunité est couvert par
`tests/test_legacy_sync.py`, et le rattachement d'un article VSF à un produit (lot E1.1) par
`tests/test_find_existing_product.py` (six tests, valeurs propres au test, voir
[backend](technique/backend.md#rattachement-dun-article-vsf-à-un-produit-lot-e11)) ; ils demandent
une base PostgreSQL et le lanceur Odoo avec `--test-enable`. Le poste de développement n'a pas
PostgreSQL et le build de staging met le module à jour sans `--test-enable`. Le test de
rattachement est **non exécuté, abandonné sur décision de l'utilisateur (2026-10-06)** ; le fichier
reste dans le dépôt. La recette live du 2026-10-05 ne couvre que le cas d'origine, par SO-07,
étape 1.

La recette « Tableau VSF en plein écran » plus bas remplace l'ancienne recette R13 à R17 ; elle
vaut pour le build B (`17.0.261005.2`).

### CRM-07 — Créer un devis (lot E1)

Scénario de recette des lots E1 (`17.0.261005.3`) et E1.1 (`17.0.261005.4`). Il **écrit** dans
Odoo : le jouer uniquement sur une opportunité de recette dédiée, avec un client de test, jamais sur
un dossier réel. Le devis brouillon est annulé à la fin et chaque écriture est listée dans le rapport.

**Recette réussie le 2026-10-05**, en `17.0.261005.4`, pour E1 et E1.1 ensemble. Points vérifiés,
notamment : à l'étape 2, la section arrêtée à « 4. Base Eurocode » sans aucune recherche VSF, le
raccourci Ctrl+Entrée toujours sur « Confirmer » et, sur une opportunité sans client, « Créer un
devis » grisé avec l'info-bulle ; à l'étape 3, la ligne « Autres marques AM » choisie (13 lignes, un
seul `/getPieceAm` sans `pieceId`, première ligne ARGIC `6108AGACMU`, base `6108A`), un seul
enregistrement et un seul appel à l'action native après un double clic, puis la fenêtre du devis
ouverte seule, avec le véhicule, la pièce et la base `6108A` restaurés, la recherche VSF automatique
(21 articles) et « 4. Main d'œuvre » ; aux étapes 4 et 5, un devis enregistré avec ses deux lignes,
puis annulé. Le contrôle du second véhicule (étape 3) est **impossible** avec `GS600HH`, qui ne
renvoie qu'un seul véhicule X'Glass : il faut une plaque qui en renvoie plusieurs. La recette a aussi
relevé que « Retirer du devis » manquait après « Ajouter au devis » (R28, corrigé au lot
`17.0.261006.1` : voir SO-08).

1. Relever `write_date` et les champs `rpbm_*` de l'opportunité de test.
2. Ouvrir la fenêtre du widget sur l'opportunité.
   - Attendu : « 4. Base Eurocode » (champ base et lien « Ouvrir dans un nouvel onglet »), sans
     tableau ni bouton « Rechercher sur VSF », et **aucun** appel `/searchBaseEurocode` dans le
     journal réseau.
   - Attendu : « Créer un devis » visible après « Confirmer et enregistrer », actif une fois le
     véhicule et la catégorie choisis et les chargements terminés (les trois boutons d'écriture sont
     grisés pendant un chargement).
   - Attendu : Ctrl+Entrée déclenche « Confirmer », pas « Créer un devis » (contrôle sans
     enregistrer : abandonner ensuite les modifications du formulaire).
   - Attendu : le bouton est absent sur une piste ; sur une opportunité sans client, il est grisé,
     avec l'info-bulle « Renseignez le client de l'opportunité pour créer un devis. » au survol du
     bouton grisé (l'info-bulle est portée par son enveloppe : à vérifier à la souris).
3. Parcourir `GS600HH` › `PARE-BRISE` › une pièce › une ligne « Autres marques AM », base `6108A` ;
   avec une plaque qui renvoie plusieurs véhicules X'Glass (`GS600HH` n'en renvoie qu'un), choisir le
   second. Faire un **double clic** sur « Créer un devis ».
   - Attendu : une seule sauvegarde de l'opportunité, avec `rpbm_xglass_vehicle_id`, les
     identifiants de pièce (X'Glass, OE, AM) et le libellé de la pièce (`rpbm_xglass_piece_label`,
     lot E2) renseignés ;
     `rpbm_eurocode`, `rpbm_vsf_designation`, `rpbm_vsf_stock` et `rpbm_constructor_reference`
     inchangés.
   - Attendu : un seul devis, non enregistré, lié à l'opportunité.
   - Attendu (lot E2, non rejoué ; au lot E1 : restauration immédiate, voir l'en-tête) : la fenêtre
     du devis s'ouvre seule **sans authentification X'Glass** ni seconde connexion : encart « Dossier »
     (véhicule, catégorie, pièce concernée, libellé de la pièce, article principal) et recherche
     `6108A` immédiate. « Charger X'Glass » restaure alors le véhicule mémorisé, la pièce, la pièce AM,
     puis « 4. Main d'œuvre » et « 5. Article VSF », sans vider le tableau.
4. Sur le devis, ajouter un article (créer le produit si besoin : écriture à lister) et, après
   « Charger X'Glass », une opération de main-d'œuvre, puis « Confirmer et enregistrer ».
   - Attendu : le devis brouillon est enregistré ; les champs de l'opportunité sont cohérents avec
     le devis (miroirs `related`).
5. Annuler le devis de test, puis lister toutes les écritures : opportunité, devis, lignes,
   produit, véhicule et verrou technique `rpbm_agent.session_lock`. Y ajouter les effets de bord
   natifs de l'enregistrement : les messages de suivi et, quand l'enregistrement du devis réécrit
   les champs miroirs, les enregistrements `x_audit` qu'une automatisation Studio crée (environ 75
   par enregistrement de devis, R29, non qualifié).

Cas limite accepté : sur une opportunité sans pièce OE, avec seulement une ligne « Autres marques
AM » et une base, le devis s'ouvre sans recherche VSF automatique (R12) ; il faut un clic sur
« Rechercher sur VSF ».

### CRM-08 — Pièce mémorisée conservée (lot E1.1)

Scénario de recette du build `17.0.261005.4`. Il **écrit** dans Odoo : même règle que CRM-07
(opportunité de recette dédiée, client de test, écritures listées). Relever par RPC, avant et après
chaque étape, `rpbm_xglass_piece_id`, `rpbm_piece_oe_id`, `rpbm_piece_am_id`, `rpbm_eurocode_base`
et `rpbm_xglass_vehicle_id` de l'opportunité.

**Recette réussie le 2026-10-05**, avec CRM-07. Points vérifiés :
- étape 2 : les boutons d'écriture sont grisés pendant tous les chargements, avec un passage à l'état
  actif de 55 ms entre deux chargements enchaînés (accepté, voir l'attendu) ; un clic réel sur
  « Confirmer » pendant un chargement est sans effet ;
- étape 3 : la confirmation sans rien toucher ne réécrit ni la pièce ni la pièce AM ;
- étape 5 : la ligne « Autres marques AM » mémorisée ne revient pas sélectionnée à la réouverture
  mais reste mémorisée : la sauvegarde ne contient pas `rpbm_piece_am_id` et seul `write_date` change ;
- étape 7 : un nouveau clic sur le véhicule et sur la catégorie déjà affichés ne déclenche aucun
  appel réseau, et la pièce AM reste mémorisée (le lien « Voir » n'a pas été essayé).

Étapes 4 et 6 non jouées. Deux points restent **non vérifiés** (voir en fin de scénario).

1. Partir d'une opportunité de recette avec véhicule, catégorie, pièce OE et pièce AM mémorisés
   (issus de CRM-07).
2. Rouvrir la fenêtre et observer le pied pendant le chargement.
   - Attendu : « Confirmer », « Confirmer et enregistrer » et « Créer un devis » sont grisés tant
     qu'un chargement est en cours, puis s'activent à l'arrivée des pièces. Un bref passage à l'état
     actif entre deux chargements enchaînés n'est pas un échec : seules comptent les valeurs relevées
     (étape 3).
3. Rouvrir, puis « Confirmer et enregistrer » dès que les boutons sont actifs, sans toucher à la
   sélection.
   - Attendu : les valeurs relevées sont inchangées.
4. Pièce introuvable : remplacer par RPC `rpbm_xglass_piece_id` et `rpbm_piece_oe_id` par un
   identifiant que X'Glass ne renvoie pas (écriture à lister), rouvrir, puis « Confirmer et
   enregistrer » sans toucher aux pièces.
   - Attendu : la pièce n'est pas retrouvée, mais les identifiants mémorisés sont inchangés.
5. Ligne « Autres marques AM » : mémoriser une pièce AM choisie dans « Autres marques AM » (CRM-05),
   rouvrir, puis « Confirmer et enregistrer » sans toucher à la sélection.
   - Attendu : `rpbm_piece_am_id` est inchangé, bien que la ligne ne soit pas re-sélectionnée à la
     réouverture.
6. Actions explicites : pour chacune, rouvrir la fenêtre, la faire, puis « Confirmer et
   enregistrer » : cliquer sur une autre pièce ; cliquer de nouveau sur la pièce sélectionnée pour
   la désélectionner ; cliquer sur une **autre** catégorie ; cliquer sur un **autre** véhicule (si
   l'immatriculation en renvoie plusieurs) ; relancer « Rechercher » avec succès ; cliquer sur une
   carte « Équivalence AM » ou une ligne « Autres marques AM ».
   - Attendu : les identifiants écrits sont ceux de la sélection affichée après l'action, remplacés
     par la nouvelle sélection ou vidés lorsqu'elle est retirée ou n'est plus retrouvée ; pour une
     carte ou une ligne après-marché, seul `rpbm_piece_am_id` change.
7. Actions sans effet : rouvrir la fenêtre, cliquer de nouveau sur le véhicule et sur la catégorie
   déjà affichés (et sur « Voir » dans la carte du véhicule affiché), puis « Confirmer et
   enregistrer ».
   - Attendu : les identifiants mémorisés sont inchangés.

**Non vérifié à la recette du 2026-10-05** (limites connues du code, à observer à la prochaine
occasion, sans verdict) :

- **Ligne « Autres marques AM » choisie pendant la restauration de la pièce AM.** Cliquer une ligne
  « Autres marques AM » pendant que la pièce AM mémorisée se charge : `getPieceAm()` réassigne la
  sélection avec le résultat de sa recherche parmi les équivalences (la pièce mémorisée, ou rien), si
  bien que la ligne choisie peut être remplacée et `rpbm_piece_am_id` écrit vide à la confirmation
  (comportement antérieur à E1.1). La fenêtre est étroite : le clic doit tomber pendant le
  chargement. Relever `rpbm_piece_am_id` après « Confirmer et enregistrer ».
- **Largeur de téléphone.** Ouvrir l'opportunité à 375 px : « Créer un devis » est enveloppé dans un
  `<span>` qui porte l'info-bulle. Relever s'il reste entier, visible et utilisable dans le pied de
  la fenêtre.

## Scénarios devis

### SO-01 — Devis avec opportunité

Créer un devis lié à une opportunité de test issue de CRM-01. Ouvrir la
fenêtre par la loupe du devis (le chemin « Créer un devis » relève de CRM-07 et
SO-06), cliquer sur « Charger X'Glass » (le devis s'ouvre sans X'Glass depuis le lot E2), rejouer la
recherche `DS808DZ`, sélectionner `PARE-BRISE`, puis l'article `6539RGSH5RD`.

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
- le second clic retrouve le produit sans doublon, par son eurocode (lot E1.1) ;
- la suggestion dispose des mêmes actions que l'article principal ;
- le retrait ne supprime qu'une ligne créée par le widget pendant la dialog (voir SO-08).

### SO-04 — Opérations de main-d'œuvre X'Glass

Sur un devis de test avec opportunité, cliquer sur « Charger X'Glass » (la main-d'œuvre
n'apparaît qu'après, lot E2), sélectionner une pièce qui renvoie des opérations T1, T2 ou T3, cocher
plusieurs opérations puis les ajouter.

Résultats attendus :

- une ligne de service par opération, avec quantité égale à la durée X'Glass ;
- le produit et ses taxes viennent du tarif Odoo T1/T2/T3, sans calcul Studio ;
- le rechargement du devis ne crée aucun doublon et permet de retirer seulement
  la ligne portant la provenance de l'opération ;
- une opération sans durée, identifiant ou taux reconnu reste indisponible ;
- les lignes manuelles, le champ Studio agrégé et le produit « Pose à Domicile »
  restent inchangés.

### SO-05 — Dialog devis après découplage de la section VSF (lot D, build A)

Sur un devis lié à une opportunité (même protocole sans écriture que CRM-06 ; recette réussie le 2026-10-05 sur le build `ab31793`). Depuis le lot E2, le devis s'ouvre sans X'Glass : cliquer d'abord sur « Charger X'Glass » ; les étapes ci-dessous valent ensuite (adaptation non rejouée) :

1. Sélectionner une pièce : les sections « 4. Main d'œuvre » et « 5. Article VSF » sont
   toutes deux présentes, dans cet ordre.
2. Rouvrir sans pièce, déplier un encart « Autres marques AM » et cliquer sur une ligne :
   « 5. Article VSF » est présente (dès l'ouverture depuis le lot E2), la base est remplie et la
   recherche VSF se relance, « 4. Main d'œuvre » reste absente (elle suit la pièce sélectionnée ;
   la numérotation saute de 3 à 5, constat déjà présent pour une base restaurée seule).
3. Aucune action de devis (ajout, retrait) n'est exécutée.

### SO-06 — Ouverture automatique du dialog sur le devis (lot E1)

Scénario du build `17.0.261005.3`, à jouer sur l'opportunité de recette de CRM-07. Il crée des
devis brouillons : les lister, puis les annuler.

**Recette réussie le 2026-10-05**, en `17.0.261005.4` : étapes 1 à 5. La fenêtre s'ouvre seule, et ne
se rouvre ni après l'enregistrement du devis ni après « Annuler » (la loupe la rouvre), ni par le fil
d'Ariane, ni par « Nouveau devis » natif, ni par Ventes › Devis › Nouveau, ni au rechargement du
devis (aucun dialog ni requête `/rpbm_agent_*`). Étape 6 non jouée, volontairement : elle aurait créé
un second devis.

1. Ouverture : après « Créer un devis » (CRM-07), la fenêtre du widget s'ouvre seule sur le
   nouveau devis, une seule fois (sans X'Glass depuis le lot E2 : encart « Dossier » et recherche
   VSF, voir SO-10). La fermer (**Annuler**) : elle ne se rouvre pas d'elle-même ;
   la loupe la rouvre.
2. Aller-retour : revenir à l'opportunité par le fil d'Ariane, puis rouvrir le devis : la fenêtre
   ne s'ouvre pas.
3. « Nouveau devis » natif, depuis l'opportunité : le formulaire s'ouvre sans fenêtre du widget.
4. Ventes › Devis › Nouveau : le formulaire s'ouvre sans fenêtre du widget.
5. Recharger la page sur un devis enregistré : aucune ouverture.
6. Un nouveau clic sur « Créer un devis » ouvre un nouveau devis ; les devis existants de
   l'opportunité ne sont ni réutilisés ni modifiés.

### SO-07 — Rattachement d'un article VSF à un produit Odoo (lot E1.1)

Scénario du build `17.0.261005.4`. Les étapes 1 et 2 sont sans écriture : ne pas cliquer
« Créer le produit », « Ajouter au devis » ni « Définir comme article principal » ; relever
`write_date` et les champs `rpbm_*` du devis, de son opportunité et du véhicule lié avant et après.

**Recette réussie le 2026-10-05, avec une réserve** : étapes 1 et 2. VSF ne proposant plus `6108AXSR`
en suggestion, le contrôle de l'étape 1 a porté sur sa ligne principale : `/doesProductExists` répond
`false`, la ligne affiche « Article absent de la base Odoo » avec « Créer le produit » (non cliqué) et
le produit `6574AXSH` n'est plus proposé. À l'étape 2, `6108AGACHM` et `6108AGABCHM` affichent
« Produit Odoo trouvé (eurocode) ». Étape 3, avec écriture, non jouée.

1. Sur un devis lié à une opportunité, rechercher la base `6108A`, sélectionner un article dont la
   fiche suggère `6108AXSR` « GEL CAPTEUR SILICONE », puis sélectionner cette suggestion (cas observé
   le 2026-10-05). Si VSF ne la suggère plus (constaté à la recette du 2026-10-05), sélectionner la
   ligne principale `6108AXSR` : mêmes attendus.
   - Attendu : « Article absent de la base Odoo », avec « Créer le produit », et **plus**
     « Produit Odoo trouvé (nom) » vers le produit de code `6574AXSH`, qui porte le même nom mais
     est le gel d'un autre article.
2. Sélectionner un article dont le produit Odoo existe à son eurocode.
   - Attendu : « Produit Odoo trouvé (eurocode) », avec « Voir le produit ».
3. Avec écriture, sur le devis de recette de CRM-07 : « Créer le produit » pour `6108AXSR`.
   - Attendu : un nouveau produit portant l'eurocode `6108AXSR` est créé, retrouvé ensuite par
     « eurocode » ; le produit `6574AXSH` n'est ni réutilisé ni modifié. Lister l'écriture.

### SO-08 — Retirer du devis (lot correctif du 2026-10-06, R28)

Scénario du build `17.0.261006.1`. Il n'enregistre rien : « Ajouter au devis » et « Retirer du
devis » ne modifient que le formulaire ouvert, dont on abandonne les modifications à la fin
(« Ignorer les modifications »). Relever par RPC `write_date` et les lignes du devis avant et après :
elles doivent rester inchangées. Depuis le lot E2, le devis s'ouvre sans X'Glass et ne prend donc pas
le verrou technique `rpbm_agent.session_lock` (relevé inchangé) ; avant, la seule écriture tolérée
était ce verrou, vide en fin de recette.

**Recette réussie le 2026-10-06**, en `17.0.261006.1` (commit `44b86e0`), sans aucune écriture : étapes
1 à 3 et 6. Après « Ajouter au devis », les actions affichent « Retirer du devis », jamais « Article
déjà présent dans le devis. » ; après « Retirer du devis », « Ajouter au devis » revient, sans
« Retirer du devis » ni « Article déjà présent ». Les relevés en lecture seule avant et après ne
montrent rien de créé ni de modifié sur le devis, son opportunité et le véhicule lié, et le verrou est
vide. Étapes 4 et 5 non exécutées (facultatives). Deux points ne s'observent pas dans ce protocole :
la quantité et le prix de la ligne ajoutée (sans enregistrer ; la preuve vient d'une ligne de la
recette d'E1, enregistrée, qui porte la quantité 1 et un prix unitaire égal au prix X'Glass × 1,5) et
le maintien des autres lignes (le devis de la recette n'en avait aucune).

Dossier : un devis brouillon lié à une opportunité, sans aucune ligne du produit testé, dont la base
mémorisée est `6574A`. Article : `6574AGACIMVZ`, dont le produit Odoo existe déjà (rien à créer).

Défaut d'origine (recette d'E1, 2026-10-05) : après « Ajouter au devis », la ligne était bien ajoutée,
avec sa quantité et son prix, mais « Retirer du devis » ne s'affichait pas et l'article montrait
« Article déjà présent dans le devis. ».

1. Ouvrir la fenêtre, chercher la base `6574A` (la recherche part seule à l'ouverture depuis le lot
   E2, sans X'Glass ; au build `17.0.261006.1`, seulement si une pièce était retrouvée, sinon par
   « Rechercher sur VSF »), puis sélectionner la ligne `6574AGACIMVZ`.
   - Attendu : « Voir le produit » (le produit existe) et « Ajouter au devis » ; ni « Retirer du
     devis », ni « Article déjà présent dans le devis. ».
2. Cliquer sur « Ajouter au devis ».
   - Attendu : **« Retirer du devis » remplace « Ajouter au devis »** ; « Article déjà présent dans le
     devis. » n'apparaît pas. Une ligne de ce produit est ajoutée au formulaire du devis ; sa quantité
     (1) et son prix ne s'observent pas sans enregistrer.
3. Cliquer sur « Retirer du devis ».
   - Attendu : la ligne ajoutée disparaît, et elle seule : les autres lignes du devis (manuelles,
     main-d'œuvre, autres articles) restent en place ; « Ajouter au devis » revient. Ajouter puis
     retirer une seconde fois : la bonne ligne à chaque fois, sans ligne résiduelle.
4. Si un second article de la liste a lui aussi un produit Odoo : ajouter les deux articles, puis en
   retirer un.
   - Attendu : la ligne de l'autre article reste, avec « Retirer du devis ».
5. Règle inchangée : on ne retire que ce que le widget a ajouté pendant la fenêtre ouverte. Ajouter
   de nouveau l'article, fermer par **Annuler** sans enregistrer le formulaire, rouvrir la fenêtre sur
   le même devis (la ligne est encore dans le formulaire), puis sélectionner l'article.
   - Attendu : « Article déjà présent dans le devis. », sans « Retirer du devis » ; la ligne se
     supprime dans la liste native du devis.
6. Abandonner les modifications du formulaire (« Ignorer les modifications »), puis relever
   `write_date` et les lignes du devis.
   - Attendu : identiques au relevé de départ.

La main-d'œuvre n'est pas concernée : son « Retirer » repose sur la clé de provenance de la ligne
(SO-04).

### SO-09 — Base sans résultat (lot correctif du 2026-10-06, R24)

Scénario du build `17.0.261006.1`, sans écriture enregistrée (même protocole que SO-08). Il **envoie
volontairement** des valeurs au portail VSF : une valeur saisie dans le champ « Base Eurocode » du
devis part au portail dès la validation du champ, y compris par la simple perte de focus de la
fenêtre.

**Recette réussie le 2026-10-06**, en `17.0.261006.1` (commit `44b86e0`), sans aucune écriture :
étape 1 jouée avec `9999Z`, qui affiche « Aucun article VSF pour « 9999Z ». », sans tableau, sans
notification d'erreur et sans erreur de console. Étapes 2 à 5 non exécutées (facultatives).

Défaut d'origine (recette R13 à R17, 2026-10-05) : toute base sans résultat, même au bon format,
affichait « Recherche impossible : le portail VSF est inaccessible. ». VSF répondait pourtant par une
page normale, « Aucun résultat ne correspond à votre recherche. ».

1. Dans la section VSF du devis, saisir `9999Z` (bon format, aucune base de ce nom) puis valider le
   champ (Tab ou clic ailleurs). Depuis le lot E2, la recherche part seule à la validation, sans
   X'Glass ; au build `17.0.261006.1`, seulement avec une pièce ou une pièce après-marché sélectionnée,
   sinon par « Rechercher sur VSF ».
   - Attendu : aucun tableau, et la section affiche « Aucun article VSF pour « 9999Z ». » ;
     **aucune notification d'erreur** (ni « portail VSF inaccessible », ni autre) ; une seule requête
     `/searchBaseEurocode`, qui répond par une liste vide.
2. Même contrôle avec `61-08A` (mal formée) puis `A+B &C D` (caractères à encoder).
   - Attendu : même résultat ; le message cite la valeur saisie.
3. Cliquer sur « Rechercher sur VSF » sans changer la valeur.
   - Attendu : une nouvelle recherche part, car aucun résultat n'est affiché (règle du 2026-09-20 :
     une même base n'est écartée que si ses résultats sont déjà affichés), et le même message revient.
4. Saisir une base à résultats (`6574A`).
   - Attendu : le message disparaît dès le départ de la recherche et le tableau se remplit.
5. Sur l'opportunité (lot E1), saisir `9999Z` puis valider.
   - Attendu : aucune requête VSF et aucun message : l'opportunité ne cherche plus sur VSF.

Si la session VSF expire pendant la recherche (R23), la reconnexion et le rejeu ont lieu côté serveur
depuis le lot E2 : le navigateur ne voit qu'une requête `/searchBaseEurocode`. Au build
`17.0.261006.1`, le widget se reconnectait et rejouait la requête une seule fois : deux requêtes pour
une saisie, avec le même résultat, n'étaient pas un double déclenchement ; c'est ce rejeu qui échouait
avec le message trompeur avant le lot correctif.

Hors protocole, car non rejouable à la demande en live : « Recherche impossible : le portail VSF est
inaccessible. » reste affiché pour une vraie panne (réseau, réponse HTTP inattendue) et pour une page
de résultats inattendue, ni liste d'articles ni message « aucun résultat » : le message exact de
l'erreur figure alors dans le journal serveur. Une session VSF expirée se reconnecte seule dans le
serveur (une fois) ; si cette reconnexion échoue (identifiants refusés), l'utilisateur voit « Connexion
au portail VSF impossible. Vérifiez les identifiants configurés. », sans reconnexion X'Glass. La page « aucun résultat » et la page inattendue sont couvertes hors réseau par
`test_portal_auth.py`.

### SO-10 — VSF d'abord, X'Glass à la demande (lot E2)

Scénario du build `17.0.261006.2`, **recette à faire**. Étapes 1 à 5 : sans écriture enregistrée (même protocole que SO-08, formulaire abandonné à la fin) ; étape 6 : avec écriture, sur l'opportunité de recette de CRM-07.

Dossier : un devis brouillon lié à une opportunité qui a une base mémorisée (`6574A`), un véhicule, une catégorie et une pièce mémorisés, sans ligne. Relever par RPC, avant et après : `rpbm_agent.session_lock`, `rpbm_xglass_vehicle_id`, `write_date` et les lignes du devis.

1. **Ouverture.** Ouvrir la fenêtre par la loupe, journal réseau ouvert.
   - Attendu : **aucun** `/rpbm_agent_auth` ; un `/searchBaseEurocode` sur `6574A`, et le tableau s'affiche, sans attendre X'Glass ; l'encart « Dossier » en lecture seule (véhicule, catégorie, pièce concernée, pièce X'Glass, article principal ; « — » pour une valeur absente) ; **ni** « 1. Véhicule », ni sections 2 et 3, ni « 4. Main d'œuvre » ; « Confirmer » actif ; le verrou inchangé.
2. **Sélection.** Sélectionner `6574AGACIMVZ` et le définir comme article principal (sans « Créer le produit » ni « Ajouter au devis »).
   - Attendu : sélection, détail et actions comme dans la recette du tableau VSF.
3. **« Charger X'Glass ».** Cliquer sur le bouton.
   - Attendu : un `/rpbm_agent_auth`, puis la chaîne X'Glass (véhicule mémorisé, planche, catégorie, pièces), **sans nouvelle recherche VSF** ; l'encart disparaît ; « 1. Véhicule », les sections 2 et 3 et « 4. Main d'œuvre X'Glass » apparaissent ; **le tableau, la sélection et l'article principal sont conservés** ; la pièce concernée affiche la valeur enregistrée, non remplacée par la suggestion du calque. Un double clic sur le bouton ne fait qu'une authentification (il est désactivé pendant le chargement).
4. **Fermeture avec X'Glass.** « Annuler ».
   - Attendu : un `/rpbm_agent_close`, verrou libéré ; abandonner les modifications du formulaire (« Ignorer les modifications ») : formulaire propre.
5. **Fermeture sans X'Glass.** Rouvrir la fenêtre, puis la fermer aussitôt par « Annuler ».
   - Attendu : **aucun** `/rpbm_agent_close` ; verrou inchangé.
6. **Avec écriture.** Sur l'opportunité de recette de CRM-07, « Créer un devis ».
   - Attendu : la fenêtre du devis s'ouvre aussitôt, sans seconde authentification, avec le libellé de la pièce dans l'encart ; « Confirmer » sans « Charger X'Glass » n'écrit que la base et l'article principal (relever : `rpbm_xglass_vehicle_id`, identifiants de pièce, véhicule et catégorie inchangés) ; abandonner le devis, sans l'enregistrer ; lister toutes les écritures (opportunité, verrou).
7. **Facultatives.**
   - Devis sans base ni pièce enregistrées (dossier avec seulement une catégorie, ou presque vide) : saisir une base, choisir un article principal, puis « Charger X'Glass » : la base, le tableau, la sélection et l'article principal survivent à la restauration automatique de la catégorie ; en revanche, cliquer ensuite sur une **autre** catégorie vide la base et le tableau, comme avant.
   - Fermeture pendant « Charger X'Glass » : cliquer sur le bouton puis fermer aussitôt par « Annuler ». Attendu : quand la réponse de `/rpbm_agent_auth` arrive, un `/rpbm_agent_close` part (verrou libéré, session X'Glass fermée), sans autre appel (fenêtre de temps étroite, à jouer sur un réseau lent).
   - Base sans résultat (`9999Z`) puis « Charger X'Glass » : aucune seconde recherche, le message reste ; « Rechercher sur VSF » la relance (R24).
   - Deux vendeurs en même temps : les deux ouvrent un devis et voient leur tableau VSF, sans message de verrou. Si le premier a chargé X'Glass, « Charger X'Glass » du second affiche « actuellement utilisé par … » dans l'encart, et son tableau reste ; le bouton sert alors de « Réessayer ».
   - Après un arrêt du processus (environ 2 minutes sans requête), la première recherche VSF se reconnecte seule : aucune erreur visible, une seule requête côté navigateur.
   - Dans les journaux, compter les connexions VSF et les reconnexions, pour les confronter aux traces T1 et T2 ([backend](technique/backend.md#état-de-session-partagée)).

Non rejouable à la demande : des identifiants VSF refusés donnent « Connexion au portail VSF impossible. Vérifiez les identifiants configurés. » sans reconnexion X'Glass (couvert hors réseau) ; « Annuler » d'un vendeur dont le verrou a expiré (15 minutes de travail VSF seul) ne déconnecte pas la session X'Glass d'un autre vendeur qui a repris le verrou ; deux vendeurs qui créent le même article en même temps ne produisent pas de doublon de produit (recherche d'existence par un curseur neuf après le verrou par code).

## Tableau VSF en plein écran (R21, R22, reprise de R15 à R17)

Recette sans écriture du tableau VSF en plein écran (build `17.0.261005.2`) : **recette réussie le
2026-10-05 sur le build `6cbecd3`**, sans écriture métier. Rejouée sur un devis, sans écriture, le
2026-10-06 sur le build `44b86e0` (`17.0.261006.1`), comme non-régression du lot correctif : réussie.
Les vérifications qui restaient à faire à la main (clic milieu sur « Ouvrir dans un nouvel onglet » et
sur une vignette, étapes 8 et 9 ; clic simple sur « Fiche technique », étape 9 ; affichage de la
recherche VSF après connexion, étape 8) ont été faites par l'utilisateur le 2026-10-06 : vérifiées à
la main, sans écart signalé.
Elle remplace la recette R13 à R17 (cartes sur une colonne) : le tableau remplace R13 et R14, et R15
à R17 sont repris aux étapes 8 à 10. Depuis le lot E1 (`17.0.261005.3`), le tableau n'existe plus sur
l'opportunité : pour la rejouer, les étapes 2 à 11 se font sur un devis lié à une opportunité ; seules
l'étape 1 (plein écran) et l'étape 12 (non-régression) concernent aussi l'opportunité.

Lire d'abord la version du module par RPC. Ouvrir un dossier de test ayant une base Eurocode
mémorisée : un devis lié à une opportunité, sauf mention contraire. Ne pas confirmer le dialogue, créer un produit, définir un article principal ni ajouter de ligne ;
fermer par **Annuler**. Relever par RPC `write_date` et les champs `rpbm_*` avant et après sur le
dossier, son opportunité et le véhicule lié : toutes ces valeurs doivent rester inchangées (seule
écriture tolérée : le verrou technique `rpbm_agent.session_lock`, vide en fin de recette ; depuis le
lot E2, un devis ouvert sans « Charger X'Glass » ne le prend pas). Depuis le lot E2, le tableau s'affiche
à l'ouverture du devis : « Charger X'Glass » n'est nécessaire que pour les étapes 11 (main-d'œuvre) et 12.

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
   - Une valeur synthétique (`+`, `&`, espace) saisie dans le champ du devis part au portail dès la
     validation du champ (`change`), y compris par la simple perte de focus de la fenêtre. VSF
     répond « aucun résultat » (page 200 sans liste, trace du 2026-10-06) et, depuis le lot correctif
     `17.0.261006.1`, le widget affiche « Aucun article VSF pour « *base* ». » (recette réussie le
     2026-10-06, SO-09) ; avant ce lot, il affichait le message trompeur « portail VSF inaccessible »
     (R24). N'en saisir donc que volontairement : c'est le critère « base sans résultat » de SO-09. L'encodage du lien est couvert
     hors réseau (`test_widget_vsf.mjs`).
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
    - Sur le devis (SO-05) : après « Charger X'Glass » (lot E2), « 4. Main d'œuvre X'Glass » (avec
      une pièce sélectionnée) puis « 5. Article VSF », avec le tableau et ses lignes de détail ; avant
      « Charger X'Glass », seuls l'encart « Dossier » et « 5. Article VSF » sont affichés. « Retirer du devis » n'apparaît
      qu'après un ajout : il relève de SO-08 et de SO-03, hors de ce protocole.
    - Sur l'opportunité : « 4. Base Eurocode » sans tableau ni bouton « Rechercher sur VSF » ; le
      lien « Ouvrir dans un nouvel onglet » reste.
12. **Non-régression.** Rejouer CRM-03 et CRM-05 : base restaurée avec et sans pièce AM, aucune
    recherche automatique sur l'opportunité (sur le devis, la recherche part dès l'ouverture depuis le
    lot E2, avec ou sans pièce mémorisée), « Autres marques AM » chargé une seule fois par véhicule et
    famille, puis base remplie au clic ; sur le devis, après « Charger X'Glass ».

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
