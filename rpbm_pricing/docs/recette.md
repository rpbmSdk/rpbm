# Recette sur Odoo.sh

[RPBM Pricing](../README.md) › [Documentation](README.md) › Recette

Recette de l'itération 1 (`17.0.261012.1`) sur un build de la branche `pre-prod`. Aucune installation locale
d'Odoo : les contrôles locaux se limitent à `python3 -I rpbm_pricing/tests/run_pure.py`, à la compilation et
à l'analyse des XML.

## 1. Installation

1. Ouvrir le build du commit cible (URL résolue par la skill `odoo-sh-build-connect`, jamais l'alias de
   branche).
2. *Applications › Mettre à jour la liste des applications*, puis installer « RPBM Pricing ».
3. Journal attendu :
   - `rpbm_pricing: N modèle(s) de devis classé(s) sur M sans régime` ;
   - `rpbm_pricing: garde de la règle 8 posée sur l'action 1510`, ou un avertissement « valeur inattendue »
     (la garde n'est alors pas posée : relire l'action avant tout).

La mise en place ne tourne qu'à l'installation (`post_init_hook`). Si le module est déjà installé et que la
garde manque, la poser par *Paramètres › Technique › Actions serveur › « RPBM : activer la garde de la
règle 8 » › Exécuter*.

## 2. Tests sous Odoo

Dans le webshell du build :

```sh
odoo-bin -u rpbm_pricing --test-enable --test-tags /rpbm_pricing --stop-after-init --http-port=8899 --max-cron-threads=0
```

- `--http-port=8899` : avec `--test-enable`, Odoo démarre le serveur HTTP même avec `--stop-after-init` ; il
  faut un port distinct de celui du build.
- Les tests tournent sur la base de préprod et sont annulés ; `-u` committe en revanche la mise à jour du
  module (idempotente).
- Ce qui exige un champ Studio ou l'automatisation réelle saute (`skipTest`) au lieu d'échouer ; les
  colisages de test sont datés 2099.

## 3. Recette non destructive

Par la skill `recette-odoo-jev`, comme pour `rpbm_agent` : un script joue chaque étape dans la page, Jev ne
décide qu'en secours, et le pilote ne fait que lancer, trancher les pauses et lire le rapport. Instance du
projet : `.paradigme/scripts/recette_rapide/` (non suivie). Opportunité et devis de test, abandonnés ou
annulés ensuite ; écritures limitées à `allowedWriteRecords`. Les valeurs qui ne se lisent pas à l'écran
(valeur de l'action 1510, colisages créés, coefficient annuel, demande de prix créée) sont relevées avant et
après par `snap.py`, en lecture seule.

Scénarios à écrire dans `scenarios/`, un par lot :

| Scénario | Lot | Écriture autorisée |
|---|---|---|
| `pricing_regime_bandeau` | Régime | aucune (devis modifié puis abandonné) |
| `pricing_regle8_garde` | Règle 8 | aucune (lignes saisies puis abandonnées) ; l'aller-retour « restaurer » / « activer » se fait hors scénario, relevé par `snap.py` |
| `pricing_fournisseur_vsf` | Fournisseur et mode | devis de test confirmé puis annulé, demande de prix créée puis annulée |
| `pricing_colisage_reprise` | Colisage | colisages 2025-2026 créés et factures rattachées (écriture réelle voulue) |
| `pricing_facture_bareme` | Facture | facture de test créée puis annulée |

| Lot | Scénario | Attendu |
|---|---|---|
| Régime | Devis « Pare-Brise Hors Assurance » sur un dossier avec assureur | Bandeau « Le modèle de devis est « Hors assurance », le dossier est « Assurance ». » ; régime du dossier affiché en lecture seule |
| Régime | *Ventes › Configuration › Modèles de devis*, colonne Régime | Modèles 1, 5, 7, 8, 19 en assurance ; 10, 11, 12 hors assurance ; les autres vides |
| Règle 8 | Ligne dont le Prix X'Glass est un Prix XGlass HT **relevé dans X'Glass et saisi à la main** (jamais une ligne posée par le widget actuel, qui écrit `prixVenteRPBM`) | Prix = barème × 1,5 à 4 décimales |
| Règle 8 | Quantité passée à 2 | Prix inchangé |
| Règle 8 | Ligne de main-d'œuvre (service) et kit de la catégorie 19 portant un barème | Prix non majoré |
| Règle 8 | Action 1510, puis « restaurer » et « activer » | Valeur = garde ; l'aller-retour restaure puis repose la garde |
| Fournisseur | Transporteur « Retrait / pose Galleria », article sans stock dont le client est aussi fournisseur | Demande de prix chez VSF, pas chez le client |
| Fournisseur | Même article en stock | Aucune demande de prix |
| Mode | Demande de prix VSF en brouillon passée en Bateau, puis nouveau besoin | Le brouillon bateau ne reçoit pas la ligne : une autre demande est créée |
| Colisage | *Achats › Colisages VSF › Reprendre l'historique*, deux fois | La seconde ne crée ni ne rattache rien ; liste des exceptions relue |
| Colisage | Avoirs VSF rattachés à la main, puis *Coefficient annuel* | 2025 ≈ 1,883 et 2026 ≈ 1,980 (classeur corrigé) ; un écart se documente avant de continuer |
| Facture | Devis de test avec le transporteur « Pose sur site (Camion) », pose ajoutée par « Ajouter l'expédition », puis facture | Barème sur la ligne produit de la facture (champ technique, sans vue) ; ligne « Pose à domicile » à 55,30 € HT, non majorée ; PDF sans prix net ni remise fournisseur |

La pose à domicile n'est jamais facturée par le seul choix du transporteur Camion : la ligne « Pose à domicile »
(55,30 € HT) n'apparaît que par le bouton « Ajouter l'expédition » du devis.

La reprise des colisages est une écriture réelle, voulue : elle crée les colisages 2025-2026 et rattache
leurs factures.

Voir aussi : [Paramètres](parametres.md) · recette détaillée de la [Règle 8](regle-8.md#recette) et du
[Colisage VSF](colisage.md#recette)

---
Précédent : [Colisage VSF](colisage.md)
