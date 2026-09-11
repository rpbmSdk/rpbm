# Migration stock RPBM vers Odoo

Migration du suivi de stock tenu dans Google Sheets (`Gestion Stock V4 - Stock Complet.csv`, export
du 29/01/2025) vers Odoo 17.

Cible : `rpbm-preprod` (`https://rpbm-pre-prod.odoo.com/`) — accès **exclusivement** via la skill
`paradigme-mcp`, profil `rpbm-preprod`. Aucun secret dans ce dossier.
Environnement Python : `pyenv 3.10.11` (fixé par `.python-version` à la racine du dépôt).

## État au 2026-08-06

**Le catalogue est importé en préproduction** : 15 catégories, 30 fournisseurs, 3 229 articles,
3 137 tarifs fournisseurs et leurs coûts, sans aucun échec de chargement. `rpbm_agent` a été
installé au préalable — il était en réalité *désinstallé* sur l'instance, ce que le garde-fou de la
phase produits a détecté avant toute écriture.

Deux blocages subsistent :

- **Entrepôts et emplacements** (P2, P3) : volontairement non lancés, car créer les 5 entrepôts
  trancherait Q1 de fait. Voir [questions-ouvertes.md](questions-ouvertes.md#q1). *(2026-08-06 : la
  sous-question déterminante — un fournisseur peut-il livrer au comptoir ? — est répondue « oui »
  sans faire basculer la recommandation ; voir
  [architectures-stock.md § I](architectures-stock.md#i--arbitrage-du-2026-08-06).)*
- **Stock initial** : l'inventaire corrigé du 30/06/2026 n'a pas été fourni (Q2).

Détail phase par phase et relevés d'exécution dans
[plan-import-articles.md](plan-import-articles.md) § Suivi.

## Où trouver quoi

| Document | Contenu |
|---|---|
| [decisions.md](decisions.md) | **Les décisions arrêtées.** Source unique, ne plus reposer au client. |
| [questions-ouvertes.md](questions-ouvertes.md) | **Ce qui reste à trancher**, avec l'option par défaut de chacune. |
| [architectures-stock.md](architectures-stock.md) | **Définition comparée des trois architectures** (Q1) : flux métier, diagrammes, routes et règles de chaque implémentation, configuration des profils Comptoir / Dépôt / Camion, et l'arbitrage du 2026-08-06 sur la livraison fournisseur au comptoir. |
| [Réponses_rpbm.md](Réponses_rpbm.md) | Journal des réponses du client, verbatim et daté. |
| [plan-import-articles.md](plan-import-articles.md) | Le plan d'exécution phase par phase (P0 → P8), commandes, contrôles, reprise. |
| [data_quality_report.md](data_quality_report.md) | Volumes, anomalies et contrôles sur les données source. |
| [architectures/](architectures/) | **Configuration cible détaillée**, un document par architecture : tous les enregistrements et leurs champs, plus un diagramme de séquence par flux. [00-invariants.md](architectures/00-invariants.md) fixe ce qui ne dépend pas de l'architecture — référentiel des 31 types d'opération, transporteurs, périmètre de réservation. |
| [architectures/audits/](architectures/audits/) | **Procédure d'audit réplicable** des implémentations, registre de données de recette, matrice architecture 1 et modèles de rapports persistants. |
| [routes_transferts_entrepots.md](routes_transferts_entrepots.md) | Recherche Odoo sur les routes et transferts — matière pour Q1. |
| [procédure actuelle stock.md](procédure%20actuelle%20stock.md) | Le fonctionnement historique, tel que décrit par les utilisateurs. |
| [infos.md](infos.md) | Cadrage initial : correspondances de catégories, dépôts, inventaire. |
| [archive/](archive/) | Documentation superseded, conservée pour l'historique. |

Analyse de la coexistence avec le module `rpbm_agent` :
[docs/cartographie/reconciliation-stock-rpbm-agent.md](../../docs/cartographie/reconciliation-stock-rpbm-agent.md).

Tâches GRH de rattachement : 1263 (gestion de stock), 1269 (valorisation), 2079 (inventaire juin
2026), 251 (mise à jour des statistiques).

## Outillage

```
pyenv exec python prepare_migration_files.py          # CSV source -> fichiers de préparation
pyenv exec python prepare_migration_files.py --check  # vérifications hors ligne du mapping
pyenv exec python import_odoo.py selfcheck            # vérifie la logique d'import sans réseau
pyenv exec python import_odoo.py <phase> [--commit]   # une phase à la fois
```

**Sans `--commit`, rien n'est écrit dans Odoo.** Les identifiants sont lus depuis
`~/.paradigme/.env`, jamais depuis le dépôt.

Fichiers de préparation produits par `prepare_migration_files.py` :

| Fichier | Contenu |
|---|---|
| [categories_mapping.csv](categories_mapping.csv) | 31 valeurs `TYPE` source → catégorie et sous-catégorie cible |
| [categories_odoo_proposition.csv](categories_odoo_proposition.csv) | Catégories Odoo à créer ou réutiliser — fait foi pour les libellés |
| [locations_mapping.csv](locations_mapping.csv) | 568 valeurs `PLACE` source, avec statut de rapprochement |
| [suppliers_mapping.csv](suppliers_mapping.csv) | 55 valeurs `FRS` source → 30 partenaires Odoo |
| [products_to_import.csv](products_to_import.csv) | Catalogue dédoublonné par eurocode normalisé |
| [stock_initial_to_import.csv](stock_initial_to_import.csv) | Modèle **volontairement vide** — voir Q2 |

## Structure du CSV source

Le fichier n'est pas exploitable avec sa première ligne comme en-tête : les lignes 1 à 4 sont des
informations de synthèse, la ligne 5 porte les en-têtes, les données commencent ligne 6.

| Colonne | Sens | Cible Odoo |
|---|---|---|
| `EUROCODE` | référence article principale | `default_code` et `x_studio_eurocode` |
| `TYPE` | famille article | `product.category` (via mapping, jamais tel quel) |
| `DESIGNATION` | libellé article | `name`, repli sur l'eurocode |
| `FRS` | fournisseur ou origine | `res.partner` du `product.supplierinfo` |
| `PRIX ACHAT` | coût d'achat | `product.supplierinfo.price` |
| `PRIX RV` | coût retenu | `standard_price` (D6) |
| `PRIX BRUT` | prix catalogue | `list_price` (voir Q3) |
| `PLACE` | emplacement physique | `stock.location` |
| `QTE Act` | quantité actuelle | stock initial — **non repris**, voir Q2 |
| `VALEUR`, `VALEUR (Av Fret)`, `FRET` | montants de ligne | contrôle de valorisation uniquement |
| `AUTRE CODE`, `EUROCODE INTERNE`, `INV *`, `NB Sort`, `DATE *` | historique | **non repris** (D4) |

Relations vérifiées sur les lignes à quantité positive : `VALEUR (Av Fret)` ≈ `QTE Act × PRIX ACHAT`
(760 lignes sur 768) et `VALEUR` ≈ `QTE Act × PRIX RV` (761 sur 768). Aucune des deux ne doit servir
de coût unitaire.

## Inventaire de référence

| Indicateur | Montant |
|---|---:|
| Stock théorique au 30/06/2026 | 106 745,23 € |
| Stock réel inventorié | 100 297,05 € |
| **Écart à arbitrer** | **6 448,18 €** |

## Risques principaux

- Données source non fiables depuis 2023, et postérieures de 17 mois à l'inventaire de référence.
- Statuts vendu/réservé/cassé portés par des couleurs Google Sheets, **perdues à l'export CSV**.
- Doublons d'eurocode à interpréter comme quantités ou historique, non comme produits distincts.
- Blocage définitif de la synchronisation VSF (`UserError`) sur tout produit portant plus d'une ligne
  `product.supplierinfo` active pour le partenaire VSF — d'où la règle `date_start` (D9).
- Catalogue migré non synchronisable si `x_studio_eurocode` n'est pas renseigné à l'import.
- Création de produits en doublon si le rapprochement par `default_code` n'est pas fait avant
  écriture — `product_reconciliation.csv` est obsolète et doit être régénéré (P0).
- Seuls 8 % des unités en stock sont aujourd'hui réservables par une commande client, à cause du
  `lot_stock_id` de l'entrepôt `RPBM` — correctif décrit dans
  [questions-ouvertes.md](questions-ouvertes.md#q1).
