# Instructions Agents

Ce projet utilise des agents IA. Avant toute modification, inspecter le contexte existant et privilegier les changements minimaux.

## Regles de travail

- Ne pas supprimer les changements utilisateur non demandes.
- Documenter en francais lorsque le contenu est destine au repo.
- Verifier les commandes pertinentes avant de terminer une tache.
- Garder les outils et scripts simples, explicites et reproductibles.

## Structure recommandee

- `docs/`: documentation permanente.
- `skills/`: skills reutilisables.
- `agents/`: definitions et generateurs d'agents.
- `tools/`: outils locaux ou distribuables.
- `profiles/`: profils de configuration.
- `templates/`: fichiers generes par la toolbox.

## Audit Odoo Studio

- Lorsqu'un `.paradigme.yaml` est present, charger la skill `paradigme-mcp-local` avant tout appel Odoo. Ce fichier reste local, ignore par Git et ne contient aucun secret.
- Avant d'analyser une personnalisation Odoo, consulter l'[audit Studio](.paradigme/audits/README.md). Distinguer les faits observes des interpretations et hypotheses.
- Le snapshot `data/` d'un audit est local et ignore par Git. Ne jamais y ajouter de secrets ou de donnees metier non necessaires.
