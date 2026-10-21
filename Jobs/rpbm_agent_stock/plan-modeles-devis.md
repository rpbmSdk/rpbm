# Plan — modèles de devis, articles standards et tarif « Pose à domicile »

Date : 2026-09-29. Étape **3 bis** du [séquencement de déploiement](README.md#séquencement-complet).

> **2026-10-21 — option A retenue** : l'étape 3 bis passe par des kits vides ([§9](#9-kits-vides-option-a-retenue-le-2026-10-21),
> [`consumable_kits.py`](consumable_kits.py)) ; les articles génériques restent dans les modèles. Les §2 à §8
> (`sale_templates.py`) restent la trace de l'analyse ; ne pas lancer `sale_templates.py --commit`.

Relevés faits en lecture seule sur la préproduction (build 37939198, copie de la production au
2026-09-11, Odoo 17). Les mécanismes ont été relus dans le source Odoo 17 (`../odoo17/odoo/addons`,
chemins ci-dessous relatifs à ce dossier `addons`). Les chiffres sont à recompter sur la
production par le dry-run de l'étape 3 bis.

## 1. Pourquoi la confirmation échoue

Message remonté : « Il n'y a pas de prix fournisseur correspondant pour générer un bon d'achat
pour le produit [VITRAGE1] VITRAGE 1 ». Le devis en cause est très probablement SO7758 (essai du
2026-09-28, modèle « Pare Brise V », transporteur Galleria).

La chaîne :

1. `rpbm_agent` refuse de confirmer sans transporteur (`rpbm_agent/models/sale_order.py:133-143`),
   et la route du transporteur est injectée dans l'approvisionnement
   (`stock_delivery/models/sale_order.py:51-55`).
2. Seules les lignes consommables ou stockables dont la quantité est > 0 sont approvisionnées.
   Les services, les sections, les notes et les lignes à qté 0 sont ignorés
   (`sale_stock/models/sale_order_line.py:341-345`).
3. Les routes des transporteurs sont en make_to_order (Camion → Clients) ou en `mts_else_mto`, qui
   compare la quantité au `free_qty` de l'emplacement source (`stock/models/stock_rule.py:250-276`). Un consommable n'a
   jamais de quant (`stock/models/stock_move_line.py:684`) : il passe donc toujours en
   make_to_order, jusqu'à la règle *Acheter*, car tous les articles des modèles portent la
   route Buy.
4. Sans fournisseur valide, `_run_buy` lève l'erreur (`purchase_stock/models/stock_rule.py:66-76`).
   Les erreurs sont cumulées, une ligne par produit. Sur SO7758, le message complet devait donc
   citer aussi « Produits Connexes ». La confirmation est annulée en bloc : aucun transfert, aucun
   achat.

Avant, l'ancien transporteur « Free delivery charges », qui n'a pas de route, faisait passer ces
lignes par l'ancienne règle d'entrepôt, sans achat. C'est pour cela que SO7752 a encore été
confirmé le 2026-09-28.

**Une ligne bloque** si elle remplit trois conditions :

- elle est consommable ou stockable, avec une qté > 0 ;
- elle n'a aucun fournisseur valide, c'est-à-dire un `product.supplierinfo` dont le partenaire est
  actif, la société vide ou RPBM, et l'article vide ou celui de la ligne ;
- il n'y a pas assez de `free_qty` à la source de chaque règle `mts_else_mto` traversée.

Changer le type de ces articles n'est pas possible : Odoo le refuse dès qu'il existe des lignes de
mouvement terminées ou réservées (`stock/models/product.py:911-923`). Par exemple, VITRAGE1 a 10
lignes terminées et 3 075 réservées. Retirer la route Buy ne règle rien non plus : l'erreur
devient « No rule has been found » (`stock/models/stock_rule.py:476-481`).

8 des 20 modèles actifs ne sont pas confirmables tels quels :

