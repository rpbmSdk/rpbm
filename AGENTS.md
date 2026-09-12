# Instructions Agents

Ce projet utilise des agents IA. Avant toute modification, inspecter le contexte existant et privilegier les changements minimaux.

## Regles de travail

- Ne pas supprimer les changements utilisateur non demandes.
- Documenter en francais lorsque le contenu est destine au repo.
- Verifier les commandes pertinentes avant de terminer une tache.
- Garder les outils et scripts simples, explicites et reproductibles.

## Delegation par defaut

Pour toute tache non triviale, deleguer les sous-taches independantes puis
attendre leurs resultats avant la synthese ou toute modification sur un meme
perimetre :

- `rpbm_product_owner_luna` : qualification fonctionnelle, audit en lecture
  seule et criteres de recette ;
- `rpbm_luna_codeur` : implementation d'un lot de fichiers explicitement
  attribue ;
- `rpbm_verificateur_computer_use` : recette independante et preuve visuelle
  sur l'environnement autorise.

Le pilote conserve la coordination et attribue une responsabilite exclusive a
chaque agent qui ecrit. Ne jamais faire modifier les memes fichiers par deux
agents en parallele. Pour une tache simple ou inseparable, le pilote peut
travailler seul et indique brievement pourquoi.

Lorsqu'un verificateur constate un build ou une recette en echec, le pilote
transmet son analyse factuelle a `rpbm_luna_codeur` pour un correctif cible.
Apres le correctif, le pilote relance le build puis confie de nouveau la
verification au verificateur. Cette boucle se poursuit jusqu'a une preuve de
recette ou a un blocage externe documente.

## Structure recommandee

- `docs/`: documentation permanente.
- `skills/`: skills reutilisables.
- `tools/`: outils locaux ou distribuables.
- `profiles/`: profils de configuration.
- `templates/`: fichiers generes par la toolbox.

## Audit Odoo Studio

- Lorsqu'un `.paradigme.yaml` est present, charger la skill `paradigme-mcp-local` avant tout appel Odoo. Ce fichier reste local, ignore par Git et ne contient aucun secret.
- Avant d'analyser une personnalisation Odoo, consulter l'[audit Studio](.paradigme/audits/README.md). Distinguer les faits observes des interpretations et hypotheses.
- Le snapshot `data/` d'un audit est local et ignore par Git. Ne jamais y ajouter de secrets ou de donnees metier non necessaires.
