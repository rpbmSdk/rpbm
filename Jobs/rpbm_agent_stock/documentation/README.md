# Guide client : logistique et assistant véhicule

Édition du 11 septembre 2026, pour validation de l'organisation et prise en main.

- [Guide PDF destiné au client](Guide_client_RPBM_logistique_et_assistant.pdf) : 14 pages, schémas des sites et des circuits, captures cadrées, mode opératoire du widget et fiche de validation.
- [Texte du guide en Markdown](guide-client.md), généré en même temps que le PDF.
- [Notes de vérification et modification de la vue](notes-verification-2026-09-11.md).
- [Résultat brut du contrôle structurel](controle-structurel-2026-09-11.txt).
- [Captures originales](captures/) : transporteur, accès au widget, connexion en attente, emplacements.

## Régénération hors ligne

Le [générateur](generer_guide.py) porte le texte source et la mise en page. Il ne lit aucun secret et ne contacte aucun service. Il utilise les captures locales et les polices Arial de Windows.

```powershell
python -m venv .venv-doc
.venv-doc/Scripts/python -m pip install reportlab Pillow
.venv-doc/Scripts/python Jobs/rpbm_agent_stock/documentation/generer_guide.py
pdftoppm -r 100 -png Jobs/rpbm_agent_stock/documentation/Guide_client_RPBM_logistique_et_assistant.pdf tmp/pdfs/guide
```

Exécuter depuis la racine du dépôt. Contrôler les 14 pages rendues après toute modification ; les références de pages en couverture doivent suivre la pagination finale. Le fichier Markdown est une sortie, à ne pas modifier isolément.

## Lectures et correctif de préproduction

Les scripts suivants sont volontairement bornés au profil `rpbm-preprod` et à la base de branche utilisée pour cette édition. Ils passent par MCP, avec les secrets lus exclusivement dans le stockage local Paradigme. Le nom du profil seul n'est pas suffisant : l'URL et la base sont contrôlées.

```powershell
# Acquisition en lecture seule : métadonnées locales ignorées par Git.
python Jobs/rpbm_agent_stock/documentation/inspect_live.py

# Contrôle structurel existant, adapté au transport MCP en lecture seule.
python Jobs/rpbm_agent_stock/documentation/verify_via_mcp.py

# Aperçu du correctif de vue, sans écriture.
python Jobs/rpbm_agent_stock/documentation/restore_carrier_view.py
```

La [vue complémentaire](transporteur_visible.xml) est déjà appliquée sur la préproduction. Le [script de correctif](restore_carrier_view.py) n'écrit qu'avec `--commit`. Son mode `--restore --commit` désactive exclusivement cette vue complémentaire : il ne modifie ni la vue Studio ni les ventes. Ce retour arrière n'a pas été exécuté pendant la documentation. Les sauvegardes sont locales dans le dossier d'audit ignoré par Git.

Le [script de préparation de démonstration](prepare_demo.py) crée un dossier CRM et un devis sans ligne, sans les confirmer, uniquement avec `--commit` ; il refuse de recréer un dossier du même nom. Il n'est pas nécessaire pour régénérer le guide. Ses identifiants et son périmètre sont consignés dans les notes.

Pour une autre instance, notamment la production, préparer un déploiement explicite adapté au profil et aux vues réellement présentes ; ne pas supprimer les garde-fous de ces scripts pour les rejouer à l'aveugle.

## Sources du projet

- [Outillage d'installation et de configuration](../README.md).
- [Dernier compte rendu d'installation, import et essais T1/T3](../runs/2026-09-11-module-et-architecture.md).
- [Gestion Stock](../../Gestion%20Stock/README.md), [architecture 1](../../Gestion%20Stock/architectures/01-architecture-1-zones.md) et [décisions](../../Gestion%20Stock/decisions.md).
- [Guide fonctionnel existant du module](../../../rpbm_agent/docs/fonctionnel/parcours-utilisateur.md).

Le guide client distingue les faits vérifiés, les résultats historiques et les parcours à tester. Les accès X'Glass/VSF ont été configurés après la préparation de cette édition ; l'authentification et la recherche d'articles restent à valider en direct.
