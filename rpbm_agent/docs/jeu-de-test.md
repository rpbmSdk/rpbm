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
5. vérifier ou saisir la base `6539R` ;
6. sélectionner l'article `6539RGSH5RD` ;
7. utiliser **Confirmer**, puis enregistrer le formulaire nativement.

Résultats attendus :

- le véhicule Fleet est créé ou retrouvé puis lié par `rpbm_vehicle_id` ;
- la catégorie X'Glass et la pièce concernée sont visibles ;
- la base Eurocode est `6539R` ;
- l'article sélectionné est mémorisé sans modifier de prix ;
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
- `6539R` reste restaurée même sans article VSF sélectionné ;
- les résultats VSF peuvent être relancés sans repartir d'un état incohérent.

### CRM-04 — Recherche vide et saisie manuelle

Avec la plaque synthétique `ZZ-TEST-00`, vérifier le comportement d'une
recherche sans résultat. Puis utiliser une plaque de test retournant au moins
un véhicule et saisir manuellement `6539R` sans sélectionner de pièce AM.

Résultats attendus : la recherche vide affiche une information exploitable,
ne crée aucun véhicule et ne lève pas d'exception non gérée. La base saisie
manuellement permet néanmoins de rechercher les articles VSF.

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
- un clic n'importe où sur une ligne la met en évidence, remplit la base (`6108A`) et lance la
  recherche VSF ;
- une famille sans entrée affiche « Aucune autre référence après-marché. », sans erreur.

### CRM-06 — Groupage et Autres AM par famille (lot D, build A)

Scénario de recette du build `17.0.261005.1`. **Non exécuté** : les résultats attendus
ci-dessous viennent du plan du 2026-10-05 et des qualifications du 2026-10-01 ; aucun n'est
une observation sur le build cible. Protocole sans écriture : ne pas confirmer, créer de
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
   - Attendu : ligne mise en évidence, base `6108A`, section « Article VSF » visible, une
     seule recherche VSF lancée.
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
     « Rechercher sur VSF » la lance ; « Afficher les autres » affiche les cartes.

Dernier contrôle hors protocole : lire dans les logs serveur Odoo.sh les lignes `INFO` par
famille (clés, drapeaux, nombre de pièces) pour tracer les calques et familles non encore
observés ; elles ne contiennent aucune donnée client.

Contrôles hors réseau avant tout push, depuis la racine du dépôt :
`node rpbm_agent/test_widget_vsf.mjs` ([script](../test_widget_vsf.mjs)),
`python rpbm_agent/test_portal_auth.py` ([script](../test_portal_auth.py), qui contrôle aussi
que chacun des deux XPath du devis cible un seul nœud), rendu Owl local des trois modes
(focalisé, tout, restauré sans pièce) et `git diff --check`. La recette R13 à R17 plus bas reste valable pour le build A ; elle
sera remplacée au build B (tableau VSF).

## Scénarios devis

### SO-01 — Devis avec opportunité

Créer un devis lié à une opportunité de test issue de CRM-01. Rejouer la
recherche `DS808DZ`, sélectionner `PARE-BRISE`, puis l'article
`6539RGSH5RD`.

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

Sur un devis lié à une opportunité (même protocole sans écriture que CRM-06, **non exécuté**) :

1. Sélectionner une pièce : les sections « 4. Main d'œuvre » et « 5. Article VSF » sont
   toutes deux présentes, dans cet ordre.
2. Rouvrir sans pièce, déplier un encart « Autres marques AM » et cliquer sur une ligne :
   « 5. Article VSF » apparaît, la recherche VSF se lance, « 4. Main d'œuvre » reste absente
   (elle suit la pièce sélectionnée ; la numérotation saute de 3 à 5, constat déjà présent pour
   une base restaurée seule).
3. Aucune action de devis (ajout, retrait) n'est exécutée.

## Présentation VSF — recette sans écriture (R13 à R17)

Ouvrir un dossier de test ayant une base Eurocode mémorisée. Ne pas confirmer le dialogue,
créer un produit, définir un article principal ni ajouter de ligne ; fermer par **Annuler**.
Relever par RPC `write_date` et les champs `rpbm_*` avant et après sur le dossier, son
opportunité et le véhicule lié : toutes ces valeurs doivent rester inchangées.

1. Rechercher `6108A` puis `6574A` : une seule colonne de cartes, y compris à grande largeur.
   Le titre est la désignation seule ; « Eurocode : … » est en chasse fixe, immédiatement
   au-dessus de la référence constructeur. Comparer des codes de longueurs différentes.
2. Sélectionner un article avec suggestions : celles-ci sont aussi sur une colonne et
   reprennent la même présentation, avec leurs actions dans leur propre carte.
3. Modifier la base sans lancer la recherche : le lien **Ouvrir dans un nouvel onglet**
   suit la valeur saisie, également par Ctrl+clic ou clic central avant validation du champ.
   Vérifier l'encodage avec une valeur synthétique contenant `+`, `&` et un espace, sans
   envoyer cette valeur au portail. La saisie ne lance pas un RPC par caractère.
4. Vider le champ, puis saisir uniquement des espaces : le lien est désactivé au clavier
   comme à la souris. Renseigner une base valide : il redevient utilisable.
5. Ouvrir une base valide dans le nouvel onglet : VSF affiche la recherche, après connexion
   si nécessaire ; le contexte du widget reste disponible dans l'onglet d'origine.
6. Rejouer CRM-03 et CRM-05 : base restaurée avec et sans pièce AM, aucune recherche
   automatique sans pièce mémorisée, « Autres marques AM » chargé une seule fois par
   véhicule et famille, puis base remplie au clic.
7. Dès les résultats, ouvrir une vignette : clic simple = aperçu interne ; tout clic modifié
   garde le comportement natif sans sélectionner la carte. Vérifier en particulier Ctrl/Cmd-clic
   et clic central, qui ouvrent l'image VSF signée dans un nouvel onglet.
   Dans l'aperçu, vérifier ←/→, le rebouclage après la dernière et avant la première image, et
   l'absence des photos du modèle de véhicule.

Les références de dossiers et les preuves live restent dans le document de travail local.
Ces critères ne constituent pas une recette réussie avant leur exécution sur le build cible : la
recette live R16/R17 reste ouverte. Le contrôle hors réseau de la saisie, du lien, de l'aperçu
et de la priorité de restauration se lance
depuis la racine du dépôt : `node rpbm_agent/test_widget_vsf.mjs`
([script](../test_widget_vsf.mjs)).

## Scénarios de robustesse

| ID | Précondition | Action | Résultat attendu |
|---|---|---|---|
| ROB-01 | Deux véhicules candidats | Changer rapidement de véhicule | Une seule planche et une seule métadonnée correspondent au véhicule finalement sélectionné |
| ROB-02 | Session X'Glass expirée | Déclencher une recherche ou une sélection | Reconnexion proposée, contexte conservé, action rejouée au plus une fois. Après reconnexion, mêmes pièces AM qu'avant (GS600HH, pièce `G27006RA3E` : aucune « Équivalence AM », 13 « Autres marques AM » avec validité) |
| ROB-03 | VIN Fleet déjà renseigné | Confirmer avec une valeur X'Glass différente | Le VIN Fleet valide n'est pas écrasé |
| ROB-04 | VIN Fleet de forme `var = <VIN>;` | Confirmer avec une valeur X'Glass valide | Le VIN malformé est nettoyé et remplacé par le VIN valide |
| ROB-05 | Article sans image ou stock | Sélectionner l'article | La carte reste utilisable, sans erreur JavaScript |
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
