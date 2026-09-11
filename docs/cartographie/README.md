# Cartographie des champs Studio — instance RPBM

> **Statut.** Cette cartographie est le releve historique du 2026-07-25. Le cadre
> reproductible pour les prochains snapshots, l'inventaire et le rafraichissement est
> decrit dans l'[audit Odoo Studio](../../.paradigme/audits/rpbm-preprod/README.md).
> Un snapshot complet en lecture seule est desormais disponible localement ; la documentation
> versionnable de l'audit a ete regeneree depuis ce snapshot.

Cartographie de l'**instance** `rpbm-pre-prod` (Odoo 17), distincte de la documentation du
**module** (`rpbm_agent/docs/`). Objectif : savoir, champ par champ, quelle donnée métier
porte quel `x_studio_*`, pour que le widget **fiabilise la série de champs existante** au lieu
d'en créer une parallèle (objectif d'assainissement — cf.
[roadmap L0.4](../../rpbm_agent/docs/roadmap.md)).

Établie le 2026-07-25 en lecture seule via la skill `paradigme-mcp` (profil `rpbm-preprod`)
sur `ir.model.fields`, `base.automation`, `ir.actions.server`, plus le relevé live du parcours
widget (L0.1). Les tableaux d'inventaire sont **générés** depuis l'instance (non transcrits à
la main) pour rester exhaustifs.

## Documents

- [`crm-lead.md`](crm-lead.md) — inventaire exhaustif des **265** champs `x_studio_*` de
  `crm.lead`, avec statut et taux de remplissage (champs décisionnels).
- [`sale-order.md`](sale-order.md) — les **87** champs `x_studio_*` de `sale.order`
  (+ `sale.order.line`) ; presque tous `related` vers l'opportunité.
- [`automatisations.md`](automatisations.md) — les 7 `base.automation`/`ir.actions.server` du
  périmètre (Revenu Espéré, Parrainage, Audit, « Tarif x glass »).
- [`calques-mapping.md`](calques-mapping.md) — correspondance calque X'Glass → « Pièce
  concernée » (prérequis L1.2.b), sur libellés réels.
- [`prix-devis/`](prix-devis/README.md) — **cartographie du prix de vente** (migrée depuis
  `Jobs/`, format de référence) : cascade complète `crm.lead` → `sale.order`, formules
  `compute`, vérification numérique sur un devis réel, anomalies.
- [`reconciliation-stock-rpbm-agent.md`](reconciliation-stock-rpbm-agent.md) — analyse croisée
  entre le module `rpbm_agent` et la migration stock (`Jobs/Gestion Stock/`) : conventions
  divergentes sur `product.product` (clé `default_code`, catégorie, coût), hiérarchie de
  priorités et questions client à trancher avant que les deux tournent en production
  simultanément.

## Légende des statuts (`crm-lead.md`)

| Statut | Sens |
|---|---|
| `cible widget` | Champ que le widget écrit aujourd'hui (immatriculation, véhicule, catégorie, base eurocode). |
| `cible widget (proposé)` | Champ que le widget **devrait** écrire (L1.2.b / L1.3). `⚠` = a un effet tarifaire. |
| `à trancher` / `candidat` | Cible d'écriture encore à décider (ex. `refConstructeur`). |
| `cascade prix` | Entrée de la cascade de calcul du prix (voir [prix-devis](prix-devis/README.md)). |
| `lecture seule` | `readonly`/calculé — **ne jamais écrire**. |
| `calculé` | `compute` Studio (dérivé, non saisi). |
| `obsolète` | Libellé `[Obsolète]`/`OBSOLETE`/`SUPPRIMER` — ne jamais recibler. |
| `hors périmètre` | Champ métier existant sans lien avec le widget (assurance, parrainage, photos, attributs vitrage…). |

## Synthèse — décisions de ciblage du widget

Ce que le widget écrit aujourd'hui vs ce qu'il devrait écrire, avec le taux de remplissage
réel (base : 10 364 pistes) qui montre où est la donnée métier :

