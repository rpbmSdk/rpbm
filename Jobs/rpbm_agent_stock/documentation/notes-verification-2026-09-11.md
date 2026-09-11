# Vérifications du guide client - 11 septembre 2026

## Périmètre et sources

- Dépôt inspecté avant modification : `08b6b1d6fc441bad0205b4b4b460226d78564183`.
- Profil choisi par le [fichier projet local](../../../.paradigme.yaml) : `rpbm-preprod`.
- Le profil global emploie l'alias stable `rpbm-pre-prod.odoo.com`, base `rpbm-pre-prod-37860002`. Pour ces appels, l'URL est explicitement remplacée en mémoire par l'URL de branche demandée par l'utilisateur : `https://rpbm-pre-prod-37860002.dev.odoo.com/`. Aucune configuration globale ni aucun secret n'a été modifié.
- Transport XML-RPC à travers le serveur Paradigme MCP, enveloppes `tools/call` ; pas d'appels directs XML-RPC par les scripts documentaires.
- [Index d'audit Studio](../../../.paradigme/audits/README.md) consulté : il indiquait une structure initialisée sans acquisition complète. Une acquisition ciblée des vues de vente et métadonnées stock a été effectuée pour cette tâche ; ce n'est pas un audit Studio exhaustif.
- Sources locales brutes : `.paradigme/audits/rpbm-preprod/data/documentation-2026-09-11/`, ignorées par Git. Les paramètres de connexion des portails n'ont été recherchés que par leurs noms, jamais par leurs valeurs.

## Configuration observée

- Module `rpbm_agent` installé, id 1551, version `17.0.260730.6`.
- Un entrepôt RPBM, emplacement principal `RPBM/Stock` id 1778.
- Trois routes métier (10, 11, 12), six règles métier ; achat natif id 6 orienté vers Stock et type de réception Dépôt 2 id 39.
- 34 types d'opération de l'architecture présents, sur 39 types actifs lus au total.
- Une règle de rangement : Stock vers Dépôt 2. Aucun rack de réception imposé : conforme à l'amendement du compte rendu du 11/09.
- Quatre modes d'expédition actifs lus : les trois nouveaux et le mode historique gratuit, sans route associée.
- 179 emplacements enfants directs du Dépôt 1, 255 du Dépôt 2. **Deux fiches partagent le chemin `RPBM/Stock/Dépôts/Dépôt 1/R101`**, ids 1374 et 1375. Aucun déplacement ou fusion de ces fiches n'a été tenté. Le guide demande de lever l'ambiguïté avant l'inventaire initial.

Le contrôle structurel existant a été rejoué via [l'adaptateur MCP](verify_via_mcp.py). Résultat : **53 entrées, 50 PASS, 2 OBSERVED, 1 NOT_RUN, 0 FAIL, 0 WARN**. Voir le [journal complet](controle-structurel-2026-09-11.txt). L'essai non joué porte sur la réception directe au comptoir et le transfert devenu inutile. Le journal hérité suggère T2/F4, mais le script `verify_flows.py` actuel n'implémente que T1 et T3 : ne pas exécuter ces noms comme s'ils étaient disponibles.

Limite du contrôle structurel existant : il vérifie principalement présence, sélection des routes et méthodes d'approvisionnement. Il ne prouve pas toutes les destinations, tous les droits, toutes les réservations ni l'exécution physique des flux. Le rapprochement des emplacements et le doublon R101 sont des observations complémentaires.

## Interprétation du dernier commit

Le [compte rendu](../runs/2026-09-11-module-et-architecture.md) contient des étapes historiques suivies d'amendements en début de fichier. Les compléments 0.c et 0.d font foi pour l'import et la recette, malgré le paragraphe final conservé qui les décrit comme hors du périmètre initial.

- Catalogue rapporté : 3 229 produits nets, 15 catégories, 30 fournisseurs, 3 137 tarifs ; 43 références douteuses exclues. Ces volumes ne sont pas recomptés en direct dans cette tâche.
- T1 a vérifié la génération d'un document de livraison Galleria à partir d'un article présent au comptoir. Le script ne prouve pas à lui seul toutes les lignes réservées.
- T3 a vérifié la création d'un achat ; le rapport décrit aussi la chaîne GALL/OUT, DEP-GALL et destination D2/IN. Les données ont été nettoyées lors du lancement précédent : preuve historique du rapport, pas documents encore visibles pendant cette tâche.
- Le manque de transporteur avait provoqué le repli sur le circuit natif de Galleria lors des premiers essais. Cette observation motive l'affichage visible du champ et la consigne vendeur.
- Aucun mouvement physique n'avait été validé dans ces essais. Ne pas présenter les 53 contrôles comme 53 scénarios de bout en bout.

## Visibilité du transporteur : correctif appliqué

### Diagnostic observé

Le champ `carrier_id` est absent des architectures des vues formulaire de vente actives acquises avant correction. La vue livraison standard fournit notamment le bouton d'assistant d'expédition, conditionné par les lignes du devis. La vue Studio id 4858 réorganise fortement le formulaire et supprime l'adresse de livraison, mais **aucune instruction masquant directement `carrier_id` n'a été trouvée**. Une suppression historique par Studio reste une hypothèse non démontrée.

### Modification

Création via MCP d'une seule vue complémentaire :

- id **7905**, nom `sale.order.form.rpbm.transporteur.visible` ;
- hérite de la vue de vente 1118, priorité 100, après la personnalisation Studio 99 ;
- ajoute `carrier_id` sous le client, libellé **Transporteur / mode de remise** ;
- empêche la création rapide d'un transporteur depuis ce champ ;
- rend le champ non modifiable sur les ventes confirmées/annulées ou verrouillées ;
- ne rend pas la saisie obligatoire et ne modifie pas le calcul de frais de livraison ;
- ne modifie ni la vue Studio ni les routes ni les ventes existantes.

Source reproductible : [XML](transporteur_visible.xml), [script](restore_carrier_view.py). Sauvegarde avant : `carrier_view_before.json` (liste vide : la vue n'existait pas). Relecture après : `carrier_view_after.json`. Le premier contrôle textuel a signalé un écart dû à la normalisation des espaces XML par Odoo ; la structure, les attributs et le contenu ont été vérifiés, puis le script a été corrigé pour comparer le XML structurellement. Il ne s'agissait pas d'un échec de création.

Cette vue est une personnalisation de préproduction indépendante du module. Elle est à reprendre explicitement dans le déploiement de production, après inspection des vues de cette cible. Une reconstruction de branche peut la faire disparaître. Le script documentaire reste volontairement borné à la base de cette édition.

### Vérification dans Chrome

- Nouveau devis sans opportunité : champ transporteur visible, onglet X'Glass absent conformément au module.
- Devis de démonstration lié à une opportunité : champ visible, onglet X'Glass présent.
- Liste visible : Frais de livraison gratuit ; Retrait / pose Galleria ; Retrait / pose Genipa ; Pose sur site (Camion).
- Sélection Galleria enregistrée dans Chrome ; relecture MCP : `carrier_id = 3`, `state = draft`, `picking_ids = []`.

## Jeu de démonstration et widget

Créations dédiées à cette documentation : opportunité **12628**, nom `DEMO-DOC-RPBM-20260911`, et devis **7755**, numéro **SO7756**, même référence client. Partenaire interne RPBM id 1 utilisé. Ces deux documents sont **conservés pour revue**, le devis reste brouillon sans ligne ni mouvement. Aucun achat, aucune confirmation de vente, aucune réception ni livraison physique n'a été réalisé dans cette tâche.

Le bouton Assistant véhicule est visible sur le devis lié. Lors de l'essai, l'ouverture est restée sur « Authentification des agents en cours... » pendant plusieurs minutes ; la fenêtre a ensuite été fermée par sa croix. Les noms `XGLASS_USER`, `XGLASS_PASS`, `VSF_LOGIN`, `VSF_PASSWORD` n'ont pas été retrouvés parmi les paramètres système lus. Aucun accès portail n'a été copié ni configuré ; la reprise des identifiants du fichier local a été proposée à l'utilisateur et n'a pas reçu de réponse explicite au moment de cette édition.

**Fait :** ouverture du bouton observée, aucun résultat véhicule ou article obtenu. **Interprétation :** les accès absents sont un prérequis manquant, mais ils ne prouvent pas à eux seuls la cause de l'attente prolongée. **Non testé :** connexion effective, recherche véhicule, choix de pièce, recherche VSF, ajout/retrait de ligne et confirmation du widget. Le guide distingue ces limites de son mode opératoire, établi à partir des sources du module.

Une erreur client transitoire a également été rencontrée en passant par la recherche de menus Odoo ; le rechargement de la liste a permis la navigation. Elle n'a pas été attribuée au module ni corrigée sans diagnostic.

## Contrôle documentaire

Le [générateur](generer_guide.py) produit le PDF et le texte Markdown hors ligne. Les captures originales sont conservées ; le PDF les cadre sur les éléments utiles sans falsifier leur contenu. Les 14 pages ont été rendues et inspectées visuellement ; pagination, tableaux, schémas et lisibilité des captures vérifiés. Les liens ajoutés dans les index sont contrôlés par existence de fichier.

Les fichiers utilisateur non suivis présents avant la tâche ont été conservés. Aucune mise à jour des mémoires, aucun commit ni push n'a été effectué.
