# Cartographie — champs Studio `sale.order`

> Généré depuis `ir.model.fields` de `rpbm-pre-prod` le 2026-07-25. **87** champs `x_studio_*`. Convention de l'instance : la donnée métier vit sur `crm.lead` (l'opportunité), `sale.order` la recopie via des `related` **stockés** vers `opportunity_id.*`. Écrire un tel champ depuis le devis mute l'opportunité liée (et est un no-op si `opportunity_id` est vide — cf. roadmap cause (B)/(D) et [L1.4](../../rpbm_agent/docs/roadmap.md)).

Répartition : **68** `related → opportunity_id`, **17** propres au devis, 2 autres related.

| Champ | Libellé | Type | Relation | Related → | store | ro | Statut |
|---|---|---|---|---|:-:|:-:|---|
| `x_studio_ap1_description` | AP1 - Description | text |  | opportunity_id.x_studio_field_6A1kb | o |  | related → crm.lead |
| `x_studio_ap1_pice_concerne` | AP1 - Pièce concernée | char |  | opportunity_id.x_studio_field_oNlmt.x_name | o |  | related → crm.lead |
| `x_studio_assurance_` | Assurance : | char |  | opportunity_id.x_studio_field_ZiY2J.display_name |  | o | related → crm.lead |
| `x_studio_assurances_simples` | Assurances Simples | many2one | x_rpbm_assurances_simples |  | o |  | propre au devis |
| `x_studio_attention_ajouter_un_kit_colle_supplementaire` | ATTENTION AJOUTER UN KIT COLLE SUPPLEMENTAIRE | char |  |  | o |  | propre au devis |
| `x_studio_attributs_pare_brise` | Attributs Pare Brise | char |  | opportunity_id.x_studio_many2many_field_erJNc.x_name | o |  | related → crm.lead |
| `x_studio_autres` | Autres... | char |  | opportunity_id.x_studio_field_FZ6qM | o |  | related → crm.lead |
| `x_studio_avez_vous_imprim_la_dbdg_eurodommages` | Avez-vous imprimé la DBDG Eurodommages? | char |  |  | o |  | propre au devis |
| `x_studio_base_eurocode` | Base Eurocode | char |  | opportunity_id.x_studio_field_ORIyy | o |  | related → crm.lead |
| `x_studio_categorie_xglass` | Catégorie X'Glass | char |  |  | o |  | propre au devis |
| `x_studio_char_field_pFyrM` | New Texte | char |  |  | o |  | propre au devis |
| `x_studio_circonstances_sinistre_` | Circonstances : | char |  | opportunity_id.x_studio_field_pBB78 | o |  | related → crm.lead |
| `x_studio_date_1re_mec` | Date 1ère MEC | char |  | opportunity_id.x_studio_field_Eh6Wd | o |  | related → crm.lead |
| `x_studio_date_sinistre_` | Date sinistre : | date |  | opportunity_id.x_studio_field_QDW3I | o |  | related → crm.lead |
| `x_studio_difficult_montage` | Difficulté Montage | selection |  | opportunity_id.x_studio_difficult_montage | o |  | related → crm.lead |
| `x_studio_dtails_modle` | Détails Modèle | char |  | opportunity_id.x_studio_field_i8fWl | o |  | related → crm.lead |
| `x_studio_email_` | Email : | char |  | opportunity_id.x_studio_field_nSegr | o | o | related → crm.lead |
| `x_studio_email__1` | Email : | char |  | opportunity_id.email_from | o | o | related → crm.lead |
| `x_studio_eurocode_complet` | Eurocode (Complet) | char |  | opportunity_id.x_studio_field_NwRik | o |  | related → crm.lead |
| `x_studio_eurocode_joint` | Eurocode (Joint) | char |  | opportunity_id.x_studio_eurocode_joint | o |  | related → crm.lead |
| `x_studio_immatriculation_` | Immatriculation | char |  | opportunity_id.x_studio_field_NVioD | o |  | related → crm.lead |
| `x_studio_je_valide_la_piece` | JE VALIDE LA PIECE | boolean |  | opportunity_id.x_studio_je_valide_la_piece | o |  | related → crm.lead |
| `x_studio_kilomtrage` | Kilométrage | char |  | opportunity_id.x_studio_kilomtrage | o | o | related → crm.lead |
| `x_studio_kilomtrage_1` | Kilométrage | char |  | opportunity_id.x_studio_field_aIM13 | o |  | related → crm.lead |
| `x_studio_kilomtrage__1` | Kilométrage | char |  |  | o |  | propre au devis |
| `x_studio_lat1_autres_infos` | LAT1 - Autres Infos... | text |  | opportunity_id.x_studio_field_GkDyv | o |  | related → crm.lead |
| `x_studio_lieu_de_sinistre_` | Lieu de sinistre : | char |  | opportunity_id.x_studio_field_oxqB6.x_name | o |  | related → crm.lead |
| `x_studio_lieu_sinistre_` | Lieu Sinistre : | char |  | opportunity_id.x_studio_field_oxqB6.x_name | o |  | related → crm.lead |
| `x_studio_many2many_field_ExOig` | Attributs Latérales | many2many | x_attributs_laterales | opportunity_id.x_studio_many2many_field_88dTV |  |  | related → crm.lead |
| `x_studio_many2many_field_vSplB` | Attributs Lunette | many2many | x_attributs_lunette | opportunity_id.x_studio_many2many_field_5yh3d |  |  | related → crm.lead |
| `x_studio_many2many_field_y5lRT` | Attributs Pare Brise | many2many | x_attributs_pare_brise | opportunity_id.x_studio_many2many_field_erJNc |  |  | related → crm.lead |
| `x_studio_many2one_field_DkgHx` | Modèle d'un véhicule | many2one | x_rpbm_modeles_voitures | opportunity_id.x_studio_field_ZhaeY |  |  | related → crm.lead |
| `x_studio_many2one_field_YLpq6` | Modèle de devis | many2one | sale.order.template |  | o |  | propre au devis |
| `x_studio_many2one_field_iSVlQ` | Modèle de devis | many2one | sale.order.template |  | o |  | propre au devis |
| `x_studio_many2one_field_rP62C` | Marque du véhicule | many2one | x_rpbm_marques_voitures | opportunity_id.x_studio_field_KyCjB |  |  | related → crm.lead |
| `x_studio_many2one_field_xiuBA` | Option Modèle de devis | many2one | sale.order.template.option |  | o |  | propre au devis |
| `x_studio_marque__1` | Marque | char |  |  | o |  | propre au devis |
| `x_studio_modle` | Modèle | char |  | opportunity_id.x_studio_field_ZhaeY.x_name | o |  | related → crm.lead |
| `x_studio_modle_` | Modèle | char |  |  | o |  | propre au devis |
| `x_studio_modle_de_devis_` | Modèle de devis : | many2one | sale.order.template |  | o |  | propre au devis |
| `x_studio_modle_devis_` | Modèle devis : | char |  | sale_order_template_id.name | o | o | related (autre) |
| `x_studio_n_contrat_` | N° Contrat : | char |  | opportunity_id.x_studio_field_TkrvA | o |  | related → crm.lead |
| `x_studio_n_sinistre_` | N° Sinistre : | char |  | opportunity_id.x_studio_field_9JcOl | o |  | related → crm.lead |
| `x_studio_necessite_numero_sinistre` | Necessite numero sinistre | boolean |  | opportunity_id.x_studio_field_ZiY2J.x_studio_necessite_numero_sinistre |  | o | related → crm.lead |
| `x_studio_nergie_moteur` | Énergie Moteur | selection |  | opportunity_id.x_studio_field_TAhpP | o |  | related → crm.lead |
| `x_studio_nom_prnom_client_` | Nom Prénom Client : | char |  | opportunity_id.partner_name | o | o | related → crm.lead |
| `x_studio_note_sur_la_pice` | Note sur la pièce | text |  | opportunity_id.x_studio_field_rJxKm | o |  | related → crm.lead |
| `x_studio_pb_bandeau` | PB - Bandeau | char |  | opportunity_id.x_studio_field_8NaTF | o |  | related → crm.lead |
| `x_studio_pb_couleur` | PB - Couleur | char |  | opportunity_id.x_studio_field_vn3Ki | o |  | related → crm.lead |
| `x_studio_pice_concerne` | Pièce concernée | selection |  | opportunity_id.x_studio_field_eENQz | o |  | related → crm.lead |
| `x_studio_pice_trouve` | Pièce Trouvée | selection |  | opportunity_id.x_studio_field_z5iaE | o |  | related → crm.lead |
| `x_studio_prix_de_la_pice` | Prix Pièce dans l'OP (HT) | float |  | opportunity_id.x_studio_prix_rv_coef | o | o | related → crm.lead |
| `x_studio_prix_op_ht` | Prix OP (HT) | float |  | opportunity_id.x_studio_prix_op_ht | o | o | related → crm.lead |
| `x_studio_prix_pice_seule_ht` | Prix Pièce Seule (HT) | float |  | opportunity_id.x_studio_prix_pice_seule_ht | o | o | related → crm.lead |
| `x_studio_prix_pose_ttc` | Prix + Pose (TTC) | float |  | opportunity_id.x_studio_prix_pose_ttc | o | o | related → crm.lead |
| `x_studio_related_field_33SYr` | LUN - Autres Infos... | text |  | opportunity_id.x_studio_field_40Jkn | o |  | related → crm.lead |
| `x_studio_related_field_5aKdJ` | New Champ lié | char |  | opportunity_id.x_studio_field_eobpV | o | o | related → crm.lead |
| `x_studio_related_field_82G8q` | New Champ lié | char |  | opportunity_id.x_studio_field_ZiY2J.x_name | o | o | related → crm.lead |
| `x_studio_related_field_BVrw9` | New Champ lié | selection |  | opportunity_id.x_studio_field_eENQz | o | o | related → crm.lead |
| `x_studio_related_field_QueKt` | New Champ lié | char |  | opportunity_id.x_studio_field_FAbEi.x_studio_field_vBzC6 | o |  | related → crm.lead |
| `x_studio_related_field_e8sbT` | New Champ lié | char |  | opportunity_id.partner_id.x_studio_field_vBzC6 | o | o | related → crm.lead |
| `x_studio_related_field_f8gTZ` | New Champ lié | boolean |  | analytic_account_id.message_follower_ids.channel_id.message_follower_ids.is_active |  | o | related (autre) |
| `x_studio_related_field_hiT9N` | Chèque cadeaux RAD | float |  | opportunity_id.x_studio_chque_cadeaux_rad | o | o | related → crm.lead |
| `x_studio_related_field_slpsr` | PB - Autres Infos... | text |  | opportunity_id.x_studio_field_vjVQA | o | o | related → crm.lead |
| `x_studio_rv_autres_ht` | RV Autres (HT) | float |  | opportunity_id.x_studio_field_qQUMQ | o | o | related → crm.lead |
| `x_studio_rv_ht_concess` | RV HT (Concess) | float |  | opportunity_id.x_studio_field_JGkRK | o |  | related → crm.lead |
| `x_studio_rv_ht_mpb` | RV HT (MPB) | float |  | opportunity_id.x_studio_field_moZrn | o |  | related → crm.lead |
| `x_studio_rv_ht_stock` | RV HT (Stock) | float |  | opportunity_id.x_studio_field_W0dYq | o |  | related → crm.lead |
| `x_studio_signature_client_` | Signature Client : | binary |  |  | o |  | propre au devis |
| `x_studio_stock` | Stock | char |  | opportunity_id.x_studio_field_H5wgh | o |  | related → crm.lead |
| `x_studio_temps_main_oeuvre` | Temps Main Oeuvre | float |  |  | o | o | propre au devis |
| `x_studio_test_lieu` | test lieu | char |  |  | o |  | propre au devis |
| `x_studio_text_field_yixN6` | New Texte multiligne | text |  |  | o |  | propre au devis |
| `x_studio_tlphone_` | Téléphone : | char |  | opportunity_id.phone | o | o | related → crm.lead |
| `x_studio_tlphone_1_` | Téléphone 1 : | char |  | opportunity_id.x_studio_field_mnj0C | o | o | related → crm.lead |
| `x_studio_tlphone_2_` | Téléphone 2 : | char |  | opportunity_id.x_studio_field_OiyXV | o | o | related → crm.lead |
| `x_studio_ttc_avr_concess` | TTC AVR (Concess) | float |  | opportunity_id.x_studio_field_PZeIB | o |  | related → crm.lead |
| `x_studio_validation_pice` | Validation Pièce | text |  | opportunity_id.x_studio_field_3lm5n | o | o | related → crm.lead |
| `x_studio_vehicle_id` | Véhicule | many2one | fleet.vehicle |  | o |  | propre au devis |
| `x_studio_vin_` | VIN | char |  | opportunity_id.x_studio_field_PfJlB | o |  | related → crm.lead |
| `x_studio_vsf_dsignation_1` | VSF - Désignation | char |  | opportunity_id.x_studio_field_j8eh3 | o |  | related → crm.lead |
| `x_studio_vsf_prix_jt1_1` | VSF - Prix JT1 | float |  | opportunity_id.x_studio_field_40VX7 | o |  | related → crm.lead |
| `x_studio_vsf_prix_jt2` | VSF - Prix JT2 | float |  | opportunity_id.x_studio_field_b515W | o |  | related → crm.lead |
| `x_studio_vsf_prix_jt3` | VSF - Prix JT3 | float |  | opportunity_id.x_studio_field_o53Jo | o |  | related → crm.lead |
| `x_studio_vsf_prix_rv` | VSF - Prix RV | float |  | opportunity_id.x_studio_field_h06UD | o | o | related → crm.lead |
| `x_studio_vsf_prix_vit_1` | VSF - Prix VIT | float |  | opportunity_id.x_studio_field_F0zf7 | o |  | related → crm.lead |
| `x_studio_vsf_qt_dispo` | VSF - Qté Dispo | char |  | opportunity_id.x_studio_field_BKtpw | o |  | related → crm.lead |

