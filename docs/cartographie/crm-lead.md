# Cartographie — champs Studio `crm.lead`

> Généré depuis `ir.model.fields` de l'instance `rpbm-pre-prod` le 2026-07-25 (voir [README](README.md) pour la méthode et la légende des statuts). **265** champs `x_studio_*` au total : 47 décisionnels, 54 obsolètes, 164 hors périmètre widget.

Taux de remplissage mesurés uniquement sur les champs décisionnels (base : 10364 pistes). `ro`=readonly, `calc`=compute Studio.

## Champs décisionnels (cibles widget, prix, lecture seule)

| Champ | Libellé | Type | Relation | Related → | store | ro | calc | Rempli (/10364) | Statut |
|---|---|---|---|---|:-:|:-:|:-:|---|---|
| `x_studio_chque_cadeaux_rad` | Chèque cadeaux RAD | float |  |  | o |  | o |  | calculé |
| `x_studio_field_MNzfJ` | Code Constructeur | char |  |  | o |  |  | 3411 (33%) | candidat (L1.3) |
| `x_studio_difficult_montage` | Difficulté Montage | selection |  |  | o |  |  | 6188 (60%) | cascade prix |
| `x_studio_field_40VX7` | VSF - Prix JT1 | float |  |  | o |  |  | 9938 (96%) | cascade prix |
| `x_studio_field_JGkRK` | RV HT (Concess) | float |  |  | o |  |  |  | cascade prix |
| `x_studio_field_O1pEU` | Prix Proposé (TTC) | float |  |  | o |  |  | 9943 (96%) | cascade prix |
| `x_studio_field_W0dYq` | RV HT (Stock) | float |  |  | o |  |  |  | cascade prix |
| `x_studio_field_b515W` | VSF - Prix JT2 | float |  |  | o |  |  | 9857 (95%) | cascade prix |
| `x_studio_field_moZrn` | RV HT (MPB) | float |  |  | o |  |  |  | cascade prix |
| `x_studio_field_o53Jo` | VSF - Prix JT3 | float |  |  | o |  |  | 9853 (95%) | cascade prix |
| `x_studio_field_yBqOW` | Prix XGlass (TTC) | float |  |  | o |  |  | 10227 (99%) | cascade prix |
| `x_studio_field_z5iaE` | Pièce Trouvée | selection |  |  | o |  |  | 10340 (100%) | cascade prix |
| `x_studio_prix_retenu` | Prix Retenu | selection |  |  | o |  |  | 6744 (65%) | cascade prix |
| `x_studio_categorie_xglass` | Catégorie X'Glass | char |  |  | o |  |  | 0 (0%) | cible widget |
| `x_studio_field_NVioD` | Immatriculation | char |  |  | o |  |  | 10096 (97%) | cible widget |
| `x_studio_field_ORIyy` | Base Eurocode | char |  |  | o |  |  | 9117 (88%) | cible widget |
| `x_studio_vehicle_id` | Véhicule | many2one | fleet.vehicle |  | o |  |  | 0 (0%) | cible widget |
| `x_studio_field_BKtpw` | VSF - Qté Dispo | char |  |  | o |  |  | 7360 (71%) | cible widget (proposé) |
| `x_studio_field_NwRik` | Eurocode (Complet) | char |  |  | o |  |  | 9394 (91%) | cible widget (proposé) |
| `x_studio_field_eENQz` | Pièce concernée | selection |  |  | o |  |  | 9980 (96%) | cible widget (proposé) |
| `x_studio_field_j8eh3` | VSF - Désignation | char |  |  | o |  |  | 7921 (76%) | cible widget (proposé) |
| `x_studio_field_F0zf7` | VSF - Prix VIT | float |  |  | o |  |  | 10268 (99%) | cible widget (proposé) ⚠ |
| `x_studio_assurance_dclaration_de_sinistre` | Nouveau Champ associé | char |  | x_studio_field_ZiY2J.x_studio_dclaration_de_sinistre_filename | o | o |  |  | lecture seule |
| `x_studio_dclaration_de_sinistre` | Déclaration de sinistre | binary |  | x_studio_field_ZiY2J.x_studio_dclaration_de_sinistre |  | o |  |  | lecture seule |
| `x_studio_field_0RYCW` | Marge Brute (€) | float |  |  | o | o | o |  | lecture seule |
| `x_studio_field_24zWQ` | VSF - Prix RV | float |  |  | o | o | o |  | lecture seule |
| `x_studio_field_5VGQD` | TOTAL Cadeaux | float |  |  | o | o | o |  | lecture seule |
| `x_studio_field_BAiIX` | Prix Proposé (HT) | float |  |  | o | o | o |  | lecture seule |
| `x_studio_field_HJIi5` | Prix XGlass (HT) | float |  |  | o | o | o |  | lecture seule |
| `x_studio_field_OMuUZ` | Taux de Marque (%) | float |  |  | o | o | o |  | lecture seule |
| `x_studio_field_QKmmB` | Prix RPB (HT) | float |  |  | o | o | o |  | lecture seule |
| `x_studio_field_U2Wuh` | Dernière Modif | datetime |  | x_studio_modifs.x_studio_date_modification | o | o |  |  | lecture seule |
| `x_studio_field_gUd4S` | Prix RPB (TTC) | float |  |  | o | o | o | 9664 (93%) | lecture seule |
| `x_studio_field_h06UD` | RV Pièce | float |  |  | o | o | o |  | lecture seule |
| `x_studio_marge_brute_` | Marge Brute (€) | float |  |  | o | o | o |  | lecture seule |
| `x_studio_montant_montage_pour_autres_vitrages` | Montant Montage (pour "Autres Vitrages") | float |  |  | o | o | o |  | lecture seule |
| `x_studio_prix_achat_ht` | Prix Achat (HT) | float |  |  | o | o | o |  | lecture seule |
| `x_studio_prix_op_ht` | Prix OP (HT) | float |  |  | o | o | o |  | lecture seule |
| `x_studio_prix_op_ht_1` | Prix OP HT | float |  |  | o | o | o |  | lecture seule |
| `x_studio_prix_pice_seule_ht` | Prix Pièce Seule (HT) | float |  |  | o | o | o |  | lecture seule |
| `x_studio_prix_pose_ttc` | Prix + Pose (TTC) | float |  |  | o | o | o |  | lecture seule |
| `x_studio_prix_rv_coef` | Prix RV + Coef | float |  |  | o | o | o |  | lecture seule |
| `x_studio_prix_rv_ht` | Prix RV (HT) | float |  |  | o | o | o |  | lecture seule |
| `x_studio_procedure_assurance` | procedure_assurance | html |  | x_studio_field_ZiY2J.x_studio_procedure_assurance |  | o |  |  | lecture seule |
| `x_studio_revenu_parrain_ttc` | Revenu Parrain € TTC | float |  |  | o | o |  |  | lecture seule |
| `x_studio_taux_marque_` | Taux Marque (%) | float |  |  | o | o | o |  | lecture seule |
| `x_studio_field_e6OAd` | Autre Référence | char |  |  | o |  |  | 43 (0%) | à trancher (L1.3) |