| Modèle (id) | Lignes bloquantes (qté 1) | Ventes confirmées sur 12 mois |
|---|---|---:|
| Pare Brise V (1) | VITRAGE1, Produits Connexes | 582 |
| Pare-Brise Hors Assurance (10) | VITRAGE1, Produits Connexes | 158 |
| Lunette Arrière (5) | LUNETTE V, Produits Connexes | 91 |
| Glace Mobile (7) | Produits Connexes | 59 |
| Glace Hors Assurance (12) | GLACE V, Produits Connexes | 46 |
| Glace Fixe (8) | Produits Connexes | 45 |
| Lunette Hors Assurance (11) | LUNETTE V, Produits Connexes | 41 |
| Pare-brise pose simple (13) | Film solaire bandeau (43) | 2 |

## 2. Retirer les articles génériques des modèles ? Oui

**Recommandation : supprimer des modèles actifs toutes les lignes d'articles génériques, puis
archiver ces articles.** Articles concernés :

- VITRAGE1 (13) et VITRAGE2 (47) ;
- LUNETTE V (31) et LUNETTE V CHAUFFANTE (30) ;
- GLACE V (50) ;
- PARE-BRISE V (49), PARE-BRISE V CAPTEUR PLUIE (14) et sa variante YC CAMERA (15) ;
- les 8 GLACE FIXE/MOBILE PORTE AVD/AVG/ARD/ARG (35 à 42) ;
- JOINT1 à JOINT4 (17, 27, 28, 26) et JOINT SUP PARE-BRISE (25) ;
- CALE PARE-BRISE (16) et AGRAPHES KIT (48, code réel « AGRPAHES »).

Pourquoi :

- **Les lignes en qté 1 bloquent la confirmation** (voir §1).
- **Elles font doublon avec le widget.** Le widget ajoute la vraie pièce VSF à côté du générique,
  sans retirer ce dernier (`rpbm_agent/static/src/agent_widget_dialog_sale_order.js:111-136`).
  C'est exactement le cas de SO7758, qui porte VITRAGE1 et deux pare-brise VSF.
- **Leur rôle passe au widget.** Ces articles servaient de ligne libre : le vendeur saisissait le
  prix à la main (VITRAGE1 : 719 € en moyenne sur 12 mois) et un libellé générique (« PARE-BRISE V »),
  quasiment jamais la référence de la pièce.
- **Les lignes à qté 0 sont des pièges.** Elles n'échouent pas à la confirmation, mais bloquent
  dès qu'un vendeur passe la qté à 1 sans changer d'article. Leur usage est faible, sauf JOINT1
  (14,7 % des ventes, utilisé comme fourre-tout joint ou enjoliveur).

Ordre à respecter : retirer les lignes **avant** d'archiver. Appliquer un modèle recopie le
produit même s'il est archivé (`sale_management/models/sale_order_template_line.py:107-113`).

On garde les sections (Pièces, Ingrédients, Kit Colle, Temps…) : elles servent de repères et
n'ont aucun effet. Seule la section « Pose à domicile » part, avec la ligne 46 (voir §4).

On ne touche pas aux modèles archivés (2, 3, 4, 6), qui ne sont plus proposés, ni aux modèles
« Upgraded Monthly/Yearly Subscription » (23, 24), vides et gérés par `sale_subscription`.

## 3. Articles standards

Part des ventes confirmées qui contiennent l'article en qté > 0 :

| Article (id) | Type | Prix HT | 12 mois | Historique | Effet à la confirmation |
|---|---|---:|---:|---:|---|
| Produits Connexes (20) | consommable, sans fournisseur | 9,00 | 85,6 % | 85,8 % | **bloque** |
| RETRAITEMENT DES DECHETS (29) | service | 9,00 | 84,4 % | 85,3 % | aucun |
| Frais d'identification (18) | service | 4,90 | 76,7 % | 78,8 % | aucun |
| Kit Collage Sika 400 ml (21) | stockable, 1 fournisseur | 59,00 | 75,7 % | 73,5 % | aucun (stock : 35 Galleria, 36 Genipa, 120 Dépôt 2) |
| T2 - Temps de MO 2 (23) | service | 90,32 | 74,8 % | 73,3 % | aucun |
| Nettoyage Bris de Glace (9) | service | 11,70 | 50,9 % | 47,8 % | aucun |
| Gel Capteur (19) | consommable, sans fournisseur | 25,00 | 29,0 % | 24,9 % | **bloque dès qté 1** |
| MO - Nettoyage Bris de Glace (44) | service | 78,00 | 20,6 % | 25,1 % | aucun |
| T1 - Temps de MO 1 (24) | service | 83,87 | 12,9 % | 14,6 % | aucun |

