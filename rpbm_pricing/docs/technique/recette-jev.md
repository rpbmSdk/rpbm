# Recette Jev

[RPBM Pricing](../../README.md) › [Documentation](../README.md) › [Manuel technique](README.md) › Recette Jev

Recette non destructive de l'itération 1 sur un build de la branche `pre-prod`. Elle se joue avec la skill
`recette-odoo-jev`, comme pour `rpbm_agent` : un script joue chaque étape dans la page, Jev ne décide qu'en
secours, et le pilote ne fait que lancer, trancher les pauses et lire le rapport. Instance du projet :
`.paradigme/scripts/recette_rapide/` (non suivie par Git).

Avant la recette : installer le module et lancer les [tests](tests.md) ([Installation](installation.md)).

## Principes

- Opportunité et devis de test, abandonnés ou annulés ensuite. Écritures limitées à `allowedWriteRecords`.
- Les valeurs qui ne se lisent pas à l'écran (valeur de l'action 1510, colisages créés, coefficient annuel,
  demande de prix créée) sont relevées avant et après par `snap.py`, en lecture seule.
- Une recette de règle 8 se fait sur un Prix XGlass HT **relevé dans X'Glass et saisi à la main**. Jusqu'à
  `rpbm_agent` `17.0.261013.1`, le widget écrivait `prixVenteRPBM` (VM-10) : une ligne qu'il posait ne prouvait
  rien sur la règle 8. Depuis `17.0.261015.1` (VD-08), il pose le Prix XGlass HT de la pièce d'origine dans la
  colonne native « Barème X'Glass HT ».
- La reprise des colisages est une écriture réelle voulue.

## Scénarios

Scénarios dans `.paradigme/scripts/recette_rapide/scenarios/` (local, non suivi par Git), un par lot. Le tableau en donne le contenu.

| Scénario | Lot | Écriture autorisée |
|---|---|---|
| `pricing_regime_bandeau` | Régime | aucune (devis modifié puis abandonné) |
| `pricing_regle8_garde` | Règle 8 | aucune (lignes saisies puis abandonnées) ; l'aller-retour « restaurer » / « activer » se fait hors scénario, relevé par `snap.py` |
| `pricing_fournisseur_vsf` | Fournisseur et mode | devis de test confirmé puis annulé, demande de prix créée puis annulée |
| `pricing_colisage_reprise` | Colisage | colisages 2025-2026 créés et factures rattachées (écriture réelle voulue) |
| `pricing_facture_bareme` | Facture | facture de test créée puis annulée |

| Lot | Étape | Attendu |
|---|---|---|
| Régime | devis « Pare-Brise Hors Assurance » sur un dossier avec assureur | bandeau « Le modèle de devis est « Hors assurance », le dossier est « Assurance ». » ; régime du dossier en lecture seule |
| Régime | *Ventes › Configuration › Modèles de devis*, colonne Régime | modèles 1, 5, 7, 8, 19 en assurance ; 10, 11, 12 hors assurance ; les autres vides |
| Règle 8 | Prix X'Glass saisi à la main | prix = barème × 1,5 à 4 décimales |
| Règle 8 | quantité passée à 2 | prix inchangé |
| Règle 8 | ligne de main-d'œuvre (service) et kit de la catégorie 19 portant un barème | prix non majoré |
| Règle 8 | action 1510, puis « restaurer » et « activer » | valeur = garde ; l'aller-retour restaure puis repose la garde |
| Fournisseur | transporteur « Retrait / pose Galleria », article sans stock dont le client est aussi fournisseur | demande de prix chez VSF, pas chez le client |
| Fournisseur | même article en stock | aucune demande de prix |
| Mode | demande de prix VSF en brouillon passée en Bateau, puis nouveau besoin | le brouillon bateau ne reçoit pas la ligne : une autre demande est créée |
| Colisage | *Achats › Colisages VSF › Reprendre l'historique*, deux fois | la seconde ne crée ni ne rattache rien ; exceptions relues |
| Colisage | avoirs VSF rattachés à la main, puis *Coefficient annuel* | 2025 ≈ 1,883 et 2026 ≈ 1,980 (classeur corrigé) ; un écart se documente avant de continuer |
| Facture | devis de test avec le transporteur « Pose sur site (Camion) », pose ajoutée par « Ajouter l'expédition », puis facture | barème sur la ligne produit de la facture (champ technique, sans vue) ; ligne « Pose à domicile » à 55,30 € HT, non majorée ; PDF sans prix net ni remise fournisseur |

La pose à domicile (55,30 € HT, article 3414) n'est jamais facturée par le seul choix du transporteur Camion :
la ligne n'apparaît que par le bouton « Ajouter l'expédition » du devis. Ce comportement relève de
`rpbm_agent`, pas du code de `rpbm_pricing` ; il est relevé ici parce que la recette de la facture le traverse.

## Résultats du 2026-10-13

Build `rpbm-pre-prod-39736343`, `rpbm_pricing` 17.0.261012.1 installé, `rpbm_agent` 17.0.261013.1.

| Point | Résultat |
|---|---|
| tests sous Odoo | 35 tests, 0 échec |
| garde de la règle 8 | posée sur l'action 1510 |
| modèles de devis classés | 1, 5, 7, 8, 19 en assurance ; 10, 11, 12 hors assurance |
| bandeau de divergence | observé |
| confirmation d'un devis avec Galleria | crée la demande de prix chez VSF |
| reprise des colisages | 97 colisages, 185 factures, 4 avoirs à rattacher à la main ; seconde reprise sans effet |
| coefficients annuels avant rattachement des avoirs | 2025 = 1,9027 ; 2026 = 1,9408 |
| pose à domicile | ajoutée seulement par « Ajouter l'expédition » avec « Pose sur site (Camion) » |

Les coefficients attendus du classeur corrigé (1,883 et 1,980) valent **après** rattachement des 4 avoirs. L'écart
actuel n'est pas une erreur. À relire après rattachement, puis à documenter s'il subsiste.

Voir aussi : [Colisage VSF](colisage.md) · [Garde de la règle 8](regle-8.md)

---
Précédent : [Tests](tests.md) · Suivant : [Conventions de développement](conventions.md)