## Champs obsolètes

Marqués `[Obsolète]`/`OBSOLETE`/`SUPPRIMER` dans leur libellé — **à ne jamais recibler**. Leur suppression est un chantier de nettoyage Studio distinct (hors périmètre widget).

| Champ | Libellé | Type |
|---|---|---|
| `x_studio_field_2Xgrz` | OBSOLETE - New Integer number | integer |
| `x_studio_field_3lz5k` | LAT1 - Avant (OBSOLETE) | boolean |
| `x_studio_field_4d30L` | LAT2 - Mobile (OBSOLETE) | boolean |
| `x_studio_field_4uP4w` | LAT2 - Droite (OBSOLETE) | boolean |
| `x_studio_field_5EjkH` | OBSOLETE - Photos | selection |
| `x_studio_field_6300P` | PB - Caméra (LDW) (OBSOLETE) | boolean |
| `x_studio_field_7zPDk` | PB - Acoustique (OBSOLETE) | boolean |
| `x_studio_field_836zR` | LUN -  (OBSOLETE) | boolean |
| `x_studio_field_8e4qn` | LAT1 - Mobile (OBSOLETE) | boolean |
| `x_studio_field_Ag1KV` | LAT1 - Arrière (OBSOLETE) | boolean |
| `x_studio_field_B0nM2` | AC - Description (OBSOLETE) | char |
| `x_studio_field_BUgKL` | PB - Capteur Lumière (OBSOLETE) | boolean |
| `x_studio_field_EmI75` | LUN - 3e feu stop (OBSOLETE) | boolean |
| `x_studio_field_F4dU3` | Assuré BDG (OBSOLETE) | boolean |
| `x_studio_field_Fr3mt` | LAT2 - Feuilletée (OBSOLETE) | boolean |
| `x_studio_field_HYt6X` | OBSOLETE - LAT1 - Autres Infos... | char |
| `x_studio_field_Lfw0z` | OBSOLETE - LAT2 - Autres Infos... | char |
| `x_studio_field_MZHQA` | OBSOLETE - Lieu sinistre | char |
| `x_studio_field_NbY5O` | Champs Obsolètes V1 | boolean |
| `x_studio_field_OFlHk` | OBSOLETE - LAT1 - Autres infos... | char |
| `x_studio_field_PIpBC` | OBSOLETE - PB - Capteur Pluie | selection |
| `x_studio_field_QMu6M` | PB - Athermique (OBSOLETE) | boolean |
| `x_studio_field_Rg7Rm` | LAT2 - Gauche (OBSOLETE) | boolean |
| `x_studio_field_RxDC3` | LUN - Surteintée (OBSOLETE) | boolean |
| `x_studio_field_SNgqA` | LUN - Antenne (OBSOLETE) | boolean |
| `x_studio_field_TCPoy` | OBSOLETE - PB - Capteur Lumière | selection |
| `x_studio_field_UyWPL` | Obsolète - Parrain - Suppr | boolean |
| `x_studio_field_V71yf` | SUPPRIMER - New Text | char |
| `x_studio_field_ZBilT` | OBSOLETE - New Text | char |
| `x_studio_field_awL8Q` | OBSOLETE - LUN - Autres infos... | char |
| `x_studio_field_dQm1W` | LAT2 - Custode (OBSOLETE) | boolean |
| `x_studio_field_eYa9z` | LAT2 - Avant (OBSOLETE) | boolean |
| `x_studio_field_hlz9W` | LAT2 - Arrière (OBSOLETE) | boolean |
| `x_studio_field_iLu6G` | OBSOLETE - Nb de portes | char |
| `x_studio_field_jACgh` | LAT1 - Surteintée (OBSOLETE) | boolean |
| `x_studio_field_jiYTN` | LAT2 - Surteintée (OBSOLETE) | boolean |
| `x_studio_field_jnovm` | LAT1 - Déflecteur (OBSOLETE) | boolean |
| `x_studio_field_k6YtU` | OBSOLETE - Prix Appliqué | selection |
| `x_studio_field_lGnmo` | OBSOLETE - New Text | char |
| `x_studio_field_mkG05` | LAT2 - Déflecteur (OBSOLETE) | boolean |
| `x_studio_field_mpVYT` | Montant Franchise (OBSOLETE) | float |
| `x_studio_field_nUk8g` | LAT1 - Custode (OBSOLETE) | boolean |
| `x_studio_field_oNfEq` | PB - Chauffant (OBSOLETE) | boolean |
| `x_studio_field_opJfK` | LUN - Chauffante (OBSOLETE) | boolean |
| `x_studio_field_oyMzo` | PB - Fenêtre VIN (OBSOLETE) | boolean |
| `x_studio_field_pQuls` | SUPPRIMER - New Text | char |
| `x_studio_field_pa97h` | OBSOLETE - LAT2 - Autres infos | char |
| `x_studio_field_sBBV7` | LAT1 - Gauche (OBSOLETE) | boolean |
| `x_studio_field_uTzqa` | LAT1 - Feuilletée (OBSOLETE) | boolean |
| `x_studio_field_ucQSm` | LAT1 - Droite (OBSOLETE) | boolean |
| `x_studio_field_vutd3` | OBSOLETE - LUN - Autres Infos... | char |
| `x_studio_field_x3Pb9` | OBSOLETE - LUN - Autres Infos... (Recréé en CHAR) | char |
| `x_studio_field_z6LRc` | PB - Capteur Pluie (OBSOLETE) | boolean |
| `x_studio_field_z9uvM` | New Related Field OBSOLETE | char |

