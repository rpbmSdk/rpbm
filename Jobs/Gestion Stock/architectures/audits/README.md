# Audits des implémentations stock

Ce dossier contient la procédure réplicable de contrôle des configurations stock Odoo en
préproduction. Il ne remplace pas l'[audit Odoo Studio](../../../../.paradigme/audits/README.md) :
il vérifie l'implémentation opérationnelle des architectures stock, des routes et des flux.

## Documents

- [Procédure commune](procedure-audit-implementation.md) : sécurité, relevé, préparation, contrôles,
  recette et rapport.
- [Registre architecture 1](architecture-1-test-registry.md) : critères de sélection des articles,
  racks, quants et partenaires de test.
- [Matrice architecture 1](architecture-1-compliance-matrix.md) : cible vérifiable des emplacements,
  types, routes, règles et transporteurs.
- [Rapports d'exécution](runs/README.md) : conventions et modèle de rapport par instance.
- [Rapport préproduction du 2026-08-07](runs/rpbm-preprod-2026-08-07.md) : structure et recette
  exécutées, validation humaine finale des données persistantes requise.

## Règles d'utilisation

1. Lire la [procédure commune](procedure-audit-implementation.md) avant tout appel Odoo.
2. Utiliser exclusivement le profil de préproduction explicitement autorisé par le dossier audité.
3. Ne jamais déposer de secret, jeton ou donnée métier inutile dans ce dossier.
4. Conserver les données et mouvements de recette en préproduction : aucun `unlink`, aucune
   annulation automatique et aucune restauration implicite des quantités.
5. Enregistrer les IDs Odoo réels et les états observés dans un rapport daté sous `runs/`.

Les fichiers de ce dossier décrivent une procédure et des résultats ; ils ne constituent pas une
configuration Odoo exécutée par eux-mêmes.
