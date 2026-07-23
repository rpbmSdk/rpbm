# État des lieux

Audit du module au 2026-07-02, basé sur une lecture intégrale du code (`controllers/`, `static/src/`), des notebooks et de l'historique git (70 commits depuis mars 2025). Périmètre : **constat**, pas de correctif — sert de base pour prioriser une prochaine passe.

## 1. Résumé exécutif

Le flux principal (recherche véhicule → catégorie → pièce → eurocode → article VSF → écriture Odoo) est **fonctionnellement complet et cohérent** sur les deux modèles porteurs (`crm.lead`, `sale.order`). Le développement a été itératif sur ~4 mois avec de nombreux refactorings frontend, ce qui a laissé une dette technique classique de ce mode de développement : code mort, petites duplications, incohérences de nommage. Rien de bloquant identifié sur le chemin nominal ; plusieurs points méritent encore attention (voir §3-6). Depuis cet audit initial : gestion d'erreurs typée + notifications utilisateur, verrou de concurrence entre utilisateurs, et champs Studio versionnés (`pre_init_hook`) ont été ajoutés — voir les annotations **corrigé**/**fait** dans les sections ci-dessous.

## 2. Fonctionnalités implémentées

| Fonctionnalité | Statut | Note |
|---|---|---|
| Recherche véhicule par immatriculation (X'Glass) | Complet | |
| Sélection parmi plusieurs véhicules candidats | Complet | Premier résultat auto-sélectionné |
| Détection véhicule déjà présent dans Odoo | Complet | Alerte si conducteur différent du client |
| Création véhicule Odoo (marque/modèle/carburant/image à la volée) | Complet | |
| Navigation catégories (calques) → pièces → pièces après-marché | Complet | Présélection auto si catégorie déjà connue |
| Déduction automatique de l'eurocode | Complet | 5 premiers caractères de la référence de la 1ʳᵉ pièce AM |
| Recherche VSF par eurocode | Complet | |
| Création article Odoo (`product.product` + prix fournisseur) | Complet | Uniquement sur Ordre de Vente |
| Ajout d'un article à la ligne de commande | Complet | Indépendant du bouton Confirm |
| Écriture véhicule/catégorie/eurocode sur Piste/Opportunité | Complet | |
| Retour d'erreur visible par l'utilisateur | **Corrigé** | Notifications + erreurs typées, voir §6 |
| Concurrence multi-utilisateur des sessions portails | **Corrigé** | Verrou de session, voir §3 |
| Sécurité fine (droits d'accès) | **Absent** | `auth='user'` uniquement, pas de `ir.model.access.csv` |

## 3. Cohérence technique — backend

- **État de session global partagé** (`controllers/main.py:19-20`) : `vsfAgent`/`xglassAgent` sont des instances au niveau module, réutilisées par tous les utilisateurs Odoo qui appellent les routes. Combiné à la contrainte X'Glass "un seul utilisateur actif par identifiant" (`controllers/Readme.md`), deux utilisateurs Odoo utilisant le widget simultanément partagent la même session portail. **Corrigé** : un verrou de session (`acquire_agent_lock`/`touch_agent_lock`/`release_agent_lock`, `main.py`) sérialise désormais des sessions widget complètes (de `/rpbm_agent_auth` à `/rpbm_agent_close`), avec expiration glissante de 15 min en filet de sécurité — voir [configuration](technique/configuration.md#concurrence--verrou-de-session).
- **Route mal nommée** : `/rbm_agent/getVehiculeMeta` (`main.py:57`) — coquille `rbm` au lieu de `rpbm`, seule route préfixée du module. Non corrigé (changer l'URL casserait la compatibilité sans mesure de migration).
- **Duplication `getPieceAm`** — **corrigé** : `main.py::getPieceAm` réutilise désormais `XGLASS.findSelectionsPiecesAmView()` au lieu de reconstruire l'appel HTTP.
- **`except` nu** dans `/rpbm_agent_auth` — **corrigé** : remplacé par `except XGlassError`/`except VSFError` typés, avec `_logger.exception` (trace complète) et `UserError` si les deux tentatives échouent.
- **Appel commenté cassé** : `# vsfAgent.close()` dans `/rpbm_agent_close` (`main.py:159`) — `VSFAgent` n'a toujours pas de méthode `close()` ; non ajouté (VSF ne partage pas la contrainte "un seul utilisateur actif par identifiant" de X'Glass, un logout explicite n'est pas nécessaire au même titre).
- **`getPieceData`/`getPiecesData`** (`xglass.py:421-462`) : deux implémentations quasi identiques (l'une orientée objets `XGlassPlanche`/`XGlassCalque`, l'autre orientée IDs bruts).
- **`requirements.txt` partiellement incohérent** avec les imports réels (`requests` absent, `python-dotenv` désormais actif) et avec `__manifest__.py` (voir [configuration](technique/configuration.md)).
- **Bloc `if __name__ == "__main__"`** de `xglass.py:486-501` obsolète : appelle `auth()` sans arguments alors que la méthode les exige désormais — lèverait un `TypeError`.
- **Valeurs de test hardcodées** en défaut de paramètres de méthodes "production" : `immatriculation="DS808DZ"`, `idVehicule='397899'` (`xglass.py`), `eurocode="6539RGSH5RD"` (`vsf.py`).
- **Absence de sécurité fine** : pas de `security/ir.model.access.csv` ni de groupe dédié — toutes les routes sont accessibles à n'importe quel utilisateur Odoo connecté.

## 4. Cohérence technique — frontend

- **Appels réseau dupliqués** : `getOdooVehicule` (et potentiellement `createVehicule`) sont appelés indépendamment par `AgentWidgetDialog` et par chaque `VehiculeComponent` affiché, sans partage d'état.
- **Double déclenchement de `getPieces()`** : le clic sur une `CalqueComponent` appelle `onClickCalque()` qui invoque directement `getPieces()` (`agent_widget_dialog.js:413-417`), alors que le `useEffect` sur `selectedCalque` (`agent_widget_dialog.js:106-113`) le refait automatiquement juste après.
- **Getter `baseEurocode` défini deux fois** dans `AgentWidgetDialog` (`agent_widget_dialog.js:404` et `:490`) — la seconde définition écrase silencieusement la première (valide en JS, source de confusion à la lecture).
- **Code mort après un `return`** : dans `getPieceAm()` (`agent_widget_dialog.js:459-476`), un bloc de log + recalcul de `baseEurocode` se trouve après `return res;`, donc jamais exécuté (logique de toute façon redondante avec le `useEffect` sur `selectedPieceAm`).
- **Bouton "Confirm" jamais désactivé** malgré un état `canConfim` calculé à chaque changement pertinent : `t-att-disabled="!state.canConfirm"` est commenté avec un `<!-- FIXME -->` explicite dans `agent_widget_dialog.xml:75`. L'utilisateur peut cliquer "Confirm" sans véhicule sélectionné.
- **Sélection visuelle des articles VSF non fonctionnelle** : `onClickArticleVsf(articleId)` (`agent_widget_dialog.js:514-517`) compare `article.id === articleId`, mais est appelé avec `articleVsf.code` (`agent_widget_dialog.xml:64`) alors que `VSFArticle` (`vsf.py`) **n'expose aucun champ `id`** — la comparaison échoue systématiquement, donc `selectedArticleVsf` n'est jamais renseigné et la mise en surbrillance (fond azur) au clic sur un article VSF ne s'active jamais. Sans conséquence sur la création/l'ajout au devis (qui utilisent les props de l'article directement), mais visuellement trompeur.
- **Bouton "Enlever" trompeur** (`agent_widget_dialog_sale_order.xml:18-20`) : affiché quand l'article est déjà dans le devis, mais son gestionnaire pointe vers `addToSaleOrder()`, qui ne fait qu'ajouter une nouvelle ligne — aucune logique de suppression n'existe.
- **Service `orm` importé et instancié mais jamais utilisé** (`agent_widget_dialog.js`, `utils.js`) : tous les échanges serveur passent par `rpc` vers des routes JSON custom.
- **Champs de classe redondants/incohérents** : `SaleOrder.categorieXglassField` (`agent_widget_dialog_sale_order.js:21`) redéfinit la même valeur héritée par défaut ; `SaleOrder.eurocodeField`/`get eurocode()` (lignes 22, 32-34) ne sont utilisés nulle part — l'écriture réelle passe par `baseEurocodeField`, hérité de `AbstractWidgetRecord`.
- **`baseEurocodeField` non surchargé par modèle** (`utils.js:26`, valeur par défaut `x_studio_base_eurocode`) : contrairement à `immatriculationField`, ce champ n'était pas redéfini dans `AgentWidgetDialogCrmLead`. Or `x_studio_base_eurocode` n'existe que sur `sale.order` (champ `related` vers `opportunity_id.x_studio_field_ORIyy`) — sur `crm.lead`, le vrai champ "Base Eurocode" s'appelle `x_studio_field_ORIyy`. Conséquence : l'écriture de l'eurocode échouait silencieusement quand le widget était placé sur une Piste/Opportunité (cf. [technique/champs/crm-lead.md](technique/champs/crm-lead.md#structure-des-3-champs-eurocode) pour le détail des 3 champs Eurocode existants sur `crm.lead`). **Corrigé** : `CrmLead` surcharge désormais `baseEurocodeField = 'x_studio_field_ORIyy'` (`agent_widget_dialog_crm_lead.js`).
- **Refactoring inachevé visible** : `AgentWidgetDialogCrmLead.onConfirm()` et `AgentWidgetDialogSaleOrder.onConfirm()` ne font qu'appeler `super.onConfirm()`, avec du code métier spécifique laissé en commentaire dans les deux fichiers.
- **Typos multiples** (non bloquantes, révélatrices d'un manque de relecture) : `canConfim` (état, pour "canConfirm"), `toogleLoading` (`utils.js`), `OrderlLines` (getter de `SaleOrder`).
- **Absence de nettoyage d'état à la fermeture** : `onDiscard()`/`onConfirm()` ferment la dialog sans réinitialiser `vehicules`/`pieces`/`articlesVsf` — sans impact tant que la dialog est détruite et recréée à chaque ouverture, mais aucun `onWillUnmount` explicite.

## 5. Cohérence métier

- **Remise RPBM hardcodée à 20 %** (`vsf.py:46-48`, `self.remiseRPBM = 0.2`) avec un `# TODO : recalculer le prix de vente avec la remise RPBM` laissé par le développeur — non configurable sans modifier le code.
- **`VSF_PARTNER_ID = 5708` hardcodé** (`main.py:14`) plutôt que configuré (paramètre système ou champ de configuration module).
- **Champs CRM historiques marqués `[Obsolète]`** plutôt que supprimés (`x_studio_field_KyCjB`, `x_studio_field_ZhaeY` — cf. [parcours utilisateur](fonctionnel/parcours-utilisateur.md)) : dette déjà identifiée et documentée par l'équipe elle-même, non résolue.
- **Contrainte de session mono-utilisateur du portail X'Glass** — **corrigé** : désormais gérée explicitement par un verrou applicatif (cf. §3) plutôt que subie ; RPBM ne disposant que d'un seul identifiant partagé X'Glass/VSF (confirmé), la solution retenue sérialise les utilisateurs (message "occupé par X") plutôt que d'isoler par utilisateur, ce qui ne résoudrait pas la contrainte portail elle-même.
- **Champs Studio non versionnés** — **corrigé** : les champs `x_studio_*` manquants sont désormais créés automatiquement par `pre_init_hook` (`hooks.py`), reproductible sur toute instance (voir [configuration](technique/configuration.md) et [technique/champs/](technique/champs/README.md)).

## 6. UI/UX

- **Aucune notification utilisateur en cas d'erreur** — **corrigé** : `runAsync()` (`utils.js`) affiche désormais une notification (service `notification` Odoo, type `danger`) en plus du `console.error`. Côté serveur, `/rpbm_agent_auth`, `/searchImmatriculation`, `/searchBaseEurocode`, `/getPieceAm` lèvent des exceptions typées (`XGlassError`/`VSFError`) converties en `UserError` explicite au lieu d'avaler silencieusement vers `[]`/`False` — voir [configuration](technique/configuration.md#gestion-derreurs). `doesProductExists` ne catchait en réalité qu'un cas normal ("produit non trouvé"), simplifié en `if`/`else` sans `try`/`except`.
- **Retour de chargement incohérent d'un bouton à l'autre** : certaines actions passent par `runAsync` (spinner + message), d'autres appellent la méthode brute directement (ex. bouton "Charger les pièces" → `getPieces` sans indicateur de chargement, cf. §4).
- **Bouton "Confirm" toujours actif** (cf. §4) alors qu'un état de validation existe déjà côté code — laisse la porte ouverte à une confirmation sans véhicule sélectionné.
- **Mise en surbrillance des articles VSF non fonctionnelle** (cf. §4) — petite incohérence visuelle par rapport aux véhicules/catégories/pièces, où la sélection est bien visible.
- **Documentation "Chemin" vide** pour chaque champ Studio dans le README fonctionnel — **partiellement corrigé** : `x_studio_vehicle_id`/`x_studio_categorie_xglass` (et les champs équivalents sur `fleet.vehicle`/`product.product`) ont désormais un emplacement versionné et documenté (`views/*.xml`) ; les champs Studio historiques (immatriculation, eurocode) restent placés à la main sur chaque instance, sans emplacement tracé.

## 7. Hygiène / sécurité mineure

- **Tokens de session en clair dans les outputs commités** de `controllers/vsf.ipynb` (cookies `XSRF-TOKEN`, `myvsf_session` visibles dans les cellules exécutées et committées) — à nettoyer (effacer les outputs) avant tout partage plus large du dépôt, même si ces tokens sont a priori expirés.
- **`.env` local correctement ignoré par git** (`.gitignore:4`, pattern sans slash donc actif à tout niveau de dossier) — vérifié : le fichier `.env` (racine du module) n'est ni suivi ni présent dans l'historique. Pas de fuite d'identifiants constatée.
- **Notebooks de reverse engineering** (`vsf.ipynb`, `xglass.ipynb`) : utiles comme documentation vivante des contraintes portail (ex. nécessité de charger `initRechercheVehicule.html` avant une recherche X'Glass, cf. [backend](technique/backend.md)), mais mélangent essais-erreurs obsolètes et scénarios de référence — un nettoyage éditorial les rendrait plus exploitables en documentation à part entière.

## 8. Recommandations priorisées

**Quick wins (faible effort, gain immédiat)**
1. ~~Ajouter des notifications utilisateur...~~ **Fait** — service `notification` Odoo dans `runAsync()`.
2. Rebrancher `t-att-disabled="!state.canConfirm"` sur le bouton "Confirm" (le state existe déjà).
3. Corriger la route `/rbm_agent/getVehiculeMeta` → `/rpbm_agent/getVehiculeMeta` (ou l'aligner avec le style sans préfixe des autres routes).
4. Retirer le bouton "Enlever" trompeur (ou implémenter la suppression réelle de la ligne).
5. ~~Réutiliser `XGLASS.getPieceAm()`...~~ **Fait** — `main.py::getPieceAm` réutilise `findSelectionsPiecesAmView()`.
6. Corriger `requirements.txt`/`external_dependencies` pour lister `requests` (`python-dotenv` déjà fait).

**Chantiers structurants (effort plus élevé)**
1. ~~Isoler la session portail par utilisateur Odoo...~~ **Fait**, avec une solution différente de celle envisagée ici : un seul identifiant X'Glass/VSF partagé étant confirmé (pas de pool de comptes), l'isolation par utilisateur ne réglerait pas la contrainte portail — la solution retenue sérialise les sessions widget complètes via un verrou applicatif (`ir.config_parameter`, voir [configuration](technique/configuration.md#concurrence--verrou-de-session)).
2. ~~Formaliser la création des champs `x_studio_*` manquants...~~ **Fait** : `pre_init_hook` idempotent (`hooks.py`) créant les `ir.model.fields` avec `context={'studio': True}` (mécanisme du mixin `web_studio`, vérifié dans le code source Odoo — voir [configuration](technique/configuration.md#mécanisme-retenu--pre_init_hook--contexte-studio)), plus les vues versionnées `views/*.xml` plaçant le widget et les champs correspondants.
3. Rendre la remise VSF (`remiseRPBM`) configurable (paramètre système ou champ) plutôt que hardcodée.
4. Ajouter une politique de sécurité minimale (`ir.model.access.csv`, groupe dédié) plutôt que de s'appuyer uniquement sur `auth='user'`.
5. Fournir un moyen reproductible de pousser les identifiants portails (`XGLASS_USER`/`XGLASS_PASS`/`VSF_LOGIN`/`VSF_PASSWORD`) — **fait**, [`push_credentials.py`](../push_credentials.py) (racine du module, lit `.env`, pousse vers `ir.config_parameter` via XML-RPC).