## Autres champs métier (hors périmètre widget)

Champs Studio existants sans lien avec le widget X'Glass/VSF (assurance, parrainage, photos, attributs vitrage LAT/LUN/PB, contacts, etc.). Listés pour exhaustivité.

| Champ | Libellé | Type | Relation | Related → | store | ro | calc |
|---|---|---|---|---|:-:|:-:|:-:|
| `x_studio_audit` | Audit | one2many | x_audit |  | o |  |  |
| `x_studio_audit_1` | Audit | one2many | x_audit |  | o |  |  |
| `x_studio_char_field_UXUeY` | New Texte | char |  |  | o |  |  |
| `x_studio_circonstance` | Circonstance | selection |  |  | o |  |  |
| `x_studio_date_field_RSjsp` | Date Début contrat | date |  |  | o |  |  |
| `x_studio_date_fin_contrat` | Date Fin contrat | datetime |  |  | o |  |  |
| `x_studio_dclaration_de_sinistre_filename` | Filename for x_studio_binary_field_1ug_1jkl8tel7 | char |  |  | o |  |  |
| `x_studio_eurocode_joint` | Eurocode (Joint) | char |  |  | o |  |  |
| `x_studio_field_0pnW0` | LAT1 - Mobile | selection |  |  | o |  |  |
| `x_studio_field_0qsxq` | PAR - NOM | char |  | x_studio_field_F0vnM.x_studio_field_4jLUL | o |  |  |
| `x_studio_field_37HTF` | Date RDV | datetime |  |  | o |  |  |
| `x_studio_field_3lm5n` | Validation Pièce | text |  |  | o |  |  |
| `x_studio_field_3qLzV` | LUN - Porte battante | selection |  |  | o |  |  |
| `x_studio_field_40Jkn` | LUN - Autres Infos... | text |  |  | o |  |  |
| `x_studio_field_5QedQ` | Date Clôture | date |  |  | o |  |  |
| `x_studio_field_6A1kb` | AP1 - Description | text |  |  | o |  |  |
| `x_studio_field_7Wlsi` | Photos Voiture | many2one | res.partner |  | o |  |  |
| `x_studio_field_7kJv8` | Concession | char |  |  | o |  |  |
| `x_studio_field_8Hh1Z` | LAT1 - Déflecteur | selection |  |  | o |  |  |
| `x_studio_field_8MDL3` | LAT1 - Arrière | selection |  |  | o |  |  |
| `x_studio_field_8NaTF` | PB - Bandeau | char |  |  | o |  |  |
| `x_studio_field_9JcOl` | N° Dossier | char |  |  | o |  |  |
| `x_studio_field_9Xit2` | BEG - Tailles | char |  |  | o |  |  |
| `x_studio_field_AKH5W` | LAT2 - Mobile | selection |  |  | o |  |  |
| `x_studio_field_AmOY7` | PB - Capteur Lumière | selection |  |  | o |  |  |
| `x_studio_field_BQlO1` | LUN -  Trou BEG | selection |  |  | o |  |  |
| `x_studio_field_BepEe` | LUN - Antenne | selection |  |  | o |  |  |
| `x_studio_field_CI8DO` | PB - Acoustique | selection |  |  | o |  |  |
| `x_studio_field_DdQGC` | Photo 4 | binary |  |  | o |  |  |
| `x_studio_field_DyEho` | Contact Assurance | many2one | res.partner |  | o |  |  |
| `x_studio_field_Eh6Wd` | Date 1ère MEC | char |  |  | o |  |  |
| `x_studio_field_EpEjp` | Montant Franchise | char |  |  | o |  |  |
| `x_studio_field_F0CDq` | LAT2 - Avant | selection |  |  | o |  |  |
| `x_studio_field_F0vnM` | Parrain | many2one | res.partner |  | o |  |  |
| `x_studio_field_FAbEi` | Assurance | many2one | res.partner |  | o |  |  |
| `x_studio_field_FMYUX` | Jetons Lavage | float |  |  | o |  |  |
| `x_studio_field_FTs4T` | LAT2 - Déflecteur | selection |  |  | o |  |  |
| `x_studio_field_FZ6qM` | Autre... | char |  |  | o |  |  |
| `x_studio_field_Foanx` | Autres Cadeaux | float |  |  | o |  |  |
| `x_studio_field_Fygrk` | Photos (Support) | char |  |  | o |  |  |
| `x_studio_field_GURVO` | PB - Athermique | selection |  |  | o |  |  |
| `x_studio_field_GkDyv` | LAT1 - Autres Infos... | text |  |  | o |  |  |
| `x_studio_field_H5wgh` | Stock | char |  |  | o |  |  |
| `x_studio_field_H8pVV` | AC - Note Contact | text |  | x_studio_field_iPWD0.x_studio_field_xXpup | o |  |  |
| `x_studio_field_Hkz1X` | AC2 - NOM | char |  | x_studio_field_nuhyT.x_studio_field_4jLUL | o |  |  |
| `x_studio_field_HvuBq` | Photo 2 | binary |  |  | o |  |  |
| `x_studio_field_HyapV` | PB - Fenêtre VIN | selection |  |  | o |  |  |
| `x_studio_field_K7uQf` | Documents (CG / CV) | many2one | res.partner |  | o |  |  |
| `x_studio_field_KPpqi` | Utilisateurs | many2many | res.users |  | o |  |  |
| `x_studio_field_KyCjB` | Marque | many2one | x_rpbm_marques_voitures |  | o |  |  |
| `x_studio_field_LKreG` | LAT2 - Feuilletée | selection |  |  | o |  |  |
| `x_studio_field_Lc1Vy` | Contact Courtier | many2one | res.partner |  | o |  |  |
| `x_studio_field_Ll7lw` | Contact | many2many | res.partner |  | o |  |  |
| `x_studio_field_NHIDy` | AC - Adresse Email | char |  | x_studio_field_iPWD0.email | o |  |  |
| `x_studio_field_Nj8Ur` | PB - Chauffant | selection |  |  | o |  |  |
| `x_studio_field_O5Bvc` | LAT1 - Gauche | selection |  |  | o |  |  |
| `x_studio_field_OiyXV` | AC - Téléphone 2 | char |  | x_studio_field_iPWD0.mobile | o |  |  |
| `x_studio_field_OwjyT` | Dégâts Apparents | char |  |  | o |  |  |
| `x_studio_field_PZeIB` | TTC AVR (Concess) | float |  |  | o |  |  |
| `x_studio_field_PfJlB` | VIN | char |  |  | o |  |  |
| `x_studio_field_Q6dJN` | LAT1 - Custode | selection |  |  | o |  |  |
| `x_studio_field_QDW3I` | Date Sinistre | date |  |  | o |  |  |
| `x_studio_field_QT66p` | MPB | char |  |  | o |  |  |
| `x_studio_field_QXJvh` | AC2 - Note Contact | text |  | x_studio_field_nuhyT.x_studio_field_xXpup | o |  |  |
| `x_studio_field_S4aLt` | LAT1 - Droite | selection |  |  | o |  |  |
| `x_studio_field_TAhpP` | Énergie Moteur | selection |  |  | o |  |  |
| `x_studio_field_TkrvA` | N° Contrat | char |  |  | o |  |  |
| `x_studio_field_Tv90Y` | LUN - Couleur | char |  |  | o |  |  |
| `x_studio_field_U5320` | BA - Bons N° | char |  |  | o |  |  |
| `x_studio_field_V6JQy` | Courtier (Complet) | many2one | res.partner |  | o |  |  |
| `x_studio_field_VFDsm` | Année Modèle | char |  |  | o |  |  |
| `x_studio_field_VGmbJ` | Comment Connu ? | many2one | x_choix_comment_connu |  | o |  |  |
| `x_studio_field_VP4x6` | LAT2 - Droite | selection |  |  | o |  |  |
| `x_studio_field_WCktL` | LAT 2 - Autres Infos... | text |  |  | o |  |  |
| `x_studio_field_WlA5T` | LAT2 - Gauche | selection |  |  | o |  |  |
| `x_studio_field_Wo7Zd` | PAR - Adresse Email | char |  | x_studio_field_F0vnM.email | o |  |  |
| `x_studio_field_Xasf0` | PB - Capteur Pluie | selection |  |  | o |  |  |
| `x_studio_field_Y42zJ` | Procédure Assurance | char |  |  | o |  |  |
| `x_studio_field_YLQAy` | PAR - Description | char |  |  | o |  |  |
| `x_studio_field_YNMPF` | PAR - Téléphone 2 | char |  | x_studio_field_F0vnM.mobile | o |  |  |
| `x_studio_field_Z1n5A` | Téléphone 2 | char |  | partner_id.mobile | o |  |  |
| `x_studio_field_Z9LBA` | PAR - Prénom | char |  | x_studio_field_F0vnM.x_studio_field_R0T1B | o |  |  |
| `x_studio_field_ZhaeY` | Modèle | many2one | x_rpbm_modeles_voitures |  | o |  |  |
| `x_studio_field_ZiY2J` | Assurance (Simplifié) | many2one | x_rpbm_assurances_simples |  | o |  |  |
| `x_studio_field_ZzJUr` | Autre pièce | selection |  |  | o |  |  |
| `x_studio_field_aIM13` | Kilométrage | char |  |  | o |  |  |
| `x_studio_field_aa28J` | Courtier (Simplifié) | many2one | x_rpbm_courtiers_simples |  | o |  |  |
| `x_studio_field_afB12` | Vitrages | many2many | x_choix_vitrages |  | o |  |  |
| `x_studio_field_bn2AB` | Note Dossier | text |  |  | o |  |  |
| `x_studio_field_c7Qhs` | Remb Franchise | float |  |  | o |  |  |
| `x_studio_field_dk0SG` | AP2 - Description | text |  |  | o |  |  |
| `x_studio_field_eobpV` | AC - NOM | char |  | x_studio_field_iPWD0.x_studio_field_4jLUL | o |  |  |
| `x_studio_field_er8F1` | Autres Infos Voiture... | text |  |  | o |  |  |
| `x_studio_field_f76UV` | AUT - Nature | char |  |  | o |  |  |
| `x_studio_field_fR3ag` | Fichier 1 | binary |  |  | o |  |  |
| `x_studio_field_geWMW` | Photo 1 | binary |  |  | o |  |  |
| `x_studio_field_gx9qx` | RF - Chèque N° | char |  |  | o |  |  |
| `x_studio_field_h6ozm` | LUN - Chauffante | selection |  |  | o |  |  |
| `x_studio_field_h7awX` | Étoiles (RPB) | selection |  |  | o |  |  |
| `x_studio_field_hDbmt` | Code AutoVert | char |  |  | o |  |  |
| `x_studio_field_i8fWl` | Détails Modèle | char |  |  | o |  |  |
| `x_studio_field_iCj85` | BEG | float |  |  | o |  |  |
| `x_studio_field_iHX17` | LAT1 - Feuilletée | selection |  |  | o |  |  |
| `x_studio_field_iLAHF` | LUN - Surteintée | selection |  |  | o |  |  |
| `x_studio_field_iN1IA` | Photo 3 | binary |  |  | o |  |  |
| `x_studio_field_iPWD0` | Autre Contact | many2one | res.partner |  | o |  |  |
| `x_studio_field_iZMhR` | PB - Vérification Pièce | many2many | x_verification_piece |  | o |  |  |
| `x_studio_field_iaEh1` | Photo 6 | binary |  |  | o |  |  |
| `x_studio_field_kylCN` | Validation Client | text |  |  | o |  |  |
| `x_studio_field_lGsdE` | Bons Achat | float |  |  | o |  |  |
| `x_studio_field_lVNsf` | Validation Assurance | text |  |  | o |  |  |
| `x_studio_field_leNsC` | AC - Prénom | char |  | x_studio_field_iPWD0.x_studio_field_R0T1B | o |  |  |
| `x_studio_field_lqqNU` | Photo 5 | binary |  |  | o |  |  |
| `x_studio_field_lwG5T` | LAT1 - Surteintée | selection |  |  | o |  |  |
| `x_studio_field_m66My` | AC2 - Téléphone 1 | char |  | x_studio_field_nuhyT.phone | o |  |  |
| `x_studio_field_mLeJl` | PAR - Téléphone 1 | char |  | x_studio_field_F0vnM.phone | o |  |  |
| `x_studio_field_mnj0C` | AC - Téléphone 1 | char |  | x_studio_field_iPWD0.phone | o |  |  |
| `x_studio_field_mrudZ` | LUN - 3e feu stop | selection |  |  | o |  |  |
| `x_studio_field_nSegr` | AC2 - Adresse Email | char |  | x_studio_field_nuhyT.email | o |  |  |
| `x_studio_field_nTbVk` | LAT1 - Avant | selection |  |  | o |  |  |
| `x_studio_field_njSgx` | Géré par | many2many | res.users |  | o |  |  |
| `x_studio_field_nuhyT` | Autre Contact 2 | many2one | res.partner |  | o |  |  |
| `x_studio_field_oDTKm` | JL - Nb Jetons | char |  |  | o |  |  |
| `x_studio_field_oMQWw` | Stop Rain | float |  |  | o |  |  |
| `x_studio_field_oNlmt` | AP1 - Pièce concernée | many2many | x_choix_autre_vitre |  | o |  |  |
| `x_studio_field_oxqB6` | Lieu Sinistre | many2one | x_rpbm_communes_martinique |  | o |  |  |
| `x_studio_field_p6nvs` | X Studio Field P6Nvs | selection |  |  | o |  |  |
| `x_studio_field_p9rYg` | LAT2 - Custode | selection |  |  | o |  |  |
| `x_studio_field_pBB78` | Circonstances | char |  |  | o |  |  |
| `x_studio_field_pwPpp` | AP2 - Pièce concernée | many2many | x_choix_autre_vitre |  | o |  |  |
| `x_studio_field_qQUMQ` | RV HT (Autre...) | float |  |  | o |  |  |
| `x_studio_field_rJxKm` | Note sur la pièce | text |  |  | o |  |  |
| `x_studio_field_rqN4l` | Fichier 2 | binary |  |  | o |  |  |
| `x_studio_field_s4opL` | Assuré BDG | selection |  |  | o |  |  |
| `x_studio_field_sg0M3` | AC2 - Prénom | char |  | x_studio_field_nuhyT.x_studio_field_R0T1B | o |  |  |
| `x_studio_field_tPEjh` | Contact | many2one | res.partner |  | o |  |  |
| `x_studio_field_txWOU` | LAT2 - Surteintée | selection |  |  | o |  |  |
| `x_studio_field_v79kG` | New Selection | selection |  |  | o |  |  |
| `x_studio_field_vRqqS` | Photos | binary |  |  | o |  |  |
| `x_studio_field_vjVQA` | PB - Autres Infos... | text |  |  | o |  |  |
| `x_studio_field_vn3Ki` | PB - Couleur | char |  |  | o |  |  |
| `x_studio_field_vxA2H` | New Integer number | integer |  |  | o |  |  |
| `x_studio_field_wSD1M` | Documents (Support) | char |  |  | o |  |  |
| `x_studio_field_wycWX` | LAT2 - Arrière | selection |  |  | o |  |  |
| `x_studio_field_xJPqa` | AC2 - Téléphone 2 | char |  | x_studio_field_nuhyT.mobile | o |  |  |
| `x_studio_field_y1iBa` | SR - Immat | char |  |  | o |  |  |
| `x_studio_field_yc0ck` | PB - Caméra (LDW) | selection |  |  | o |  |  |
| `x_studio_field_yp1q1` | IMPORTANT | text |  |  | o |  |  |
| `x_studio_field_zTqd9` | Heure Sinistre | char |  |  | o |  |  |
| `x_studio_je_valide_la_piece` | JE VALIDE LA PIECE | boolean |  |  | o |  |  |
| `x_studio_kilomtrage` | Kilométrage | char |  |  | o |  |  |
| `x_studio_lieu_intervention` | Lieu Intervention | selection |  |  | o |  |  |
| `x_studio_many2many_field_5yh3d` | Attributs Lunette | many2many | x_attributs_lunette |  | o |  |  |
| `x_studio_many2many_field_88dTV` | Attributs Latérales | many2many | x_attributs_laterales |  | o |  |  |
| `x_studio_many2many_field_OIkOP` | Attributs Latérales 2 | many2many | x_attributs_laterales_ |  | o |  |  |
| `x_studio_many2many_field_erJNc` | Attributs Pare Brise | many2many | x_attributs_pare_brise |  | o |  |  |
| `x_studio_modifs` | Modifs | one2many | x_audit |  | o |  |  |
| `x_studio_moyen_1er_contact` | Moyen 1er Contact | selection |  |  | o |  |  |
| `x_studio_one2many_field_NXSnV` | New One2many | one2many | sale.order |  | o |  |  |
| `x_studio_one2many_field_fUe95` | New One2many | one2many | sale.order |  | o |  |  |
| `x_studio_selection_field_QbAz5` | New Sélection | selection |  |  | o |  |  |
| `x_studio_temps_montage_pour_autres_vitrages` | Temps Montage (pour "Autres vitrages") | float |  |  | o |  |  |
| `x_studio_validation_stock` | Validation stock | boolean |  |  | o |  |  |
| `x_studio_y_a_til_un_parrain` | Y a t'il un parrain? | selection |  |  | o |  |  |
