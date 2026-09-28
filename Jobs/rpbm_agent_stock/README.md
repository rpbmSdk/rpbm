# Déploiement rpbm_agent + architecture stock — outillage rejouable

Scripts pour installer `rpbm_agent` et poser l'architecture stock 1 sur une instance Odoo
(préproduction aujourd'hui, production plus tard), avec vérification et rollback. Séparé de
[`Jobs/Gestion Stock/`](../Gestion%20Stock/README.md), qui reste l'historique de décision de la
migration catalogue et la spécification de l'architecture — ce dossier **implémente** cette
spécification, il ne la duplique pas.

Créé après un constat direct sur `rpbm-preprod` : un rebuild d'instance remet tout à zéro
(module absent de la liste des apps, champs Studio disparus, architecture stock à refaire) sans
qu'aucune trace dans le dépôt ne le signale à l'avance. L'objectif de ce dossier est que
« redéployer » redevienne une commande, pas une reconstitution manuelle.

## Séquencement complet

Pour la validation métier et la prise en main, voir le [guide client PDF, ses captures et les notes de vérification](documentation/README.md) (édition du 11 septembre 2026). Le transporteur a été rendu visible en préproduction ; la connexion aux portails du widget reste à configurer et tester dans cette édition.

```
1. install_module.py --commit                                   (ce dossier)
2. studio_views.py apply --commit                                (ce dossier, après install_module.py ou chaque
                                                                  mise à jour de rpbm_agent qui ajoute des champs natifs)
3. Jobs/Gestion Stock/import_odoo.py <phase> --commit            (catalogue articles, P1/P4-P8)
   (P2/P3 de ce script sont l'ancienne architecture 5-entrepôts, abandonnée — ne pas les lancer,
   voir questions-ouvertes.md Q1)
4. setup_stock_architecture.py <phase> --commit                  (ce dossier, phase par phase)
5. verify_structural.py                                          (ce dossier, lecture seule)
6. verify_flows.py --run <id> --tests ... --commit                (ce dossier, écrit des ventes de recette taguées)
7. rollback.py --run <id> [--commit]                              (ce dossier, quand la recette est terminée)
```

Chaque script est **dry-run par défaut** ; `--commit` est requis pour écrire. Lancer chaque étape
sans `--commit` d'abord, lire ce qu'elle ferait, puis rejouer avec `--commit`.

Cible résolue via `--profile <nom>` (défaut : lu depuis `.paradigme.yaml` à la racine du dépôt,
soit `rpbm-preprod` aujourd'hui) — jamais une URL codée en dur. C'est ce qui rend ce lot rejouable
en production plus tard : `--profile <profil-prod>` une fois ce profil déclaré dans
`~/.paradigme/paradigme_odoo_mcp.yaml`, sans toucher au code.

## Sécurité et prérequis

- Connexion résolue en appliquant littéralement `paradigme-mcp-local` puis `paradigme-mcp` :
  `.paradigme.yaml` → nom de profil, `~/.paradigme/paradigme_odoo_mcp.yaml` → métadonnées,
  `~/.paradigme/.env` → secrets (jamais dans ce dossier, jamais affichés). Voir
  [`common.py`](common.py) `load_profile()`.
- Ces scripts appellent des méthodes Odoo arbitraires (`button_immediate_install`,
  `update_list`, `action_confirm`...), hors du jeu d'outils exposé par le serveur MCP
  `paradigme-mcp` (limité à `model_search_read/write/create/unlink`) — XML-RPC direct est donc
  nécessaire, pas une préférence de style. Voir [`common.py`](common.py).
- Un helper généré pour une tâche ponctuelle va sous `.paradigme/scripts/` à la racine du dépôt
  (skill `paradigme-mcp-local`, jamais sous `~/.paradigme/`) — ces scripts-ci sont pérennes et
  versionnés, donc dans ce dossier directement, pas sous `.paradigme/`.
- Ces scripts lisent des secrets et écrivent sur le réseau : **hors mode auto**, une confirmation
  humaine est nécessaire à chaque exécution (le mode auto de Claude Code bloque ce type d'action
  par construction, quels que soient les réglages de permissions locaux).

## Détail par script

| Script | Écrit ? | Rôle |
|---|---|---|
| [`install_module.py`](install_module.py) | oui (`--commit`) | Rafraîchit la liste des apps si besoin, installe `rpbm_agent`. |
| [`setup_stock_architecture.py`](setup_stock_architecture.py) | oui (`--commit`) | Implémente [`../Gestion Stock/architectures/01-architecture-1-zones.md`](../Gestion%20Stock/architectures/01-architecture-1-zones.md) §2.1-2.7 (34 types d'opération, 3 routes, 6 règles, transporteurs). |
| [`verify_structural.py`](verify_structural.py) | **jamais** | Compare l'instance aux tables de `setup_stock_architecture.py` (source unique) — PASS/FAIL/WARN. |
| [`verify_flows.py`](verify_flows.py) | oui (`--commit`) | Recette T1-T8/MTO ([test-registry](../Gestion%20Stock/architectures/audits/architecture-1-test-registry.md)) — taggée `ARCH1-AUDIT-<run>-<scénario>`, jamais de validation physique. |
| [`rollback.py`](rollback.py) | oui (`--commit`) | Annule/supprime les enregistrements d'un run `verify_flows.py`, jamais rien d'autre. |
| [`studio_views.py`](studio_views.py) | oui (`--commit`) | `apply` : ajoute en fin des vues Studio le bouton « Assistant véhicule » (formulaires opportunité et devis), les champs natifs `rpbm_*` (formulaires opportunité, devis, facture) et le suffixe « (ancien) » des champs Studio doublés (+ `optional="hide"` dans les listes). Listes et recherches ne reçoivent que le suffixe : leurs colonnes et champs natifs viennent du module. `rollback --run <id>` : restaure les sauvegardes de ce run. |

`tests/` : vérifications hors ligne (aucun réseau) — logique de branchement d'`install_module.py`,
garde-fou anti-dérive comptant les tables de `setup_stock_architecture.py` contre la spec, et
idempotence/rollback de `studio_views.py`. À lancer avant tout `--commit` réel :

```
python tests/test_install_module.py
python tests/test_setup_stock_architecture.py
python tests/test_studio_views.py
```

## Vues Studio (`studio_views.py`)

Une vue du module ne doit pas viser un nœud créé par Studio : si la cible disparaît, le
formulaire ne s'ouvre plus. Ces ajouts passent donc par un script, qui écrit des blocs `<xpath>`
en fin d'arch de la vue Studio (résolue par la règle de `web_studio`, jamais par un id codé en dur).

- **Idempotent, patch par patch** : chaque ajout a un contrôle qui vérifie l'effet à sa place dans
  l'arch combinée ; seuls les blocs dont le contrôle échoue sont ajoutés. Un deuxième `apply`
  répond « rien à faire ». Un nœud `rpbm_*` déplacé dans Studio n'est pas rajouté.
- **Vues ignorées** tant que les champs natifs manquent (modèle ou colonnes/recherches du
  module) : mettre `rpbm_agent` à jour d'abord.
- **Vérification intégrée** (`--commit`) : contrôles rejoués et ouverture en mode Studio strict ;
  en cas d'échec, la sauvegarde est restaurée automatiquement.
- **Sauvegardes** dans `runs/<run>-studio-views/` : arch avant écriture, sha256 avant/après,
  `manifest.json`, `rapport.md`. `rollback` ne restaure que si l'arch n'a pas bougé depuis l'apply ;
  sinon il refuse, et les ajouts se retirent à la main dans Studio.
- **Production** : `--url` (URL de l'instance, pas de build `.dev.odoo.com`) et
  `--i-understand-this-is-production` avec `--commit`.

Limites :

- **Fermer toute session Studio** avant `apply --commit` : un éditeur ouvert avant réécrit son
  instantané au prochain enregistrement et efface les ajouts (relancer `apply` pour le détecter).
- **Rejouer `apply` après chaque reconstruction** de l'instance : les vues Studio ne sont pas
  versionnées.
- **Lancer `rollback` avant de désinstaller `rpbm_agent` ou de renommer un champ `rpbm_*`** :
  la vue Studio référencerait sinon un champ inconnu.

## Rapports d'exécution (`runs/`)

Un rapport par exécution réelle (module, architecture, vérification ou rollback), versionné.
Reprendre le schéma de
[`../Gestion Stock/architectures/audits/runs/_template.md`](../Gestion%20Stock/architectures/audits/runs/_template.md)
(non dupliqué ici), en ajoutant pour ce lot : l'état du module avant/après, et l'identifiant de
run `verify_flows.py`/`rollback.py` le cas échéant.

## Ce que le rollback ne peut pas faire

Odoo n'autorise pas la suppression directe d'une vente/d'un achat/d'un transfert confirmé —
seule l'annulation l'est. `rollback.py` annule puis supprime ce qu'Odoo permet, et **rapporte
explicitement** ce qui reste (document annulé mais non supprimable, numéro de séquence déjà
consommé). Ce n'est pas une limite du script, c'est le comportement réel d'Odoo — ne jamais
essayer de forcer une suppression au-delà de ce que `unlink()` accepte.
