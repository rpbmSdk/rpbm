# Champs de calcul du prix — `crm.lead`

Tous les champs ci-dessous sont des champs Studio (`x_studio_*`), `store=True`. Le `compute` est reproduit tel que trouvé dans `ir.model.fields` (via MCP, profil `rpbm-preprod`). Beaucoup portent un nom technique généré automatiquement par Studio (`x_studio_field_XXXXX`) qui ne correspond pas à leur libellé — le libellé (`field_description`) est donc systématiquement indiqué.

Organisé par niveau de calcul, du plus bas (saisie manuelle) au plus haut (les 4 champs demandés, recopiés ensuite sur `sale.order` — voir [champs-sale-order.md](champs-sale-order.md)).

## Niveau 0 — entrées manuelles

| Champ technique | Libellé | Type | Rôle |
|---|---|---|---|
| `x_studio_field_z5iaE` | Pièce Trouvée | selection | Origine de la pièce : `À trouver` / `En Stock` / `VSF` / `MPB` / `Concession` / `Autre...` — pilote tous les `switch` de la cascade |
| `x_studio_field_eENQz` | Pièce concernée | selection | `Pare-Brise` / `Lunette arrière` / `Glace Latérale` / `Autre...` |
| `x_studio_difficult_montage` | Difficulté Montage | selection | `Simple` / `Moyen` / `Difficile` |
| `x_studio_field_F0zf7` | VSF - Prix VIT | float | Prix catalogue VSF brut (composant 1/4) |
| `x_studio_field_40VX7` | VSF - Prix JT1 | float | Prix catalogue VSF brut (composant 2/4) |
| `x_studio_field_b515W` | VSF - Prix JT2 | float | Prix catalogue VSF brut (composant 3/4) |
| `x_studio_field_o53Jo` | VSF - Prix JT3 | float | Prix catalogue VSF brut (composant 4/4) |
| `x_studio_field_W0dYq` | RV HT (Stock) | float | Prix de référence si pièce en stock |
| `x_studio_field_JGkRK` | RV HT (Concess) | float | Prix de référence si pièce via concession |
| `x_studio_field_moZrn` | RV HT (MPB) | float | Prix de référence si pièce via MPB |
| `x_studio_field_qQUMQ` | RV HT (Autre...) | float | Prix de référence si origine "Autre" |
| `x_studio_temps_montage_pour_autres_vitrages` | Temps Montage (pour "Autres vitrages") | float | Temps de pose (en heures) pour la branche "Autre..." de la pièce concernée |
| `x_studio_field_EpEjp` | Montant Franchise | char | Utilisé uniquement par le chèque cadeaux (branche annexe, voir plus bas) |

Ces champs sont saisis à la main par l'utilisateur (les prix VSF sont vraisemblablement relevés via le portail VSF, cf. `Jobs/crawler/vsf.py`, sans automatisation qui les écrive directement — aucune `ir.actions.server`/`base.automation` trouvée qui écrit sur ces champs).

## Niveau 1 — agrégats de base

**`x_studio_field_24zWQ`** ("VSF - Prix RV", float) :
```python
lead['x_studio_field_24zWQ'] = lead['x_studio_field_F0zf7']*1.76 + lead['x_studio_field_40VX7']*1.76 + lead['x_studio_field_b515W']*1.76 + lead['x_studio_field_o53Jo']*1.76
```
Somme des 4 prix VSF bruts, coefficient `×1.76` appliqué à chacun.

**`x_studio_montant_montage_pour_autres_vitrages`** ("Montant Montage (pour \"Autres Vitrages\")", float) :
```python
lead['x_studio_montant_montage_pour_autres_vitrages'] = lead['x_studio_temps_montage_pour_autres_vitrages'] * 81
```
Temps (heures) × 81 €/h.

## Niveau 2 — sélection du prix par origine (⚠ logique dupliquée deux fois, voir README)

**`x_studio_field_h06UD`** ("RV Pièce", float) :
```python
if lead.x_studio_field_z5iaE == 'En Stock':    lead['x_studio_field_h06UD'] = lead['x_studio_field_W0dYq']
elif lead.x_studio_field_z5iaE == 'VSF':        lead['x_studio_field_h06UD'] = lead['x_studio_field_24zWQ']
elif lead.x_studio_field_z5iaE == 'Concession': lead['x_studio_field_h06UD'] = lead['x_studio_field_JGkRK']
elif lead.x_studio_field_z5iaE == 'MPB':        lead['x_studio_field_h06UD'] = lead['x_studio_field_moZrn']
elif lead.x_studio_field_z5iaE == 'Autre...':   lead['x_studio_field_h06UD'] = lead['x_studio_field_qQUMQ']
elif lead.x_studio_field_z5iaE == 'À trouver':  lead['x_studio_field_h06UD'] = lead['x_studio_field_24zWQ']
else:                                            lead['x_studio_field_h06UD'] = 0
```