Les standards varient selon le modèle. Nettoyage Bris de Glace (9) figure dans 96 % des ventes
« Pare Brise V » et 0 % ailleurs. MO - Nettoyage Bris de Glace (44) figure dans 95 à 100 % des
ventes Lunette et Glace. Produits Connexes, Frais d'identification, Retraitement et Kit Collage
sont à 95-98 % dans les modèles sous assurance.

Ce qu'on en fait :

- **Services (18, 29, 9, 44, 23, 24) et Kit Collage (21)** : on les garde tels quels. Un service
  ne déclenche jamais d'achat. L'article 9 est aussi le `sale_timesheet.time_product` d'Odoo : il ne
  faut jamais l'archiver.
- **Produits Connexes (20)** : on crée un nouvel article de type service, au même nom, à 9,00 HT,
  avec la taxe 3 et un `default_code` distinct (proposition : `PC-FORFAIT`). On le substitue dans
  les modèles, puis on archive l'article 20. Lui ajouter un fournisseur serait absurde pour un
  forfait : chaque vente créerait une demande de prix et la livraison attendrait la réception.
- **Gel Capteur (19)** : par défaut, on retire la ligne des modèles (elle y est à qté 0) et on
  archive l'article. Le widget ajoute déjà le vrai gel VSF : 6574AXSH à 11,22 € sur SO7758, ou
  6570AXSH2. Garder un forfait à 25 € ferait facturer le gel deux fois. Si le client tient au
  forfait, on applique le même traitement que pour Produits Connexes.
- **Films solaires (43, 136, 137, 139, 140)** : consommables sans fournisseur, présents en qté 0
  dans 8 modèles et en qté 1 dans le modèle 13. Par défaut, on passe la ligne 43 du modèle 13 à
  qté 0. Le régime des films (service ou fournisseur) est à décider (§8, point 3).
- **T1/T2 dans les modèles** : aucune action. Dans les modèles actifs, ils sont à qté 0, sauf T1
  dans « FILM Sécuritaire » (25). Le widget ajoute la main-d'œuvre X'Glass avec sa durée réelle.

## 4. Tarif « Pose à domicile »

> Mise à jour du 2026-10-12 : 55,30 € HT est le prix de l'article 46 « Pose à Domicile » facturé par le client (72 lignes confirmées de 2022 à 2026, uniquement ce prix depuis 2023) ; c'est la valeur retenue par [P-19](../../docs/architecture/main-oeuvre-services.md#p-19--pose-à-domicile). Reste à trancher quand la facturer (Q-17).

**Prix relevé** sur l'ancien article « Pose à Domicile » (id 46, code « Pose Domicile ») :
**55,30 € HT, soit 60,00 € TTC** (taxe 3, TVA 8,5 %, non incluse dans le prix). Ce prix est
appliqué depuis le 2022-09-07. Avant, l'article était à 60,00 € HT (298 lignes en août-septembre
2022).

Sur l'historique, 85 ventes confirmées ont cette ligne en qté 1, et 80 d'entre elles l'ont
réellement facturée (5 remises à 100 %, 1 à 50 %). Répartition des prix : 55,30 × 72,
60,00 × 5, 27,65 × 4, plus 4 prix isolés.

À ne pas oublier : l'article « FRAIS DE DEPLACEMENT » (32), un service à **60,00 € HT**, a été
utilisé 6 fois, la dernière fois à 60,00. Le produit du transporteur Camion a été créé en
remplacement de « Frais de déplacement ». Le client doit confirmer lequel des deux prix vaut.

