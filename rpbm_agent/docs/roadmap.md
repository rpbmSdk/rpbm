# Roadmap — UI & transfert vers Odoo

Établie le 2026-07-24, sur lecture intégrale du module + interrogation de l'instance
`rpbm-preprod` (profil `paradigme-mcp` `rpbm-preprod`, Odoo 17). Complète
[`etat-des-lieux.md`](etat-des-lieux.md) : celui-ci auditait le **code**, celle-ci part
des **données réelles de l'instance** et en déduit un ordre de travaux.

Périmètre demandé : optimisation de l'UI du widget, et fiabilisation du transfert vers
Odoo (création de véhicule, champs Eurocode sur les opportunités, articles sur les
ordres de vente).

**Objectif du module.** Le widget n'est pas un outil de confort : sa finalité est
d'**assainir la base** en y injectant des valeurs fiables et normalisées récupérées depuis
X'Glass et VSF, à la place de saisies manuelles hétérogènes. Le module est encore en phase
de développement et n'a **jamais été mis entre les mains des équipes** — les compteurs à
zéro du §1 sont donc une ligne de base, pas une régression.

---

## 0. Résultats du diagnostic L0.1 / L0.2 (2026-07-25)

Parcours complet rejoué sur `rpbm-pre-prod` via le MCP `chrome-devtools` (capture réseau +
console), sur une piste de test jetable (plaque `DS808DZ`, supprimée après). Le traçage
portail serveur n'a pas été nécessaire : la capture réseau navigateur donne directement les
réponses JSON-RPC de chaque route. **La cause racine des compteurs à zéro est identifiée —
un bug de code, pas un problème d'environnement.**