**`x_studio_prix_rv_ht`** ("Prix RV (HT)", float) — même `switch`, mais la branche "En Stock" pointe vers `x_studio_field_h06UD` au lieu de `x_studio_field_W0dYq` directement (résultat identique, un niveau d'indirection en plus) :
```python
if lead.x_studio_field_z5iaE == 'En Stock':    lead['x_studio_prix_rv_ht'] = lead['x_studio_field_h06UD']
elif lead.x_studio_field_z5iaE == 'VSF':        lead['x_studio_prix_rv_ht'] = lead['x_studio_field_24zWQ']
elif lead.x_studio_field_z5iaE == 'Concession': lead['x_studio_prix_rv_ht'] = lead['x_studio_field_JGkRK']
elif lead.x_studio_field_z5iaE == 'MPB':        lead['x_studio_prix_rv_ht'] = lead['x_studio_field_moZrn']
elif lead.x_studio_field_z5iaE == 'Autre...':   lead['x_studio_prix_rv_ht'] = lead['x_studio_field_qQUMQ']
elif lead.x_studio_field_z5iaE == 'À trouver':  lead['x_studio_prix_rv_ht'] = lead['x_studio_field_24zWQ']
else:                                            lead['x_studio_prix_rv_ht'] = 0
```
C'est **`x_studio_prix_rv_ht`** (pas `h06UD`) qui alimente le niveau suivant.

## Niveau 3 — les deux champs "pièce"

**`x_studio_prix_rv_coef`** ("Prix RV + Coef", float) — **= `x_studio_prix_de_la_pice` sur `sale.order`** :
```python
lead['x_studio_prix_rv_coef'] = lead['x_studio_prix_rv_ht'] * 1.704545455
```

**`x_studio_prix_pice_seule_ht`** ("Prix Pièce Seule (HT)", float) — **= même nom sur `sale.order`** :
```python
lead['x_studio_prix_pice_seule_ht'] = lead['x_studio_prix_rv_ht'] * 2
```

## Niveau 4 — prix avec pose (HT)

**`x_studio_prix_op_ht`** ("Prix OP (HT)", float) — **= même nom sur `sale.order`** :
```python
if   pièce=='Pare-Brise'       and difficulté=='Simple':    prix_op_ht = prix_rv_coef + 160
elif pièce=='Pare-Brise'       and difficulté=='Moyen':     prix_op_ht = prix_rv_coef + 180
elif pièce=='Pare-Brise'       and difficulté=='Difficile': prix_op_ht = prix_rv_coef + 250
elif pièce=='Lunette arrière'  and difficulté=='Simple':    prix_op_ht = prix_rv_coef + 70
elif pièce=='Lunette arrière'  and difficulté=='Moyen':     prix_op_ht = prix_rv_coef + 90
elif pièce=='Lunette arrière'  and difficulté=='Difficile': prix_op_ht = prix_rv_coef + 150
elif pièce=='Glace Latérale'   and difficulté in (Simple,Moyen,Difficile): prix_op_ht = prix_rv_coef + 70
elif pièce=='Autre...':                                     prix_op_ht = prix_rv_coef + montant_montage_pour_autres_vitrages
elif prix_rv_coef == 0:                                     prix_op_ht = 0
else:                                                        prix_op_ht = 0
```
Forfait de pose en euros, **en dur** (pas de référence au taux horaire ni à `x_studio_temps_main_oeuvre` — voir anomalie dans le README).

## Niveau 5 — prix final TTC

**`x_studio_prix_pose_ttc`** ("Prix + Pose (TTC)", float) — **= même nom sur `sale.order`** :
```python
lead['x_studio_prix_pose_ttc'] = lead['x_studio_prix_op_ht'] * 1.085
```
Coefficient `×1.085` (8,5 %) — à confirmer avec l'équipe s'il s'agit d'un taux de TVA réduit spécifique ou d'une marge.

## Branche annexe — Chèque cadeaux RAD

**`x_studio_chque_cadeaux_rad`** ("Chèque cadeaux RAD", float) — indépendante de la cascade prix, partage seulement `x_studio_field_eENQz` :
```python
if pièce=='Pare-Brise': chque_cadeaux_rad = 100 - int(montant_franchise)
else:                    chque_cadeaux_rad = 0
```

## Mécanisme aval — sélection du prix retenu et Revenu Espéré

Trois champs indépendants représentent 3 sources de prix possibles pour la Piste :

| Champ technique | Libellé | Origine |
|---|---|---|
| `x_studio_field_gUd4S` | Prix RPB (TTC) | Calculé : `= x_studio_prix_pose_ttc` (ou 0 si celui-ci est nul) — donc dépend de toute la cascade ci-dessus |
| `x_studio_field_yBqOW` | Prix XGlass (TTC) | Manuel, indépendant |
| `x_studio_field_O1pEU` | Prix Proposé (TTC) | Manuel, indépendant |

`x_studio_prix_retenu` ("Prix Retenu", selection parmi les 3 libellés ci-dessus) détermine, via 3 `base.automation` (`trigger=on_create_or_write`, filtrées sur la valeur de `x_studio_prix_retenu`) associées chacune à un `ir.actions.server` (`state=object_write`, `evaluation_type=equation`), la valeur écrite dans le champ natif **`expected_revenue`** (Revenu Espéré) de l'opportunité :

- Retenu = "Prix RPB (TTC)" → `expected_revenue = record.x_studio_field_gUd4S`
- Retenu = "Prix XGlass (TTC)" → `expected_revenue = record.x_studio_field_yBqOW`
- Retenu = "Prix Proposé (TTC)" → `expected_revenue = record.x_studio_field_O1pEU`

Seule la branche "Prix RPB (TTC)" est réellement connectée à la cascade de calcul documentée ici.