**Report sur le transporteur « Pose sur site (Camion) » — fait dans le dépôt.**
- `SERVICE_PRODUCTS` passe à `("Pose à domicile", 55.30)`
  ([`setup_stock_architecture.py`](setup_stock_architecture.py)). La valeur est appliquée au
  prochain `setup_stock_architecture.py carriers --commit`.
- Le `fixed_price` du transporteur est calculé et stocké à partir du `list_price` du produit 3414,
  avec un inverse (`delivery/models/delivery_carrier.py:281-290`). Il ne faut pas le régler à la
  main : `load()` réécrit le produit par son identifiant externe à chaque rejeu.
- L'unique liste de prix (« Public Pricelist ») est neutre, et 3414 porte la taxe 3. La ligne
  d'expédition vaudra donc 55,30 HT, soit 60,00 TTC (`delivery/models/delivery_carrier.py:292-303`,
  `delivery/models/sale_order.py:96-101`).
- On ne touche pas à « Retrait comptoir » (3413) : il est partagé par Galleria et Genipa, et reste à 0 €.

**Comment la ligne arrive sur le devis.**
- **Jamais automatiquement.** Le préremplissage du transporteur par `rpbm_agent` n'ajoute aucune
  ligne. Seul le bouton **« Ajouter l'expédition »** la crée (`delivery/wizard/choose_delivery_carrier.py:89-91`).
- **Le bouton est masqué quand toutes les lignes sont des services**
  (`delivery/models/sale_order.py:18-21`). C'est le cas des modèles 17 et 19, et du modèle 7 une
  fois nettoyé tant qu'aucune pièce n'est ajoutée. Il faut donc suivre cet ordre : le modèle,
  puis la pièce via le widget, puis « Ajouter l'expédition ». Pour un devis entièrement en
  services, on ajoute « Pose à domicile » (3414) comme ligne ordinaire.
- **Changer de transporteur ne met pas à jour la ligne d'expédition.** Exemple : on passe de
  Camion à Galleria, et la ligne à 55,30 reste. Le vendeur doit alors cliquer sur « Mettre à jour
  les frais d'expédition ».

**Ancien article 46.** On retire la ligne et sa section « Pose à domicile » des 7 modèles actifs
(1, 5, 7, 8, 10, 11, 12), où elle est à qté 0. Sinon, elle ferait doublon avec la ligne
d'expédition. On archive ensuite 46 et 32.

**Point à trancher avec le client.** Sur 12 mois, il y a eu 145 interventions à domicile (dont 86
« Pare Brise V » sous assurance), et la pose n'a été facturée que 3 fois. Facturer 55,30 € à
chaque intervention Camion serait donc un changement de tarif, pas une simple reprise de
l'existant (§8, point 4).

## 5. La même erreur hors des modèles

Nettoyer les modèles ne suffit pas.

