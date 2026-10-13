# Paramètres

[RPBM Pricing](../README.md) › [Documentation](README.md) › Paramètres

Paramètres système (*Paramètres › Technique › Paramètres système*), clés `rpbm_pricing.*`. Ils sont créés
par des données `noupdate` : une valeur modifiée en base n'est jamais écrasée par une mise à jour du module.
Le code les lit par [`models/params.py`](../models/params.py) avec des replis identiques aux données ; une
valeur absente ou illisible donne le repli (avertissement au journal), jamais une erreur.

| Clé | Valeur | Effet | Décision qui la fixera |
|---|---|---|---|
| `rpbm_pricing.insurance_coefficient` | `1.5` | Coefficient de la règle 8 : prix = barème × coefficient | Option FFC (Q-06, Q-12) |
| `rpbm_pricing.price_rounding` | `0` | Pas d'arrondi de la règle 8 (341,87 → 512,805). `0.01` arrondit au centime (512,81) | Q-12 (P-14 en dépend) |
| `rpbm_pricing.rule8_insurance_only` | `0` | `1` : la règle 8 ne majore plus un dossier hors assurance, dont la ligne garde alors son `list_price` ; un devis sans opportunité reste majoré | Validation du client (P-08 « filtrer par régime ») |
| `rpbm_pricing.rule8_original_value` | écrite par la mise en place | Valeur d'origine de l'action de la règle 8, réécrite par « restaurer » et à la désinstallation | Aucune : ne pas modifier à la main |
| `rpbm_pricing.colisage_min_pieces` | `500` | Un colisage est retenu si ses pièces dépassent strictement ce montant | Q-18 (affinement) |
| `rpbm_pricing.colisage_min_fees` | `629` | … et si ses frais dépassent strictement ce montant | Q-18 (affinement) |
| `rpbm_pricing.colisage_boat_marchs` | `751102,795714,797088,855133,916930` | MARCH comptées en bateau, en plus de celles dont la référence ou un libellé dit « MARITIME » ou « BATEAU » | Q-18 (comment savoir qu'un envoi part en bateau) |

Fichiers de données : [`data/rule8_data.xml`](../data/rule8_data.xml) (les trois premières clés) et
[`data/rpbm_colisage_data.xml`](../data/rpbm_colisage_data.xml) (les trois clés de colisage).
`rule8_original_value` n'est dans aucun fichier : `_rpbm_rule8_install()` l'écrit avant de poser la garde.

## Points d'attention

- **Coefficient et arrondi** s'appliquent au prochain calcul d'une ligne (changement du barème ou de la
  quantité) ; les devis existants ne sont pas recalculés.
- **Seuils et liste bateau du colisage** ne sont pas des dépendances du calcul : après un changement, lancer
  *Achats › Colisages VSF › Reprendre l'historique*, qui recalcule tous les colisages.
- **Filtre de régime** laissé à `0` : l'activer change le prix des dossiers hors assurance (retour au
  `list_price` au lieu du barème × 1,5). À faire valider par le client avant.
- **Paramètres lus, non créés par le module** : `rpbm_agent.vsf_partner_id` (partenaire VSF, utilisé par la
  reprise des colisages) appartient à `rpbm_agent`. Aucune clé de remise ici : l'itération 2 réutilisera
  `rpbm_agent.vsf_discount` (A-13).

Voir aussi : [Règle 8](regle-8.md#paramètres) · [Colisage VSF](colisage.md#paramètres)

---
Précédent : [Documentation](README.md) · Suivant : [Règle 8](regle-8.md)