## `sale.order.line`

Le champ **`x_studio_prix_x_glass`** est lu par l'automatisation « Tarif x glass » (`Unit Price = x_studio_prix_x_glass × 1.5`) — voir [automatisations](automatisations.md). Pertinent pour [L1.6](../../rpbm_agent/docs/roadmap.md) (ajout de ligne au devis).

| Champ | Libellé | Type | Related → |
|---|---|---|---|
| `x_studio_float_field_Ycdbf` | New Décimal | float |  |
| `x_studio_html_field_hGDum` | New Html | html |  |
| `x_studio_integer_field_5Zssd` | New Entier | integer |  |
| `x_studio_monetary_field_ekm16` | New Monétaire | monetary |  |
| `x_studio_prix_x_glass` | Prix XGlass | float |  |
| `x_studio_related_field_G0sgU` | New Champ lié | float | product_id.taxes_id.amount |
| `x_studio_related_field_NyMTk` | New Champ lié | monetary | order_id.amount_tax |
| `x_studio_related_field_Pb1gS` | New Champ lié | monetary | linked_line_id.price_total |
| `x_studio_related_field_VuH3e` | New Champ lié | selection | product_id.taxes_id.tax_exigibility |
| `x_studio_related_field_azWMB` | New Champ lié | monetary | product_id.purchase_order_line_ids.price_total |