- **92 pièces du catalogue importé le 2026-09-15 n'ont ni fournisseur ni stock.** 60 sont des
  pare-brise. Leur colonne `supplier` était vide ou valait « INVENTAIRE » dans
  `products_to_import.csv`. Quand le widget retrouve un article existant, il le renvoie tel quel,
  sans lui créer de prix fournisseur VSF (`rpbm_agent/controllers/main.py:669-677`). La vraie
  pièce reproduit donc la même erreur. Solution : leur créer le prix fournisseur VSF avec
  `product.template.sync_vsf_information()`, qui correspond au bouton « Synchroniser VSF » en mode
  développeur (voir le point d'attention au §7). Autre solution : une évolution de `rpbm_agent`
  qui appelle `_sync_vsf_supplierinfo` quand l'article existe déjà.
- **69 consommables vendables n'ont pas de fournisseur.** On y trouve des lignes financières ou
  libres (FRANCHISE 183, REMISE EXCEPTIONNELLE 177, VENTE DIVERS 156, DIFFERENCE EXPERTISE 152) et
  des pièces saisies en ligne libre (RETROVISEUR EXT D, VITRE LATERALE, OPTIQUE…). Ce qu'on en fait :
  - le « Forfait ADAS » (104, consommable) double le service « FORFAIT Réglage ADASS » (106), au même
    prix : on le remplace par 106 et on l'archive ;
  - les autres sont à trancher (§8, point 1).
- **Le transporteur « Free delivery charges » (id 1)** contourne toute l'architecture. On
  l'archive (c'est une donnée `noupdate`, donc l'archivage résiste aux mises à jour).

## 6. Devis ouverts

En préproduction, il y a environ 2 000 devis ouverts réels (brouillons et envoyés), **tous sans
transporteur**. 1 931 contiennent au moins une ligne bloquante, dont 111 de moins de 90 jours et
45 depuis le 2026-09-01. Aucun devis récent n'est bloqué uniquement par Produits Connexes ou Gel
Capteur.

- **Pas de correction automatique.** La pièce générique ne se remplace que par la vraie pièce, via
  le widget. Le rapport de l'étape 3 bis liste ces devis, avec leur âge et leurs produits fautifs.
- **Devis récents** : le vendeur les reprend. Il remplace les génériques et les forfaits,
  supprime la ligne 46 (présente dans 1 766 lignes de devis ouverts, dont 22 en qté > 0), choisit
  le transporteur puis ajoute l'expédition.
  - Il ne doit **pas réappliquer le modèle** : cela efface toutes les lignes, y compris celles du
    widget (`sale_management/models/sale_order.py:104-121`).
  - Il ne doit **pas dupliquer un devis antérieur à la bascule** : la copie reprend les articles
    archivés (`sale/models/sale_order.py:827-835`).
- **Devis anciens** : par défaut, on les laisse en l'état, car leur confirmation échoue
  proprement. Si le client préfère les annuler, on utilise l'action native de la liste, **Action >
  « Annuler les devis »**, qui traite les brouillons et les envoyés en masse
  (`sale/wizard/mass_cancel_orders.py:31-32`). Pour revenir en arrière, on utilise « Remettre en
  brouillon ». Aucun code n'est nécessaire.

## 7. Étapes à insérer dans le déploiement

L'étape 3 bis ne dépend pas de l'architecture stock. On la place **avant l'étape 4**. Ainsi, aucune
fenêtre ne s'ouvre pendant laquelle les modèles bloquent, et le dry-run de production est lu
avant de créer les transporteurs à route.

| # | Action | Outil | Vérification | Retour arrière |
|---|---|---|---|---|
| 3 bis | Kits vides sur les consommables sans fournisseur (§9, option A du 2026-10-21) | [`consumable_kits.py`](consumable_kits.py) `apply --perimetre utilises`, puis `archive` : dry-run, puis `--commit` | `consumable_kits.py check --perimetre utilises` PASS (code retour 0) | `consumable_kits.py rollback --run <run> --commit` |
| ~~3 bis~~ | ~~Modèles et articles (§2 à §4)~~ — abandonné le 2026-10-21 : ne jamais lancer `sale_templates.py --commit` | [`sale_templates.py`](sale_templates.py) | — | — |
| 3 bis (suite) | Prix fournisseur VSF des 92 pièces sans fournisseur | `sync_vsf_information()`, appelée par le script ou lot par lot | Le rapport du dry-run ne liste plus ces pièces | Aucun (historisation native des prix fournisseur) |
| 4 | Architecture, **tarif compris** | `setup_stock_architecture.py carriers --commit` | Étape 5 : `check_carriers` compare `fixed_price` à `SERVICE_PRODUCTS` (contrôle à ajouter) | Remettre la constante et rejouer |
| 4 ter | Archiver « Free delivery charges » | à la main dans Odoo | Seuls les 3 transporteurs RPBM sont proposés | Le désarchiver |
| 6 | Recette | à la main, voir ci-dessous | — | `rollback.py --run <run>` |

> Écrit le 2026-10-16 : [`sale_templates.py`](sale_templates.py) et `tests/test_sale_templates.py` (8 scénarios, reprise
> après coupure comprise). Le retrait des génériques s'applique par défaut (Q-03 tranchée le 2026-10-12) ; Produits
> Connexes, Gel Capteur, films et pose à domicile attendent `--decision` (§8, points 2 à 4). Le §5 (92 pièces sans
> fournisseur, consommables libres) reste hors du script. Dry-run du 2026-10-16 sur la préprod : 13 lignes bloquantes,
> 8 restantes sans décision, 0 avec les quatre décisions ; 1 919 devis ouverts concernés, dont 106 de moins de 90 jours.

**`sale_templates.py`** est le seul script à créer, sur le patron de
[`studio_views.py`](studio_views.py). Il a les sous-commandes `apply` et `rollback --run`, les
options `--profile`, `--url` et `--db`, et le garde-fou `--i-understand-this-is-production`. Il
applique les règles suivantes :

- **Données de référence** : chaque article est une constante (id attendu + `default_code` ou nom
  attendu), résolue avec `active_test=False`. Les ids de production sont les mêmes, puisque la
  préprod en est une copie. Toute correspondance absente ou ambiguë **arrête le script avant la
  première écriture**.
- **Portée** : les règles s'appliquent aux lignes de **tous** les modèles actifs, pas à une liste
  de noms. Le dry-run signale tout modèle actif absent de l'inventaire de préprod.
- **Sauvegarde** : `runs/<run>-modeles-devis/manifest.json` enregistre l'instantané complet
  **avant** la première écriture, puis chaque opération au fil de l'eau. Un `--run` déjà utilisé
  est refusé.
- **Archivage** : un article n'est archivé que si plus aucune ligne de modèle actif ne le
  référence. L'id 9 n'est jamais archivé.
- **Rollback** : il refuse d'agir si un modèle a changé depuis l'`apply`, et il archive les
  services créés.
- **Rapport** : `rapport.md` contient :
  - les lignes bloquantes (FAIL) ;
  - les lignes à qté 0 qui bloqueraient à qté > 0 (WARN) ;
  - les articles vendables sans fournisseur valide, avec leur usage sur 12 mois ;
  - les devis ouverts touchés.
- **Test hors ligne** : `tests/test_sale_templates.py`, avec un faux Odoo, vérifie trois choses :
  l'idempotence, le rollback, et l'arrêt sur clé ambiguë.

**Point d'attention sur `sync_vsf_information()`** : elle réécrit aussi la fiche article
(`rpbm_agent/models/product_template.py:96-97`). Il faut relire son effet sur 2 ou 3 articles en
préproduction avant de la lancer en masse.

**Recette en préproduction.** Chaque devis de recette porte la référence client
`ARCH1-AUDIT-<run>-TPL<id>-<GALL|CAM>`, que `rollback.py` sait retrouver.

- **Modèles** : pour chacun des 8 modèles du §1, appliquer le modèle, ajouter une pièce VSF via le
  widget, puis confirmer avec Galleria, puis avec Camion. Attendu : aucune erreur.
- **Pièce sans fournisseur** : ajouter via le widget une pièce du catalogue qui n'a pas de
  fournisseur. Attendu : la confirmation passe après le traitement du §5.
- **Tarif** : sur Camion, cliquer sur « Ajouter l'expédition ». Attendu : une ligne à 55,30 HT,
  soit 60,00 TTC. Passer ensuite à Galleria, puis cliquer sur « Mettre à jour les frais
  d'expédition ».
- **Modèle 7 sans pièce** : vérifier le repli par une ligne 3414 ordinaire.

**En production** :

1. Lancer `sale_templates.py apply --profile <prod> --url https://rpbm.odoo.com` en dry-run et lire
   le rapport. Les modèles ont pu changer depuis le 2026-09-11.
2. Relancer la même commande avec `--commit --i-understand-this-is-production`.
3. Enchaîner avec l'étape 4.

Les réponses du §8 sont un prérequis.

**Documentation à suivre.**
- Guide client : modifier les textes dans `documentation/generer_guide.py`, puis régénérer sur le
  poste Windows (les polices y sont codées en dur). Trois sujets :
  - le tarif de la pose à domicile ;
  - l'ordre « modèle → widget → Ajouter l'expédition » ;
  - la règle « ne pas réappliquer le modèle ni dupliquer un ancien devis ».
- Au même endroit, corriger la phrase « aucun blocage automatique des ventes sans transporteur »,
  que `sale_order.py:133-143` contredit.
- Reporter les réponses du §8 dans [`decisions.md`](../Gestion%20Stock/decisions.md) une fois
  qu'elles sont obtenues.

## 8. Décisions à faire valider par le client

Valeurs par défaut du plan entre parenthèses.

1. **Articles génériques et lignes libres.** La pièce passe exclusivement par le widget ou le
   catalogue, et les génériques du §2 sont retirés puis archivés (oui, JOINT1 compris). Que faire
   des consommables libres : FRANCHISE, REMISE, VENTE DIVERS, pièces diverses ? (Défaut : un
   service pour REMISE, FRANCHISE et VENTE DIVERS ; archivage des articles non vendus depuis 12 mois.)
2. **Produits Connexes.** Un forfait de type service ? (Oui.) **Gel Capteur** : le gel VSF réel
   remplace-t-il le forfait à 25 € ? (Oui.)
3. **Films solaires.** Un service, ou un article avec fournisseur commandé à chaque pose ? (Qté 0
   dans le modèle 13 en attendant.)
4. **Pose à domicile.** 55,30 € HT (article 46) ou 60,00 € HT (FRAIS DE DEPLACEMENT) ? Et faut-il
   la facturer à chaque intervention Camion, seulement hors assurance, ou au cas par cas ? (55,30 €,
   au cas par cas.)
5. **Ligne d'expédition.** Geste manuel « Ajouter l'expédition », ou ajout automatique par
   `rpbm_agent` quand le transporteur est Camion ? (Geste manuel.)
6. **Devis ouverts de plus de 90 jours.** Les laisser, ou les annuler en masse ? (Les laisser.)
7. **92 pièces sans fournisseur.** Les rattacher à VSF, y compris celles marquées « INVENTAIRE » ?
   (Oui, après relecture de l'effet de la synchronisation.)

## Reste à confirmer

- Le message complet de SO7758 : une capture montrerait si Produits Connexes y figurait aussi.
- Le contenu des modèles de production par rapport à la copie du 2026-09-11 (le dry-run le montre).
- Les joints du catalogue couvrent-ils l'usage « enjoliveur » de JOINT1 ?
- La vue devis modifiée par Studio en production affiche-t-elle bien « Ajouter l'expédition » ?

## 9. Kits vides (option A, retenue le 2026-10-21)

Décision de l'utilisateur du 2026-10-21. Chaque consommable vendable sans fournisseur reçoit une nomenclature `mrp.bom`
de type « Kit » (phantom), sans ligne, référence `RPBM-SANS-APPRO` : à la confirmation, Odoo remplace son besoin par
celui de ses composants (`mrp/models/stock_rule.py:254-284`), donc aucun achat, aucune erreur « pas de prix
fournisseur ». Donnée standard, aucun code ; l'article garde son type et reste dans les modèles de devis.

Appliqué en préprod le 2026-10-21 : 51 kits (25 consommables des modèles actifs + 26 encore utilisés, run
`runs/20261021-kits-utilises-consommables/`), 18 consommables sans usage archivés (`runs/20261021-archive-18-consommables/`),
`check --perimetre utilises` PASS. En parallèle, `setup_stock_architecture.py picking_types` fixe la séquence des
réceptions (D2/IN proposé par défaut aux achats) et passe les commandes d'achat ouvertes vers une vue sur D2/IN.

Effets connus :

- les lignes de ces articles n'apparaissent plus sur les bons de livraison et leur quantité livrée reste à 0 (la
  facturation sur quantités commandées n'est pas touchée) ;
- rejouer `consumable_kits.py check --perimetre utilises` après tout ajout d'article : un nouveau consommable sans
  fournisseur ni kit bloque de nouveau la confirmation ;
- si un fournisseur est ajouté un jour à l'un de ces articles, supprimer son kit en même temps (sinon sa réception
  d'achat est explosée en rien) ;
- hors cible : les stockables sans fournisseur (un kit casserait leur suivi de stock) ; leur donner un fournisseur.
