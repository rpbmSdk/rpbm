# Données, paramètres et droits

[RPBM Pricing](../../README.md) › [Documentation](../README.md) › [Manuel technique](README.md) › Données, paramètres et droits

## Fichiers de données

Ordre de chargement du manifeste ([`__manifest__.py:15-23`](../../__manifest__.py)) :
`security/ir.model.access.csv`, `data/rule8_data.xml`, `data/rpbm_colisage_data.xml`, puis les vues (régime,
modèle de devis, achat, colisage).

| Fichier | Contenu | `noupdate` |
|---|---|---|
| [`data/rule8_data.xml`](../../data/rule8_data.xml) | trois paramètres de la règle 8, deux actions serveur | oui (tout le fichier) |
| [`data/rpbm_colisage_data.xml`](../../data/rpbm_colisage_data.xml) | trois paramètres du colisage, action serveur de la reprise | oui |

`noupdate` : une valeur modifiée en base n'est jamais écrasée par une mise à jour du module.

## Paramètres système

*Paramètres › Technique › Paramètres système*, clés `rpbm_pricing.*`. Le code les lit par
[`models/params.py`](../../models/params.py) avec des replis identiques aux données. Règles de lecture
(`params.py:18-52`) : lecture en `sudo` ; valeur absente, le repli ; valeur invalide, le repli et un
avertissement au journal, jamais d'exception (ces lectures tournent aussi dans l'automatisation Studio) ;
virgule décimale acceptée ; booléens `1`, `true`, `yes`, `oui`, `vrai` et `0`, `false`, `no`, `non`, `faux`, vide.

| Clé | Valeur | Effet | Décision qui la fixera |
|---|---|---|---|
| `rpbm_pricing.insurance_coefficient` | `1.5` | coefficient de la règle 8 : prix = barème × coefficient | option FFC (Q-06, Q-12) |
| `rpbm_pricing.price_rounding` | `0` | pas d'arrondi (341,87 donne 512,805) ; `0.01` arrondit au centime (512,81) | Q-12 (P-14 en dépend) |
| `rpbm_pricing.rule8_insurance_only` | `0` | `1` : la règle 8 ne majore plus un dossier hors assurance, dont la ligne garde son `list_price` ; un devis sans opportunité reste majoré | validation du client (P-08) |
| `rpbm_pricing.rule8_original_value` | écrite par la mise en place | valeur d'origine de l'action de la règle 8, réécrite par « restaurer » et à la désinstallation | aucune : ne pas modifier à la main |
| `rpbm_pricing.colisage_min_pieces` | `500` | un colisage est retenu si ses pièces dépassent strictement ce montant | Q-18 |
| `rpbm_pricing.colisage_min_fees` | `629` | … et si ses frais dépassent strictement ce montant | Q-18 |
| `rpbm_pricing.colisage_boat_marchs` | `751102,795714,797088,855133,916930` | MARCH comptées en bateau, en plus de celles dont la référence ou un libellé dit « MARITIME » ou « BATEAU » | Q-18 |

`rule8_original_value` n'est dans aucun fichier : `_rpbm_rule8_install()` l'écrit avant de poser la garde
(`models/sale_order_line_rule8.py:136`).

**Paramètres lus, non créés par le module** : `rpbm_agent.vsf_partner_id` (partenaire VSF, défaut 5708) et
`rpbm_agent.vsf_discount` appartiennent à `rpbm_agent`
([`rpbm_agent/controllers/vsf_config.py:8-10`](../../../rpbm_agent/controllers/vsf_config.py)). Aucune clé de
remise n'est ajoutée ici : l'itération 2 réutilisera `rpbm_agent.vsf_discount` (A-13).

### Effet d'un changement

- **Coefficient et arrondi** : appliqués au prochain calcul d'une ligne (changement du barème ou de la
  quantité). Les devis existants ne sont pas recalculés.
- **Seuils et liste bateau** : non dépendances du calcul. Relancer *Reprendre l'historique*.
- **`rule8_insurance_only = 1`** : change le prix des dossiers hors assurance. À faire valider par le client.