| Donnée | Champ cible `crm.lead` | Rempli | Statut widget |
|---|---|---:|---|
| Immatriculation | `x_studio_field_NVioD` | 97 % | écrit ✓ |
| Véhicule lié | `x_studio_vehicle_id` | **0 %** | écrit, mais bloqué par [L1.0](../../rpbm_agent/docs/roadmap.md#l10) |
| Catégorie X'Glass (libellé exact) | `x_studio_categorie_xglass` | **0 %** | écrit (traçabilité) |
| **Pièce concernée** | `x_studio_field_eENQz` | 96 % | **à écrire** (L1.2.b) — pilote le prix |
| Base Eurocode | `x_studio_field_ORIyy` | 88 % | écrit ✓ |
| **Eurocode Complet** | `x_studio_field_NwRik` | 91 % | **à écrire** (L1.3) |
| **VSF Désignation** | `x_studio_field_j8eh3` | 76 % | **à écrire** (L1.3), hors prix |
| VSF Qté Dispo | `x_studio_field_BKtpw` | 71 % | à écrire (L1.3) |
| **VSF Prix VIT** | `x_studio_field_F0zf7` | 99 % | à écrire (L1.3) — **⚠ entre dans le prix** |
| Réf. constructeur | `x_studio_field_e6OAd` (43×) *ou* `x_studio_field_MNzfJ` (3411×) | — | **à trancher** (L1.3) |

**Points saillants révélés par les taux de remplissage :**

1. **Le désalignement de cible est chiffré.** Les champs que le widget écrit
   (`x_studio_vehicle_id`, `x_studio_categorie_xglass`) sont à **0 %** ; les champs que le
   métier remplit à la main pour la même information (« Pièce concernée » 96 %, « Eurocode
   Complet » 91 %, « VSF Désignation » 76 %) ne sont **pas** ceux que le widget cible. C'est
   tout l'enjeu de L1.2/L1.3.

2. **`refConstructeur` : mauvaise cible pressentie.** `x_studio_field_e6OAd` « Autre
   Référence » n'est rempli que **43 fois** ; `x_studio_field_MNzfJ` « Code Constructeur »
   (3 411 fois) est le champ réellement utilisé pour cette donnée. À trancher en L1.3 avant de
   coder.

3. **Effet tarifaire à surveiller.** `x_studio_field_F0zf7` (VSF Prix VIT) est rempli sur
   **99 %** des pistes et entre dans `VSF - Prix RV = (VIT+JT1+JT2+JT3)×1,76`, qui pilote le
   prix de vente quand « Pièce Trouvée » vaut `VSF`/`À trouver` (10 340 pistes, ~100 %). Le
   widget qui écrit ce champ **change le prix facturé** — voir [prix-devis](prix-devis/README.md)
   et l'avertissement L1.3.

4. **Cascade de prix sans mécanisme natif.** Aucun des prix ne passe par une liste de prix
   Odoo : tout est en champs Studio `compute` recopiés à la main. C'est le périmètre de
   [L4](../../rpbm_agent/docs/roadmap.md#l4).

## `sale.order` : la donnée vit sur l'opportunité

68 des 87 champs `x_studio_*` de `sale.order` sont des `related` **stockés** vers
`opportunity_id.*` (17 propres au devis). Écrire ces champs depuis le devis mute l'opportunité
liée, et est un no-op si `opportunity_id` est vide (38 devis sur 7 106). C'est la cause (B)/(D)
de la roadmap et la raison de [L1.4](../../rpbm_agent/docs/roadmap.md#l14) et
[L1.2.a](../../rpbm_agent/docs/roadmap.md#l12) (aligner `x_studio_vehicle_id`/
`x_studio_categorie_xglass` sur cette même convention `related`). Détail dans
[sale-order.md](sale-order.md).

## Anomalies relevées au passage

- **Champs dupliqués** : `x_studio_prix_op_ht` / `x_studio_prix_op_ht_1` (« Prix OP (HT) » /
  « Prix OP HT »), `x_studio_field_0RYCW` / `x_studio_marge_brute_` (« Marge Brute (€) » ×2),
  `x_studio_field_OMuUZ` / `x_studio_taux_marque_`. Doublons Studio à rationaliser (hors
  périmètre widget).
- **Coquille de condition** : l'automatisation « Revenu Espéré (RPB) » filtre sur
  `"PRix RPB (TTC)"` (double majuscule) — cf. [automatisations.md](automatisations.md).
- **54 champs obsolètes** encore présents (`[Obsolète]`/`OBSOLETE`/`SUPPRIMER`) — nettoyage
  Studio distinct.
