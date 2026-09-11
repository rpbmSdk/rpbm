# Champs de calcul du prix — `sale.order`

Sur `sale.order`, tous ces champs sont des `related` **stockés et en lecture seule** vers `opportunity_id` (la Piste/Opportunité liée). Aucun calcul ne se fait sur `sale.order` lui-même pour le prix — voir [champs-crm-lead.md](champs-crm-lead.md) pour la source réelle des formules.

**Conséquence importante** : si un devis n'a pas de `opportunity_id` renseigné (créé directement, hors parcours CRM), ces 4 champs restent vides/à 0 — le prix n'existe que via l'opportunité.

## Les 4 champs demandés

| Champ `sale.order` | Libellé | Related → `crm.lead` | Remarque |
|---|---|---|---|
| `x_studio_prix_de_la_pice` | Prix Pièce dans l'OP (HT) | `opportunity_id.x_studio_prix_rv_coef` | ⚠ libellé "Prix Pièce dans l'OP" mais pointe vers le champ **"Prix RV + Coef"** — mêmes données, noms différents entre les deux modèles |
| `x_studio_prix_op_ht` | Prix OP (HT) | `opportunity_id.x_studio_prix_op_ht` | nom identique des deux côtés |
| `x_studio_prix_pice_seule_ht` | Prix Pièce Seule (HT) | `opportunity_id.x_studio_prix_pice_seule_ht` | nom identique des deux côtés |
| `x_studio_prix_pose_ttc` | Prix + Pose (TTC) | `opportunity_id.x_studio_prix_pose_ttc` | nom identique des deux côtés — c'est le prix final TTC affiché au client |

## Champs miroirs associés (composants intermédiaires, aussi recopiés sur le devis)

| Champ `sale.order` | Libellé | Related → `crm.lead` |
|---|---|---|
| `x_studio_vsf_prix_vit_1` | VSF - Prix VIT | `opportunity_id.x_studio_field_F0zf7` |
| `x_studio_vsf_prix_jt1_1` | VSF - Prix JT1 | `opportunity_id.x_studio_field_40VX7` |
| `x_studio_vsf_prix_jt2` | VSF - Prix JT2 | `opportunity_id.x_studio_field_b515W` |
| `x_studio_vsf_prix_jt3` | VSF - Prix JT3 | `opportunity_id.x_studio_field_o53Jo` |
| `x_studio_vsf_prix_rv` | VSF - Prix RV | `opportunity_id.x_studio_field_h06UD` |
| `x_studio_vsf_qt_dispo` | VSF - Qté Dispo | `opportunity_id.x_studio_field_BKtpw` |
| `x_studio_vsf_dsignation_1` | VSF - Désignation | `opportunity_id.x_studio_field_j8eh3` |
| `x_studio_rv_ht_stock` | RV HT (Stock) | `opportunity_id.x_studio_field_W0dYq` |
| `x_studio_rv_ht_concess` | RV HT (Concess) | `opportunity_id.x_studio_field_JGkRK` |
| `x_studio_rv_ht_mpb` | RV HT (MPB) | `opportunity_id.x_studio_field_moZrn` |
| `x_studio_rv_autres_ht` | RV Autres (HT) | `opportunity_id.x_studio_field_qQUMQ` |
| `x_studio_ttc_avr_concess` | TTC AVR (Concess) | `opportunity_id.x_studio_field_PZeIB` |
| `x_studio_pice_concerne` | Pièce concernée | `opportunity_id.x_studio_field_eENQz` |
| `x_studio_pice_trouve` | Pièce Trouvée | `opportunity_id.x_studio_field_z5iaE` |
| `x_studio_difficult_montage` | Difficulté Montage | `opportunity_id.x_studio_difficult_montage` |
| `x_studio_je_valide_la_piece` | JE VALIDE LA PIECE | `opportunity_id.x_studio_je_valide_la_piece` |
| `x_studio_related_field_hiT9N` | Chèque cadeaux RAD | `opportunity_id.x_studio_chque_cadeaux_rad` |

Notons que `x_studio_field_h06UD` ("RV Pièce") est recopié sous le libellé "VSF - Prix RV" sur `sale.order` (`x_studio_vsf_prix_rv`), alors que `x_studio_prix_rv_ht` (le champ réellement utilisé par la cascade, voir [champs-crm-lead.md](champs-crm-lead.md#niveau-2--sélection-du-prix-par-origine-⚠-logique-dupliquée-deux-fois-voir-readme)) n'a pas de miroir direct sur `sale.order`.

## Champ indépendant (pas un `related`)

**`x_studio_temps_main_oeuvre`** ("Temps Main Oeuvre", float) — c'est le **seul** champ de calcul de prix qui a sa propre formule directement sur `sale.order` (pas un `related` vers `crm.lead`) :
```python
if   pièce=='Pare-Brise'      and difficulté=='Simple':    temps = 0.982
elif pièce=='Pare-Brise'      and difficulté=='Moyen':     temps = 1.229
elif pièce=='Pare-Brise'      and difficulté=='Difficile': temps = 1.550
elif pièce=='Lunette arrière' and difficulté=='Simple':    temps = 0
elif pièce=='Lunette arrière' and difficulté=='Moyen':     temps = 0.118
elif pièce=='Lunette arrière' and difficulté=='Difficile': temps = 0.859
elif pièce=='Glace Latérale'  and difficulté in (Simple,Moyen,Difficile): temps = 0.60
else: temps = 0
```
Exprime un temps en heures, informatif — **non branché** sur le forfait en euros utilisé par `x_studio_prix_op_ht` (voir README, section anomalies). `x_studio_pice_concerne`/`x_studio_difficult_montage` étant eux-mêmes des `related`, ce champ recalcule localement à partir de valeurs qui viennent quand même de `crm.lead`.