**① Cause n°1 des écritures à zéro — ordonnancement du verrou dans `onConfirm()` (bloquant,
nouveau).** `AgentWidgetDialog.onConfirm()` appelle `await this.closeAgents()` **avant**
`getRecordData()`. Or `closeAgents()` → `/rpbm_agent_close` → `release_agent_lock()` (libère
le verrou) **et** `xglassAgent.close()` (déconnecte la session X'Glass). Ensuite
`getRecordData()` appelle `/createVehicule`, qui est décoré `@_touch_agent_lock` **et** a
besoin de la session X'Glass vivante (il télécharge l'image véhicule via `xglassAgent.get()`).
Résultat observé : `createVehicule` échoue **systématiquement** avec `UserError: "Votre
session a expiré ou a été reprise par un autre utilisateur"`. Sur `crm.lead`, la création de
véhicule au Confirm ne peut donc **jamais** aboutir → explique directement `fleet.vehicle = 0`
et `x_studio_vehicle_id = 0`. De plus `onConfirm()` n'a **pas de `try/catch`** : l'échec
remonte en `RPC_ERROR` non géré (handler global Odoo) au lieu de la notification typée du
widget. → **[L1.0](#l10)**, priorité maximale.

**② Le reste du chemin d'écriture fonctionne — hypothèse L0.2 « champs ignorés » écartée.**
En pré-créant le `fleet.vehicle` (pour que `getRecordData` saute `createVehicule`), le Confirm
aboutit : `record.update()` envoie les **4 champs** et l'`onchange` renvoie un succès —
```json
{"x_studio_field_NVioD":"DS808DZ","x_studio_vehicle_id":3,
 "x_studio_categorie_xglass":"PARE-BRISE","x_studio_field_ORIyy":"6539R"}
```
Les 4 champs sont **acceptés** par le Record (le many2one `x_studio_vehicle_id` est bien lié à
l'id 3), tous présents dans la vue `crm.lead`. L'hypothèse « un champ absent de la vue est
silencieusement ignoré » est donc **fausse** ici : le blocage est le bug ① en amont.

**③ Enregistrement explicite du widget — amélioré (2026-07-25).** `record.update()` reporte
bien les valeurs dans le formulaire, mais ne les enregistre pas. Le bouton **Confirmer**
conserve ce comportement : l'utilisateur peut continuer à compléter la fiche avant son save
normal. Le bouton **Confirmer et enregistrer** ajoute un save natif Odoo sans navigation ni
rechargement du formulaire ; il applique donc les validations habituelles, y compris les champs
requis hors périmètre du widget.

**④ Connexion portail X'Glass intermittente depuis Odoo.sh (fiabilité).** Au 1ᵉʳ essai,
`/rpbm_agent_auth` a échoué (`RemoteDisconnected: Remote end closed connection without
response` sur `GET portail-xglass.com/mainMenu.html`) ; le 2ᵉ essai a réussi. Le portail
répond depuis un autre réseau (vérifié) → ce n'est pas une panne portail mais une instabilité
de la liaison Odoo.sh↔portail (IP datacenter filtrée par intermittence, vraisemblablement).
La gestion d'erreur typée, elle, **fonctionne parfaitement en live** (XGlassError → UserError
→ notification propre). Un parcours à 11 appels séquentiels est fragile face à cette
instabilité — un léger *retry* réseau sur les `GET` X'Glass mériterait d'être évalué. À noter
aussi : le débogage d'auth du 2026-07-24 (`debug_portals.py`) tournait **en local**, pas
depuis Odoo.sh — d'où le fait que cette instabilité n'avait pas été vue.

**⑤ Doubles appels confirmés en live** (réseau) : `getPlanche` ×2, `getPieces` ×2,
`searchBaseEurocode` ×2 (onchange + clic bouton). `getVehiculeMeta` n'a tiré qu'une fois ici
(un seul véhicule candidat — la course [L1.1](#l11) nécessite ≥ 2 candidats), mais le double
`getPlanche` est bien visible. Confirme [L1.1](#l11), [L2.5](#l25)/L2.6.

**⑥ `VSFArticle` sans champ `id` confirmé** dans le payload réel (`searchBaseEurocode` renvoie
`code`/`name`/`refConstructeur`/`prixVente`/`prixHT`/`stock`/`prixVenteRPBM`/`absoluteImgUrls`,
jamais d'`id`) → la sélection/surbrillance ([L1.3](#l13) prérequis, [L2.3](#l23)) est bien
cassée.

**⑦ `getPieceAm` peut renvoyer `[]`** (pièce OE sans pièce après-marché) → pas de déduction
auto d'eurocode, saisie manuelle nécessaire. Le parcours le gère, mais la déduction auto n'est
pas garantie.

**⑧ Preuve directe pour [L1.2.b](#l12) et [L0.4](#l04) — libellés de calques réels.** La
planche du HYUNDAI I20 remonte ~25 calques : `PARE-BRISE`, `GLACE AR`, `GLACE PORTE AR/AV`,
`GLACE FIXE PORTE AR`, `GLACE RETROVISEUR`, mais aussi `FEU AR`, `PHARE`, `PHARE AB/LP`,
`RETROVISEUR EXT/INTERIEUR`, `ESSUIE-GLACE AV/AR`, `MECANISME ESSUIE-GLACE(-AR)`,
`TOIT OUVRANT`, `LEVE-GLACE PORTE AV/AR`, `ECLAIREUR PLAQUE POLICE`, `FEU REPETITEUR LATERAL`,
`FEU STOP SUPPLEMENTAIRE`, `NECESSAIRE MONTAGE`, `JT/LECHEUR PORTE AV/AR`,
`JT/ENJOLIVEUR PARE-BRISE`. **La grande majorité ne correspond à aucune des 4 valeurs de
« Pièce concernée »** (`Pare-Brise`/`Lunette arrière`/`Glace Latérale`/`Autre...`), et `GLACE AR`
est ambigu (lunette ou latérale ?). Confirme qu'un mapping automatique est intenable et valide
l'approche « suggérer + faire valider » de [L1.2.b](#l12).

---

## 1. Ligne de base (instance `rpbm-pre-prod`)

Compteurs relevés le 2026-07-24. Colonne de gauche : ce que les équipes saisissent à la
main aujourd'hui — c'est exactement le gisement que le widget doit normaliser. Colonne de
droite : ce que le widget écrit dans son état actuel.

| Champ | Modèle | Rempli sur | Écrit par le widget ? |
|---|---|---:|---|
| `x_studio_field_NVioD` — Immatriculation | `crm.lead` | **10 096** / 10 364 | oui |
| `x_studio_field_eENQz` — Pièce concernée | `crm.lead` | **9 980** | **non** |
| `x_studio_field_NwRik` — Eurocode (Complet) | `crm.lead` | **9 394** | **non** |
| `x_studio_field_ORIyy` — Base Eurocode | `crm.lead` | **9 117** | oui |
| `x_studio_field_j8eh3` — VSF Désignation | `crm.lead` | **7 921** | **non** |
| `x_studio_vehicle_id` — Véhicule | `crm.lead` | **0** | oui |
| `x_studio_categorie_xglass` — Catégorie X'Glass | `crm.lead` | **0** | oui |
| `x_studio_vehicle_id` / `x_studio_categorie_xglass` | `sale.order` | **0** / 7 106 | oui |
| — | `fleet.vehicle` | **0 enregistrement** | oui (`/createVehicule`) |
| `x_studio_reference_constructeur` | `product.product` | **0** | oui (`/createProduct`) |
| `product.supplierinfo` fournisseur VSF (id 5708) | — | **0 ligne** | oui (`/createProduct`) |

Lecture : le module n'ayant jamais été déployé auprès des équipes, les colonnes à zéro sont
attendues. Ce que ce tableau montre en revanche, c'est un **désalignement de cible** : les
champs alimentés aujourd'hui à la main (10 096 immatriculations, 9 980 pièces concernées,
9 394 eurocodes complets, 7 921 désignations VSF) ne sont pas ceux que le widget écrit.
En l'état, le widget créerait une seconde série de champs parallèle au lieu de fiabiliser
la série existante — l'inverse de l'objectif d'assainissement.

## 2. Diagnostic — trois axes

**(A) Le widget n'écrit pas dans les champs qui portent la donnée métier.**
`x_studio_categorie_xglass` (char, créé par `pre_init_hook`) est vide, alors que la notion
métier est portée par `x_studio_field_eENQz` « Pièce concernée », une **sélection** à
4 valeurs (`Pare-Brise`, `Lunette arrière`, `Glace Latérale`, `Autre...`) remplie sur
9 980 pistes — et qui, d'après la cartographie
[`prix_devis`](../../Jobs/Gestion%20Stock/prix_devis/README.md), **pilote le forfait de pose**
dans le calcul du prix de vente. Idem pour l'eurocode : le widget ne pousse que la **base**
(5 caractères), alors que la valeur qui sert au métier est l'**Eurocode (Complet)**
(9 394 pistes) plus la **désignation VSF** (7 921 pistes) — toutes deux saisies à la main
aujourd'hui, alors que le widget les a sous la main dès qu'un article VSF est sélectionné.

C'est le cœur du chantier d'assainissement : normaliser suppose d'abord de savoir quel
champ est la cible de référence pour chaque donnée, d'où la cartographie de
[L0.4](#l04).

**(B) Sur `sale.order`, les champs ciblés sont `related` vers l'opportunité.**
Vérifié via `fields_get` : `x_studio_immatriculation_`, `x_studio_base_eurocode`,
`x_studio_eurocode_complet` sont `related` (stockés) vers `opportunity_id.*`. Écrire
dessus depuis le devis **mute silencieusement l'opportunité**, et est un **no-op sur les
38 devis sans opportunité** (7 106 devis, 7 068 avec `opportunity_id`). Le widget ne
distingue pas les deux cas.

**(C) Le chemin de lecture X'Glass a une course sur l'état de session du portail.**
Point confirmé comme prioritaire. `VehiculeComponent.onWillStart()` appelle `/rbm_agent/getVehiculeMeta`
pour **chaque véhicule candidat affiché**, en parallèle — et cette route commence par
`self.getPlanche(vehiculeId)`, c'est-à-dire un `selectVehicule()` **côté portail X'Glass**,
qui est un état serveur global. Trois véhicules candidats = trois sélections concurrentes
sur la même session portail ; la planche récupérée ensuite par la dialog peut être celle
d'un autre véhicule que celui sélectionné. Détail complet en [L1.1](#l11).

**(D) Les deux champs propres au widget ne suivent pas cette même convention `related`.**
Vérification faite sur l'ensemble des champs `x_studio_*` de `sale.order` : la quasi-totalité
de ceux qui portent une donnée métier partagée avec l'opportunité sont des `related` stockés
vers `crm.lead` — pas seulement immatriculation/eurocodes, mais aussi
`x_studio_pice_concerne` → `opportunity_id.x_studio_field_eENQz` (« Pièce concernée » elle-même)
et `x_studio_pice_trouve`, `x_studio_difficult_montage`, les 4 prix VSF bruts, etc. C'est la
convention de l'instance : **`crm.lead` est la source, `sale.order` recopie en lecture**.
Or `x_studio_vehicle_id` et `x_studio_categorie_xglass`, créés par `pre_init_hook`
(`hooks.py`), sont les **deux seuls champs du module** créés comme paires indépendantes sur
les deux modèles plutôt que comme `related` — incohérent avec le reste de l'instance, et
cause directe des deux lignes à 0 sur `sale.order` : une valeur écrite depuis l'opportunité
n'apparaît jamais sur le devis, et réciproquement. Correctif en [L1.2](#l12).

---

## 3. Ordre des travaux

Priorité assumée : **L0 → L1 avant L2**. Polir l'UI d'un parcours dont l'écriture
n'aboutit pas ne produit aucune valeur ; L1 est ce qui transforme 10 000 saisies manuelles
en saisies assistées. L2 rend ce gain utilisable au quotidien. **L4 est une piste séparée,
non bloquante** : elle ne conditionne pas L0/L1/L2/L3 et peut démarrer indépendamment
(atelier métier), mais sa cartographie a intérêt à réutiliser celle de L0.4.

| Lot | Objet | Effort | État |
|---|---|---|---|
| **L0.1/L0.2** | Diagnostic bout-en-bout instrumenté | S | **Fait** (2026-07-25, voir [§0](#0-résultats-du-diagnostic-l01--l02-2026-07-25)) |
| **L0.4** | Cartographie des champs Studio + `base.automation` | M | **Fait** ([`docs/cartographie/`](../../docs/cartographie/README.md)) |
| **L1** | Transfert vers Odoo — cible des champs, séquencement, écriture | L | L1.0 identifié comme bloquant n°1 |
| **L2** | UI/UX du widget | M | à faire |
| **L3** | Hygiène : sécurité, configuration, dette résiduelle | M | à faire |
| **L4** | Refonte du calcul du prix sur les mécanismes natifs Odoo — initiative séparée | XL | atelier métier |

---

## L0 — Diagnostic bout-en-bout et cartographie (à faire en premier, M)

Avant toute correction : établir **où** le parcours casse aujourd'hui, et **quels champs**
sont la cible de référence pour chaque donnée normalisée.

- **L0.1** — Ouvrir le widget sur une piste réelle de `rpbm-pre-prod` (immatriculation déjà
  renseignée), dérouler véhicule → catégorie → pièce → eurocode → article, cliquer
  Confirm, puis Enregistrer. Instrumenter avec le MCP `chrome-devtools` (console + réseau)
  et le traçage portail (`rpbm_agent.trace` = `1`, cf.
  [configuration](technique/configuration.md#débogage-des-portails)).
- **L0.2** — Noter, pour chaque route : code de retour, payload, et pour `record.update()`
  la liste des champs effectivement acceptés par le `Record` Odoo (un champ absent de la
  vue ou `readonly` est ignoré sans erreur — hypothèse principale pour expliquer les
  compteurs à 0).
- **L0.3** — Consigner le résultat en tête de ce fichier. Les items L1 ci-dessous sont
  écrits à partir du code ; L0 dira lesquels sont la cause réelle et lesquels sont de la
  robustesse préventive.

**Vérification** : un véhicule créé et un `x_studio_vehicle_id` non nul sur une piste de
test, ou un diagnostic écrit expliquant pourquoi ça n'arrive pas.

### L0.4 — Cartographie complète des champs Studio `crm.lead` / `sale.order` {#l04}

> **Fait (2026-07-25).** Livrée dans [`docs/cartographie/`](../../docs/cartographie/README.md)
> (à la racine du dépôt) : inventaire exhaustif généré (`crm-lead.md` 265 champs, `sale-order.md`
> 87), [`automatisations.md`](../../docs/cartographie/automatisations.md) (7 `base.automation`),
> [`calques-mapping.md`](../../docs/cartographie/calques-mapping.md), et migration de
> `prix-devis/`. Deux découvertes ont rétroagi sur L1 (voir L1.3 `refConstructeur`, L1.6
> « Tarif x glass »). Le reste de cette section documente le cahier des charges initial.

**Objet.** Livrable documentaire autonome, condition d'entrée de L1 : sans savoir quel champ
porte réellement quelle donnée, « normaliser » revient à créer une série parallèle de plus.
Cette cartographie sert à trancher, champ par champ, entre **cible du widget**,
**champ à créer**, **champ à laisser tel quel** et **champ obsolète**.

**Emplacement.** Nouveau dossier documentaire à la racine du dépôt : `docs/cartographie/`
(distinct de `rpbm_agent/docs/`, qui documente le module ; celle-ci documente
l'**instance**). Choix par défaut, à confirmer au démarrage de L0.

**Reprise de l'existant.** Deux cartographies partielles existent déjà dans `Jobs/` et sont
à intégrer, pas à refaire :
- `Jobs/Gestion Stock/prix_devis/` — cartographie du prix de vente (`README.md`,
  `champs-crm-lead.md`, `champs-sale-order.md`). Récente, établie via MCP sur
  `rpbm-preprod`, avec vérification numérique sur un devis réel. **Format de référence** :
  tableaux `champ technique / libellé / type / rôle`, formules `compute` reproduites,
  diagrammes Mermaid de cascade, section « anomalies ». À migrer telle quelle dans
  `docs/cartographie/` et à étendre.
- `Jobs/champs_studio/studio_fields.json` + `studio_fields_by_model.json` — dump du
  11/10/2024, **obsolète** (déjà signalé comme tel par le README `prix_devis` : le schéma a
  beaucoup évolué depuis). À traiter comme historique, pas comme source.

Note : `Jobs/` est très largement exclu par `.gitignore` (seul `Jobs/Gestion Stock/` est
suivi) — la migration vers `docs/cartographie/` rend aussi ces documents versionnés.

**Contenu attendu**, par modèle (`crm.lead`, `sale.order`) :
1. Inventaire exhaustif des `x_studio_*` : nom technique, libellé, type, `related`,
   `store`, `readonly`, `compute` le cas échéant, taux de remplissage réel.
2. **Statut vis-à-vis du module**, colonne décisive :
   `cible widget` / `à créer` / `lecture seule` / `obsolète` / `hors périmètre`.
3. Les chaînes `related` `sale.order` → `crm.lead` (la donnée vit sur l'opportunité, le
   devis ne fait que la recopier — cf. cause (B) et README `prix_devis`).
4. Les champs déjà marqués `[Obsolète]` ou `OBSOLETE - ` dans leur libellé (~60 sur
   `crm.lead`), pour ne pas les recibler par erreur.
5. **Les `base.automation`/`ir.actions.server` qui touchent ces champs.** La cartographie
   `prix_devis` en a déjà trouvé 3 (sélection du `expected_revenue` selon `x_studio_prix_retenu`,
   cf. `champs-crm-lead.md#mécanisme-aval`) — c'est le mécanisme par lequel des utilisateurs
   non techniques ont étendu le comportement de l'instance sans toucher au code. Les
   inventorier (déclencheur, condition, champ écrit) au même titre que les champs eux-mêmes :
   un champ écrit par le widget peut aussi être **lu** par une automatisation en aval, ce qui
   déplace le rayon d'effet d'un changement bien au-delà du widget.

**Point de vigilance à traiter dans la cartographie.** Les 4 prix VSF de `crm.lead`
(`VSF - Prix VIT`, `JT1`, `JT2`, `JT3`) ne sont pas de simples champs d'affichage : leur
somme × 1,76 produit `VSF - Prix RV`, qui alimente toute la cascade du prix de vente du
devis quand « Pièce Trouvée » vaut `VSF` (cf. `prix_devis/README.md`). **Toute écriture du
widget sur ces champs modifie donc le prix facturé** — il faut établir précisément quel
prix VSF alimente `VIT` et ce que représentent `JT1`/`JT2`/`JT3` (joints ?) avant
d'implémenter [L1.3](#l13).

**Vérification.** `docs/cartographie/` contient un tableau par modèle où **chaque** champ
`x_studio_*` porte un statut, et les champs cités par L1.2/L1.3/L1.4 y sont tranchés.

---

## L1 — Transfert vers Odoo

### L1.0 — Corriger l'ordonnancement de `onConfirm()` : créer avant de fermer {#l10}

> **Correctif client implémenté (2026-07-25)** dans `static/src/agent_widget_dialog.js`, mais
> le rejeu live a montré qu'un asset frontend obsolète pouvait encore appeler
> `/rpbm_agent_close` avant `/createVehicule`. **Correctif serveur complémentaire implémenté
> (2026-07-25)** dans `controllers/main.py` : la création Odoo ne dépend plus du verrou ni de
> la session X'Glass ; seule l'image est ignorée si la session est déjà fermée. **Complément de
> persistance implémenté (2026-07-25)** : le widget propose désormais **Confirmer et enregistrer**
> en plus de **Confirmer** ; il s'appuie sur le save natif Odoo sans navigation ni rechargement
> du formulaire. À vérifier en live après déploiement. Nettoyage connexe (retrait des `onConfirm()`
> des sous-classes qui ne font qu'appeler `super`) laissé à [L3.4](#l3).

**Priorité maximale — bug bloquant confirmé en live (voir [§0 ①](#0-résultats-du-diagnostic-l01--l02-2026-07-25)).**
C'est *le* défaut qui met à zéro toutes les écritures du widget sur `crm.lead`.

**Problème.** `AgentWidgetDialog.onConfirm()` :
```js
async onConfirm() {
    await this.closeAgents();               // libère le verrou + logout X'Glass
    const data = await this.getRecordData(); // → createVehicule : besoin du verrou ET de X'Glass
    this.props.record.update(data);         // (non await)
    this.props.close();
}
```
`closeAgents()` est appelé **trop tôt** : il relâche le verrou (`@_touch_agent_lock` fait alors
échouer `createVehicule`) et déconnecte X'Glass (dont `createVehicule` a besoin pour
télécharger l'image). Échec systématique.

**Correctif minimal.** Réordonner : construire les données (donc créer le véhicule) **avant**
de fermer la session, envelopper dans `runAsync` (gestion d'erreur + notification, cf. le
bug « pas de try/catch »), et n'appeler `closeAgents()` qu'à la fin :
```js
async onConfirm() {
    await this.runAsync(async () => {
        const data = await this.getRecordData();  // createVehicule pendant que la session vit
        this.props.record.update(data);
        await this.closeAgents();                 // libère verrou + X'Glass une fois fini
        this.props.close();
    });
}
```
Attention à ne fermer/`close()` **que** si `getRecordData()` a réussi (sinon laisser la dialog
ouverte pour réessai, verrou conservé). Vérifier aussi l'`onDiscard()` (lui appelle bien
`closeAgents()` en premier, ce qui est correct puisqu'il n'écrit rien).

**Fichiers.** `static/src/agent_widget_dialog.js` (+ `onConfirm` des sous-classes, qui ne font
qu'appeler `super`).

**Vérification.** Sur une piste sans véhicule Odoo préexistant : Confirm → un `fleet.vehicle`
créé, `x_studio_vehicle_id` renseigné, **aucun** `RPC_ERROR` « session expirée ». C'est le
scénario exact qui échouait au diagnostic.

### L1.1 — Supprimer la course sur la sélection véhicule X'Glass {#l11}

> **Implémenté (2026-07-25)** — à vérifier en live après déploiement : les métadonnées sont
> désormais chargées uniquement pour le véhicule sélectionné, puis transmises à sa carte.

**Problème.** `VehiculeComponent.setup()` déclenche `getVehiculeMeta()` en `onWillStart`
pour chaque véhicule candidat ; la route appelle `getPlanche()` → `selectVehicule()` côté
portail, état global de la session. N candidats = N sélections concurrentes, puis la
planche de la dialog peut correspondre au mauvais véhicule. Aggravé par
`_touch_agent_lock` qui fait un `cr.commit()` par appel.

**Correctif minimal.** Ne récupérer les métadonnées (VIN/CNIT/date MEC) que pour le
véhicule **sélectionné**, dans la dialog (le code y existe déjà, en commentaire :
`agent_widget_dialog.js:353-360`), et les passer en prop à `VehiculeComponent`. Un seul
appel, déclenché par le `useEffect` sur `selectedVehicule` déjà présent.

**Fichiers.** `static/src/VehiculeComponent.js`, `static/src/agent_widget_dialog.js`,
`static/src/VehiculeComponent.xml`.

**Vérification.** Recherche renvoyant ≥ 2 véhicules : exactement un appel
`getVehiculeMeta` dans l'onglet réseau, et la planche correspond au véhicule surligné.

### L1.2 — Catégorie X'Glass : aligner le champ `related` et traiter « Pièce concernée » {#l12}

Ce lot couvre deux problèmes distincts, l'un mécanique et immédiatement actionnable, l'autre
une vraie question de conception qui ne se résout pas par une simple table de correspondance.

#### L1.2.a — Aligner `x_studio_vehicle_id`/`x_studio_categorie_xglass` sur la convention `related`

> **Implémenté (2026-07-25)** — les nouvelles installations créent les deux champs `related`
> stockés ; la migration `17.0.260725.6` recrée les champs existants seulement s'ils sont vides,
> sinon elle bloque l'upgrade pour éviter toute perte de données. À vérifier en live après
> déploiement.

**Problème.** Cause racine (D). Ces deux champs sont les seuls du module créés comme paires
indépendantes `crm.lead`/`sale.order` par `pre_init_hook`, alors que tout le reste de
l'instance (immatriculation, les deux eurocodes, « Pièce concernée », « Pièce Trouvée »,
Difficulté Montage, les 4 prix VSF bruts…) suit la même convention : `crm.lead` source,
`sale.order` recopie en `related` stocké.

**Correctif.** Modifier `FIELDS_TO_ENSURE`/`pre_init_hook` (`hooks.py`) pour que les entrées
`sale.order` de `x_studio_vehicle_id` et `x_studio_categorie_xglass` soient créées avec
`related: 'opportunity_id.x_studio_vehicle_id'` / `related: 'opportunity_id.x_studio_categorie_xglass'`
(store=True, comme les champs `related` déjà présents sur l'instance), au lieu de champs
indépendants. Les deux champs actuels sur `sale.order` sont à 0 utilisation constatée :
aucune perte de données à les recréer (`unlink` + recréation, un `ir.model.fields` manuel
n'accepte pas de changer son type de définition après coup).

**Conséquence pour le reste de la roadmap.** Une fois ce correctif en place, écrire
`x_studio_vehicle_id`/`x_studio_categorie_xglass` depuis `sale.order` revient exactement au
même cas que les champs eurocode : ça suppose `opportunity_id` renseigné, et [L1.4](#l14)
s'applique uniformément à *tous* les champs écrits par le widget sur un devis, pas
seulement aux eurocodes.

**Fichiers.** `hooks.py`.

**Vérification.** `fields_get` sur `sale.order` montre `related` renseigné pour les deux
champs ; une valeur écrite sur `crm.lead.x_studio_vehicle_id` apparaît en lecture sur le
devis lié.

#### L1.2.b — Écrire « Pièce concernée » (`x_studio_field_eENQz`) — sous confirmation, pas en silence

**Problème.** Cause racine (A) : `x_studio_categorie_xglass` (0 utilisation) n'est pas la
donnée qui compte pour le métier — c'est `x_studio_field_eENQz` « Pièce concernée »
(9 980 utilisations), une sélection à 4 valeurs qui **pilote le forfait de pose** dans la
cascade de prix (`prix_devis/champs-crm-lead.md#niveau-4`).

**Ce n'est pas un simple problème de table de correspondance.** Le widget ne connaît que le
*libellé du calque X'Glass* cliqué par l'utilisateur (ex. `"PARE-BRISE"`, seule valeur
confirmée dans les traces existantes — `controllers/xglass.ipynb:130`) ; rien ne garantit
que l'ensemble des calques X'Glass se répartit proprement sur les 4 valeurs
(`Pare-Brise`/`Lunette arrière`/`Glace Latérale`/`Autre...`) de `eENQz`. C'est très
vraisemblablement *pourquoi* `x_studio_categorie_xglass` avait été créé au départ : un champ
texte libre qui accepte n'importe quel libellé X'Glass sans avoir à trancher ce mapping.

**Ce champ pilote le prix : une correspondance automatique fausse est pire qu'un champ resté
vide.** Proposition : le widget **suggère** une valeur (correspondance textuelle simple sur
le libellé du calque) pré-remplie dans un champ de sélection *visible dans la dialog*, que
l'utilisateur valide ou corrige avant de cliquer Confirm — jamais une écriture silencieuse.
`x_studio_categorie_xglass` continue d'être écrit en parallèle (libellé X'Glass exact, pour
traçabilité et audit d'un mauvais mapping).

**Prérequis, à faire dans [L0.4](#l04) avant d'écrire le code** : constituer, à partir de
plusieurs véhicules de types variés (`/getPlanche` réel, pas une hypothèse), l'inventaire
complet des libellés de calques X'Glass rencontrés, et vérifier avec le métier lesquels
correspondent sans ambiguïté à `Pare-Brise`/`Lunette arrière`/`Glace Latérale`, lesquels
tombent sur `Autre...`, et si `Autre...` seul suffit pour le reste ou s'il faut une valeur
« indéterminé, à saisir manuellement » distincte.

**Fichiers.** `static/src/utils.js`, `static/src/agent_widget_dialog.js`,
`static/src/agent_widget_dialog.xml`, `docs/technique/champs/crm-lead.md`.

**Vérification.** Confirm sur une piste → « Pièce concernée » pré-remplie visible et
modifiable avant validation, jamais écrite sans passage par ce champ visible.

### L1.3 — Pousser l'article VSF sélectionné dans les champs Eurocode/VSF {#l13}

**Problème.** C'est le gain le plus direct de la demande « définition des champs Eurocode
sur les opportunités ». Une fois un article VSF sélectionné, le widget connaît le code
eurocode complet, la désignation, la référence constructeur et les prix — et n'en écrit
aucun. Les utilisateurs les retapent (9 394 + 7 921 saisies).

**Le widget atteint bien ce stade en mode Opportunité — vérifié dans le code, pas supposé.**
`AgentWidgetDialogCrmLead.onConfirm()` ne fait qu'appeler `super.onConfirm()`
(`agent_widget_dialog_crm_lead.js:44`), et la cascade de `useEffect` qui mène jusqu'à
`articlesVsf` (véhicule → planche → calque → pièces → pièce AM → eurocode → recherche VSF)
est entièrement portée par `AgentWidgetDialog`, commune aux deux modèles. Seul le template
diffère : `ArticleComponent` (sans les boutons Créer/Ajouter, propres au devis) est utilisé
tel quel sur `crm.lead`, mais reste cliquable (`onClickArticleVsf`). Rien dans le code
n'empêche donc de sélectionner un article VSF et d'écrire ces champs depuis une Opportunité.
**À confirmer côté usage réel dans le parcours instrumenté de L0.1** (le doute exprimé porte
sans doute sur la pratique métier — s'arrête-t-on à véhicule/catégorie sur la Piste,
l'eurocode venant plus tard sur le devis — plutôt que sur une limite technique).

**`x_studio_field_j8eh3` (VSF - Désignation) est confirmé hors cascade de prix** —
absent de `champs-crm-lead.md` (niveaux 0 à 5 et branche annexe) : c'est un champ purement
descriptif, sans lien avec `VSF - Prix RV` ni aucun autre calcul. Écriture sans risque
tarifaire.

**Cible par modèle — la propagation `related` change la donne.** Une fois [L1.2.a](#l12) en
place, la plupart des champs VSF ont déjà un miroir `related` côté `sale.order`
(confirmé dans `champs-sale-order.md`) : écrire le champ `sale.order` propage
automatiquement vers `crm.lead` (comportement standard d'un champ Odoo `related` stocké,
sans code supplémentaire). Il faut donc cibler des noms différents selon le modèle porteur,
sur le même principe que `baseEurocodeField` déjà surchargé par `CrmLead`/`SaleOrder`
(`utils.js`) :

| Source (article VSF) | Cible `crm.lead` | Cible `sale.order` (`related`) | Libellé |
|---|---|---|---|
| `code` | `x_studio_field_NwRik` | `x_studio_eurocode_complet` | Eurocode (Complet) |
| `name` | `x_studio_field_j8eh3` | `x_studio_vsf_dsignation_1` | VSF - Désignation |
| `stock` | `x_studio_field_BKtpw` | `x_studio_vsf_qt_dispo` | VSF - Qté Dispo |
| `refConstructeur` | `x_studio_field_e6OAd` **ou `_MNzfJ`** ⚠ | **aucun miroir trouvé** | Autre Référence / Code Constructeur |
| `prixVenteRPBM` | `x_studio_field_F0zf7` | `x_studio_vsf_prix_vit_1` | VSF - Prix VIT ⚠ voir ci-dessous |

> ⚠ **`refConstructeur` : cible à corriger (constat L0.4).** `x_studio_field_e6OAd`
> « Autre Référence » n'est rempli que **43 fois** sur 10 364 pistes, alors que
> `x_studio_field_MNzfJ` « Code Constructeur » l'est **3 411 fois** — c'est ce dernier que le
> métier utilise réellement pour cette donnée. Cibler `MNzfJ` (à confirmer avec le métier), pas
> `e6OAd`. Voir [cartographie/crm-lead.md](../../docs/cartographie/crm-lead.md).

`refConstructeur` n'a pas de champ `related` équivalent sur `sale.order` aujourd'hui — soit le
widget n'écrit ce champ que depuis une Opportunité (gap mineur assumé), soit un nouveau champ
`related` est créé sur `sale.order` pour parité (même mécanisme que [L1.2.a](#l12)).

Ne **jamais** écrire `x_studio_field_HJIi5` (Prix XGlass HT) ni `x_studio_field_h06UD`
(RV Pièce) : vérifié `readonly=True` sur l'instance, ce sont des champs calculés.

> ⚠ **`VSF - Prix VIT` n'est pas un champ d'affichage.** Il entre dans
> `VSF - Prix RV` = (`VIT` + `JT1` + `JT2` + `JT3`) × 1,76, qui devient le prix de
> référence de la cascade dès que « Pièce Trouvée » vaut `VSF` ou `À trouver`, et remonte
> jusqu'au `Prix + Pose (TTC)` du devis (cf.
> [`prix_devis`](../../Jobs/Gestion%20Stock/prix_devis/README.md)). Écrire ce champ depuis
> le widget **change le prix facturé au client**. La ligne du tableau ci-dessus est une
> hypothèse à valider en [L0.4](#l04), pas une décision : il faut d'abord établir quel prix
> VSF alimente `VIT`, et ce que couvrent `JT1`/`JT2`/`JT3`. Les 3 autres champs du tableau
> (eurocode, désignation, quantité) sont sans effet sur le prix et peuvent être implémentés
> indépendamment. Voir aussi [L4](#l4) : si la cascade de prix est un jour remplacée par les
> mécanismes natifs Odoo, cette écriture devient temporaire par construction.

Prérequis technique : la sélection d'un article VSF **ne fonctionne pas** aujourd'hui —
`onClickArticleVsf(code)` compare `article.id === articleId` alors que `VSFArticle` n'expose
pas d'`id`. À corriger d'abord (comparer sur `code`, dans `onClickArticleVsf` et dans le
getter `style` de `ArticleComponent`) ; c'est aussi le correctif de surbrillance de
[L2.3](#l23).

**Fichiers.** `static/src/agent_widget_dialog.js`, `static/src/ArticleComponent.js`,
`static/src/agent_widget_dialog_crm_lead.js`, `docs/technique/champs/crm-lead.md`.

**Vérification.** Sélection d'un article puis Confirm → les 5 champs ci-dessus remplis sur
la piste, et pas d'erreur sur un article sans image/stock.

### L1.4 — Traiter explicitement le cas `sale.order` sans opportunité {#l14}

**Problème.** Cause racine (B), élargie par [L1.2.a](#l12) : immatriculation, eurocodes,
« Pièce concernée », et désormais `x_studio_vehicle_id`/`x_studio_categorie_xglass` sont
tous des `related` vers `opportunity_id.*`. Écrire depuis le devis mute l'opportunité sans
que l'utilisateur le sache, et ne fait **rien** sur les 38 devis sans opportunité — plus
seulement pour les eurocodes, mais pour la totalité de ce qu'écrit le widget.

**Correctif minimal.** Dans `AgentWidgetDialogSaleOrder` :
- tous les champs écrits par le widget étant désormais `related`, la question devient
  binaire : `opportunity_id` présent ou non, pas un traitement champ par champ ;
- si présent, l'indiquer dans l'UI (une ligne de texte, pas une modale) : « les données du
  véhicule/pièce sont portées par l'opportunité liée » ;
- si absent, avertir au moment du Confirm — un devis créé hors parcours CRM ne peut
  structurellement pas recevoir ces données tant qu'aucune opportunité n'est liée — au lieu
  d'une écriture silencieusement perdue.

**Fichiers.** `static/src/agent_widget_dialog_sale_order.js` + template.

**Vérification.** Un devis avec opportunité (champs propagés, visibles sur l'opportunité)
et un devis sans (avertissement affiché, pas de perte silencieuse).

### L1.5 — Fiabiliser `/createProduct` {#l15}

**Problèmes cumulés** (`controllers/main.py:351-393`) :
- la route ne fait **aucun `return`** → le frontend ne peut pas distinguer succès et échec ;
- aucun contrôle d'existence avant `create()` → doublon de `default_code` possible si
  l'utilisateur double-clique ;
- `type: 'product'` suppose `stock` installé ; `categ_id`/`uom_id` laissés au défaut.

**Prix : validé, ne pas modifier.** Le `product.supplierinfo` doit bien être créé avec
`prixVenteRPBM` — `prixHT` est le **prix public VSF**, pas le prix d'achat RPBM. Point
tranché avec le métier le 2026-07-24 ; l'écrire ici pour qu'une future relecture de
`vsf.py` ne l'« corrige » pas à tort.

**Correctif minimal.** Retourner le dict du produit (même forme que `/doesProductExists`),
faire un `search` avant `create` et retourner l'existant le cas échéant, et lever un
`UserError` explicite sur échec.

**Fichiers.** `controllers/main.py`, `static/src/agent_widget_dialog_sale_order.js`.

**Vérification.** Double clic sur « Créer » → un seul produit, une seule
`product.supplierinfo` ; le bouton bascule sur « Voir » sans rechargement.

### L1.6 — Fiabiliser l'ajout de ligne au devis

**Problèmes.** `addToSaleOrder()` fait `order_line.addNewRecord({context: {default_product_id}})`
puis force `newLine.dirty = true` — contournement d'API fragile, et la ligne ne reçoit ni
quantité explicite, ni le prix X'Glass alors que `sale.order.line.x_studio_prix_x_glass`
existe sur l'instance. Le bouton « Enlever » appelle `addToSaleOrder()` (il ajoute).

> **`x_studio_prix_x_glass` a un effet tarifaire automatique (constat L0.4).** Une
> `base.automation` « Tarif x glass » (`on_create_or_write`, filtre `x_studio_prix_x_glass != 0`)
> force `price_unit = x_studio_prix_x_glass × 1.5` sur la ligne. Renseigner ce champ **est**
> donc le mécanisme de tarification de la ligne, pas une donnée d'affichage — à intégrer
> explicitement (le prix unitaire n'est pas à poser à la main, l'automatisation s'en charge).
> Voir [cartographie/automatisations.md](../../docs/cartographie/automatisations.md).

**Correctif minimal.** Passer par l'API standard de la liste éditable (`addNewRecord` puis
`update()` sur les champs, en laissant les `onchange` Odoo calculer taxes),
renseigner `x_studio_prix_x_glass` depuis la pièce OE sélectionnée (l'automatisation « Tarif x
glass » en dérive le prix unitaire), et **supprimer** le bouton « Enlever » (l'implémenter
réellement est hors périmètre : la suppression de ligne existe déjà dans la liste du devis).

**Fichiers.** `static/src/agent_widget_dialog_sale_order.js` + template.

**Vérification.** Ajout de 2 articles → 2 lignes avec produit, quantité 1, prix et taxes
calculés par Odoo, sauvegarde du devis sans erreur.

---

## L2 — UI/UX du widget

### L2.1 — Structurer la dialog en étapes

**Problème.** Le template est une suite de `div` avec styles inline, sans hiérarchie
visuelle : véhicules, calques, pièces, pièces AM et articles VSF s'empilent dans une
`Dialog size="lg"`. Les `PieceAMComponent` sont rendus comme **frères** des
`PieceComponent` dans le même conteneur flex (`agent_widget_dialog.xml:41-48`) — visuellement,
une pièce après-marché ressemble à une pièce d'origine.

**Correctif minimal.** Pas de refonte : `size="xl"`, découpage en 4 sections titrées
(Véhicule / Catégorie / Pièce / Article VSF) avec les classes Bootstrap déjà chargées par
Odoo, et imbrication des `PieceAMComponent` **dans** la carte de leur pièce. Remplacer les
`style="..."` inline par les utilitaires Bootstrap existants (`w-50`, `m-2`, `flex-wrap`).
Aucune feuille de style nouvelle, aucune dépendance.

**Fichiers.** `static/src/agent_widget_dialog.xml`, `static/src/Piece*.xml`,
`static/src/VehiculeComponent.xml`, `static/src/ArticleComponent.xml`.

### L2.2 — Rebrancher l'état du bouton Confirm

`t-att-disabled="!state.canConfirm"` est commenté avec un `<!-- FIXME -->`
(`agent_widget_dialog.xml:75`) alors que `canConfirm()` et le `useEffect` qui le recalcule
existent. Deux détails à corriger en même temps : la faute de frappe `canConfim` (état) vs
`canConfirm` (référencé dans le template commenté — c'est pourquoi le rebranchement naïf
désactiverait le bouton en permanence), et enrichir `canConfirm()` une fois L1.2/L1.3 en
place (véhicule **et** catégorie requis).

**Vérification.** Bouton grisé à l'ouverture, actif après sélection d'un véhicule.

### L2.3 — Corriger la surbrillance des articles VSF {#l23}

Même correctif que le prérequis de [L1.3](#l13) : comparer sur `code`. Aujourd'hui la
sélection d'un article n'est jamais visible, alors qu'elle l'est pour les véhicules,
calques et pièces.

### L2.4 — Corriger l'état de chargement partagé entre composants

**Problème réel, pas cosmétique.** `utils.js:57-60` définit `asyncWidgetState` comme un
objet **au niveau du module**, et `asyncWidget.setup()` fait `useState(asyncWidgetState)`
— toutes les instances qui n'écrasent pas `this.state` partagent donc le même proxy
réactif. C'est le cas d'`ArticleComponent` : sur une piste, le spinner d'un article
s'affiche sur **tous** les articles.

**Correctif.** `useState({ ...asyncWidgetState })` — une ligne.

**Vérification.** Sur une piste avec ≥ 2 articles VSF, une action sur l'un ne fait pas
tourner le spinner des autres.

### L2.5 — Uniformiser les retours de chargement {#l25}

Certaines actions passent par `runAsync` (spinner + message), d'autres appellent la méthode
brute : le bouton « Charger les pièces » appelle `getPieces` directement
(`agent_widget_dialog.xml:32`), sans indicateur — et fait double emploi avec le `useEffect`
sur `selectedCalque` **et** avec l'appel direct dans `onClickCalque()`
(`agent_widget_dialog.js:416`), soit jusqu'à trois chargements pour un clic.

**Correctif minimal.** Retirer l'appel direct dans `onClickCalque()` (le `useEffect` suffit),
supprimer le bouton « Charger les pièces » devenu redondant, et router toute action
utilisateur par `runAsync` avec un message.

### L2.6 — Débounce sur le champ Base Eurocode

`onChangeBaseEurocode` déclenche, via le `useEffect` sur `baseEurocode`, une requête VSF à
chaque `change`. Acceptable sur `change` (pas `input`), mais la déduction automatique depuis
la pièce AM peut relancer une recherche identique à celle en cours. Garder la dernière
valeur recherchée et ne pas relancer si elle est inchangée — trois lignes, pas de
bibliothèque de debounce.

### L2.7 — Nettoyage d'état à la fermeture

`onDiscard()`/`onConfirm()` ferment sans réinitialiser, et surtout : si l'utilisateur ferme
la dialog par la croix ou `Échap`, **`/rpbm_agent_close` n'est jamais appelé** et le verrou
de session reste posé jusqu'à son expiration glissante de 15 min — un autre utilisateur est
bloqué pour rien. Ajouter un `onWillUnmount` qui appelle `closeAgents()`.

**Vérification.** Ouvrir le widget, fermer par `Échap`, vérifier que
`ir.config_parameter` `rpbm_agent.session_lock` est vidé.

---

## L3 — Hygiène

- **L3.1 — Sécurité (M).** Aucun `security/`, toutes les routes en `auth='user'` : n'importe
  quel utilisateur interne peut créer des véhicules/produits et consommer la session
  portail unique. Ajouter un groupe dédié (`rpbm_agent.group_user`) et le vérifier dans les
  routes ; conditionner l'affichage du widget à ce groupe dans les vues.
- **L3.2 — Configuration (S).** Sortir du code : `VSF_PARTNER_ID = 5708` (`main.py:23` —
  vérifié, correspond bien à « VSF - VITRO SERVICE FRANCE » sur cette instance) et
  `remiseRPBM = 0.2` (`vsf.py`), tous deux en `ir.config_parameter`, cohérent avec les 4
  identifiants déjà gérés ainsi.
- **L3.3 — `requirements.txt` / `external_dependencies` (S).** `requests` manquant dans les
  deux.
- **L3.4 — Code mort (S).** À faire au passage sur chaque fichier touché, pas en chantier
  dédié : bloc après `return` dans `getPieceAm()` (`agent_widget_dialog.js:468-476`), getter
  `baseEurocode` défini deux fois (`:404` et `:490`), `SaleOrder.eurocodeField`/`get eurocode()`
  inutilisés, service `orm` injecté jamais appelé, `onConfirm()` des sous-classes qui ne font
  qu'appeler `super`.
- **L3.5 — Outputs de notebooks (S).** Cookies `XSRF-TOKEN`/`myvsf_session` en clair dans
  `controllers/vsf.ipynb` committé — effacer les outputs.

---

## L4 — Refonte du calcul du prix sur les mécanismes natifs Odoo {#l4}

**Initiative distincte, hors périmètre initial (optimisation UI + transfert), tracée ici à la
demande explicite du métier.** Constat partagé : la cascade actuelle (`prix_devis/README.md`)
n'utilise aucun mécanisme de prix natif Odoo — ni coût, ni liste de prix (`product.pricelist`),
ni règle de tarification. C'est une suite de produits/sommes sur des champs Studio recopiés à
la main (4 prix VSF bruts × 1,76, ×1,704545455, forfaits de pose en dur par pièce/difficulté,
×1,085…), portée entièrement par `crm.lead` et recopiée en lecture sur `sale.order`. Au-delà de
la question de conformité, la cartographie `prix_devis` documente déjà plusieurs incohérences
internes à cette cascade (deux `switch` dupliqués, deux référentiels de temps de pose non
connectés — voir `prix_devis/README.md#anomalies--points-de-vigilance`).

**Cible.** Reconstruire le prix avec les mécanismes Odoo standard :
- **coût** (`standard_price` sur `product.product`, alimenté par le prix d'achat VSF réel —
  ce que fait déjà correctement `/createProduct`, cf. [L1.5](#l15)) ;
- **prix de revient/vente par liste de prix** (`product.pricelist`, règles par catégorie de
  produit ou attribut plutôt que par branchement `selection`) ;
- le forfait de pose (aujourd'hui un montant en dur par couple pièce/difficulté) porté par un
  produit/service dédié avec son propre prix, plutôt qu'une addition câblée dans un `compute`
  Studio.

**Pourquoi c'est un chantier séparé, pas une tâche de L1.** L'ampleur : plus de 9 000 pistes
utilisent déjà la cascade actuelle en production côté saisie manuelle, la logique touche
`expected_revenue` (donc le forecast CRM) via 3 `base.automation`, et une bascule mal négociée
change des prix déjà validés par des commerciaux sur des dossiers en cours. Ce chantier a
besoin de sa propre cartographie (extension de `prix_devis/`, avec le contenu `base.automation`
de [L0.4](#l04)), d'une maquette de règles de pricelist validée avec le métier, et d'un plan de
bascule (double calcul en parallèle avant coupure de l'ancien, a minima).

**Interaction avec L1.3.** Tant que L4 n'est pas fait, l'écriture de `VSF - Prix VIT` décrite en
[L1.3](#l13) reste la meilleure option disponible pour alimenter la cascade existante avec une
donnée fiable — elle devient un correctif intérimaire, pas la solution finale : une fois L4 en
place, le prix ne devrait plus dépendre de champs Studio recopiés mais du coût produit et des
règles de pricelist.

**Prochaine étape concrète, si ce chantier démarre** : atelier avec le métier pour lister les
règles de tarification réelles (ce que les forfaits en dur de `prix_op_ht` encodent
aujourd'hui : pièce × difficulté), et les traduire en règles de `product.pricelist` — avant
tout code.

---

## 5. Hors périmètre (assumé)

- **Renommer la route `/rbm_agent/getVehiculeMeta`** (coquille `rbm`) : après L1.1 elle n'est
  plus appelée que depuis un seul endroit ; le renommage devient trivial et pourra se faire
  à ce moment-là, pas avant.
- **Isoler la session portail par utilisateur** : impossible, un seul identifiant X'Glass/VSF
  pour l'entreprise. Le verrou de sérialisation reste la bonne réponse (cf.
  [état des lieux §5](etat-des-lieux.md)).
- **Refonte visuelle complète du widget** : L2.1 structure l'existant avec les classes déjà
  chargées par Odoo. Une vraie refonte (SCSS dédié, composants réutilisables) n'est justifiée
  qu'après L1, quand le parcours produira de la donnée.
- **Supprimer les champs `[Obsolète]` de `crm.lead`** : ~60 champs concernés sur l'instance.
  [L0.4](#l04) les **inventorie** (pour éviter de les recibler par erreur), mais leur
  suppression reste un chantier de nettoyage Studio distinct.