À la désinstallation, les six paramètres créés par les données sont supprimés avec le module (identifiant
externe) ; `rule8_original_value`, écrit par code, reste en base. Voir [Installation](installation.md#désinstaller).

## Actions serveur

| Action | Modèle | Groupe | Rôle |
|---|---|---|---|
| RPBM : activer la garde de la règle 8 | `ir.actions.server` | `base.group_system` | pose la garde |
| RPBM : restaurer la règle 8 d'origine | `ir.actions.server` | `base.group_system` | restaure la valeur d'origine |
| Reprendre l'historique des colisages VSF | `rpbm.colisage` | `purchase.group_purchase_manager` | `action = model._rpbm_action_import_history()` ; lancée par le menu |

Détails : [Garde de la règle 8](regle-8.md#actions-serveur) et [Colisage VSF](colisage.md#reprise-de-lhistorique).

## Menus et vues

Menu racine *Achats › Colisages VSF* (séquence 8, [`views/rpbm_colisage_views.xml:142-148`](../../views/rpbm_colisage_views.xml)) :

| Menu | Groupe | Contenu |
|---|---|---|
| Colisages VSF | acheteur | liste et formulaire |
| Coefficient annuel | acheteur | liste du rapport |
| Reprendre l'historique | responsable des achats | lance l'action serveur |

Autres vues : bandeau jaune et champ « Régime du dossier » sur le devis
([`views/sale_order_regime_views.xml`](../../views/sale_order_regime_views.xml)), champ et colonne « Régime » du
modèle de devis ([`views/sale_order_template_views.xml`](../../views/sale_order_template_views.xml)), colonne
« Mode » des achats ([`views/purchase_order_views.xml`](../../views/purchase_order_views.xml)), champ « Colisage VSF »
de la facture fournisseur (`rpbm_colisage_views.xml:157-160`) et filtre « Facture fournisseur sans colisage »
(`:170-172`), champ de la réception entrante (`:184`).

**Aucun xpath positionnel** sur les formulaires modifiés par Studio. Les seules exceptions sont : `//sheet` du devis et
`//group[@id='header_right_group']/field[@name='partner_bank_id']` de la facture, tous deux nommés.

## Droits

[`security/ir.model.access.csv`](../../security/ir.model.access.csv) :

| Modèle | Acheteur (`purchase.group_purchase_user`) | Responsable (`purchase.group_purchase_manager`) |
|---|---|---|
| `rpbm.colisage`, `rpbm.colisage.dau` | lire, écrire, créer | tous les droits, suppression comprise |
| `rpbm.colisage.year.report` | lire | hérite de l'acheteur (implication de groupes, non vérifiée ici) |

Les champs `rpbm_colisage_id` de la facture et de la réception sont limités à `purchase.group_purchase_user`
(`ATTACH_GROUPS`, [`models/rpbm_colisage.py:15`](../../models/rpbm_colisage.py)). Les vendeurs n'ont donc ni menu
Colisages, ni champ Colisage VSF, ni accès aux montants.

Le module ne crée aucun groupe. Choix pris :

- **Pas de droit pour `account.group_account_invoice`.** Le plan de l'itération 1 le prévoyait ; le code n'a que
  les acheteurs. Le groupe Facturation contient tous les vendeurs en préprod : l'accès comptable attend Q-23.
- **Une validation d'achat en une étape.** Tout `purchase.group_purchase_user` peut confirmer une commande ; il
  ne faut jamais l'accorder à un vendeur.

Qui a quoi, d'après `rpbm_agent` (migration `17.0.260928.3`) : Yan et Mickaël sont responsables des achats ;
Margot et Romain (administrateurs) ont acheteur et responsable ; les autres vendeurs n'ont aucun droit Achats.
`rpbm_agent` donne à tout vendeur (`sales_team.group_sale_salesman`) le groupe `stock.group_stock_user`, qui
suffit à lire les achats liés et les réceptions. Règle métier : `docs/architecture/achats-roles.md` (local).

Voir aussi : [Colisage VSF](colisage.md) · [Garde de la règle 8](regle-8.md)

---
Précédent : [Colisage VSF](colisage.md) · Suivant : [Installation et déploiement](installation.md)
