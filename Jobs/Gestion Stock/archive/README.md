# Archive — documentation superseded

Documents conservés pour l'historique du projet. **Ils ne font plus foi.** L'état courant est dans
[../decisions.md](../decisions.md), [../questions-ouvertes.md](../questions-ouvertes.md) et
[../plan-import-articles.md](../plan-import-articles.md).

| Fichier | Ce que c'était | Pourquoi archivé |
|---|---|---|
| [README-cadrage-2026-07.md](README-cadrage-2026-07.md) | Le README d'origine : cadrage, analyse du CSV, stratégie, risques, prochaines actions | Journal d'accrétion de 600 lignes où décisions prises, hypothèses abandonnées et chiffres faux (7 blocs de racks, `list_price` dans des champs d'audit) cohabitaient sans hiérarchie. Le contenu durable est repris dans le nouveau README, `decisions.md` et `plan-import-articles.md`. |
| [questions-import-articles-2026-07-30.md](questions-import-articles-2026-07-30.md) | Les 11 questions rédigées pour envoi à RPBM | Q1 à Q10 sont tranchées ; Q11 est reprise en Q1 de `questions-ouvertes.md`. Le document continuait de poser des questions déjà répondues. |
| [questions_rpbm-2026-07-23.md](questions_rpbm-2026-07-23.md) | Consolidation des questions par thème | Doublonnait le précédent avec un découpage différent — c'est cette duplication qui a produit les questions reposées. Ses thèmes jamais transmis au client (stock initial, statuts, droits, prix de vente) sont repris dans `questions-ouvertes.md`. |

Le fichier [../Réponses_rpbm.md](../Réponses_rpbm.md) n'est **pas** archivé : c'est le journal
verbatim et daté des réponses du client, qui reste la source des décisions consolidées.

## Scripts et données obsolètes *(archivés le 2026-08-05)*

| Fichier | Ce que c'était | Pourquoi archivé |
|---|---|---|
| `prepare_migration_files.ps1` | Générateur PowerShell d'origine des fichiers de préparation | Remplacé par `prepare_migration_files.py`. Produit des volumes divergents de ceux du pipeline Python — le lancer écraserait les CSV de préparation avec des données fausses. |
| `import_product.ipynb` | Notebook d'exploration du CSV, avec création de catégories et de produits | Écrit directement dans Odoo via l'ancien connecteur `agent`, sans dry-run ni identifiants externes : il créerait des doublons hors de tout mécanisme d'idempotence. Utile seulement comme référence sur les mappings de types. |
| `product_reconciliation.csv` | Rapprochement des références candidates avec les `default_code` Odoo (20/07/2026) | Issu du pipeline PowerShell, volumes incohérents avec le catalogue actuel. **À régénérer en phase P0** : sans rapprochement, l'import peut créer un doublon pour chaque référence déjà présente dans Odoo. `data_quality_report.md` signale son absence à chaque génération. |

`analyse_gestion_stock.ipynb` reste dans le dossier du projet : analyse locale du CSV, sans
connexion Odoo ni écriture.
