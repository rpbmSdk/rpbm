# Garde de la règle 8 (IMP-2)

[RPBM Pricing](../README.md) › [Documentation](README.md) › Règle 8

La règle 8 est l'automatisation Studio « Tarif x glass » (`base.automation` 8 en préprod) : quand le Prix
X'Glass d'une ligne de devis change et n'est pas nul, son action (`ir.actions.server` 1510, du même nom)
écrit `price_unit = Prix X'Glass × 1,5`. Le module ne remplace pas cette automatisation : il en garde
l'action, sans toucher au domaine ni au déclencheur.

Code : [`models/sale_order_line_rule8.py`](../models/sale_order_line_rule8.py) ; constantes Studio :
[`models/legacy_fields.py`](../models/legacy_fields.py) ; données :
[`data/rule8_data.xml`](../data/rule8_data.xml) ; tests : [`tests/test_rule8.py`](../tests/test_rule8.py).

## La garde

La valeur de l'action passe de `record.x_studio_prix_x_glass*1.5` à :

```python
record.rpbm_rule8_price if 'rpbm_rule8_price' in record._fields else record.x_studio_prix_x_glass*1.5
```

- `safe_eval` accepte l'expression : il ne refuse que les noms contenant `__` et quelques attributs de frame
  (`odoo/tools/safe_eval.py`, `assert_no_dunder_name`) ; `_fields`, `in` et l'expression conditionnelle passent
  (vérifié en évaluant l'expression avec le `safe_eval` d'Odoo 17).
- **Retour arrière sans le module** : si le code du module disparaît sans désinstallation, `rpbm_rule8_price`
  sort de `_fields` et l'action retombe sur la formule d'origine. Aucune ligne ne plante.
- L'enregistrement Studio est `noupdate` : la garde est posée par code, pas par XML.

## Le prix de la règle 8

`sale.order.line.rpbm_rule8_price` (calculé, non stocké) vaut `_rpbm_rule8_value()`, à défaut `price_unit`
(l'action réécrit alors le prix tel quel). `_rpbm_rule8_value()` renvoie `None`, et le prix reste inchangé,
dans ces cas :

- ligne sans article ou barème (`rpbm_xglass_price`) nul ;
- article de type service ;
- article d'une catégorie enfant de 19 « Consommable », 20 « Film solaire » ou 22 « Services » (P-09),
  retrouvées par `__import__.rpbm_categ_consommable`, `…film_solaire`, `…services` ; un xmlid absent est
  ignoré ;
- filtre de régime actif (`rule8_insurance_only = 1`) et dossier explicitement hors assurance (opportunité
  sans assureur). Un devis sans opportunité reste majoré.

Sinon : barème × `insurance_coefficient`, arrondi au pas `price_rounding` seulement s'il est positif. Avec les
valeurs par défaut, 341,87 donne 512,805 (précision « Product Price » à 4 décimales), comme la règle d'origine.

## Recalcul à la quantité

Le natif `_compute_price_unit` dépend de la quantité et ramène la ligne au `list_price` ; la règle 8 ne repasse
pas, son seul déclencheur étant le Prix X'Glass. La surcharge traite à part les lignes où la règle 8 gardée
s'applique : automatisation active, action égale à la garde (lu une fois par appel), barème non nul, article
non exclu, ligne non facturée (`qty_invoiced > 0` reste au natif, qui ne la touche pas) et hors lignes
d'option de `sale_management`. Ces lignes reçoivent `_rpbm_rule8_value()` ; toutes les autres passent au
natif. Aucune dépendance n'est ajoutée à `price_unit`, la remise n'est pas touchée.

Conséquence : une ligne dont le prix a été saisi à la main revient à barème × 1,5 si sa quantité change
(le natif la ramenait au `list_price`).

## Paramètres

Données `noupdate` ([`data/rule8_data.xml`](../data/rule8_data.xml)), mêmes replis dans
[`models/params.py`](../models/params.py) :

| Clé | Défaut | Rôle |
|---|---|---|
| `rpbm_pricing.insurance_coefficient` | 1.5 | Coefficient appliqué au barème |
| `rpbm_pricing.price_rounding` | 0 | Pas d'arrondi ; 0.01 arrondit au centime (en attente de Q-12) |
| `rpbm_pricing.rule8_insurance_only` | 0 | 1 : plus de majoration sur un dossier hors assurance (en attente du client) |
| `rpbm_pricing.rule8_original_value` | — | Valeur d'origine sauvegardée par la mise en place |

## Mise en place et retrait

- `_rpbm_rule8_install()` est appelé par `hooks.setup()` (à l'installation). L'action est retrouvée par
  xmlid, sinon par recherche d'une seule action `object_write` sur `price_unit` de `sale.order.line` dont la
  valeur est l'originale ou la garde. Déjà gardée : rien à faire. Valeur différente de l'originale (espaces
  ignorés) : avertissement au journal, rien n'est écrit. Sinon la valeur est sauvegardée dans
  `rpbm_pricing.rule8_original_value`, puis la garde est écrite (le nom de l'action est conservé).
- `_rpbm_rule8_uninstall()` (appelé par `uninstall_hook`) : si l'action porte la garde, réécrit la valeur
  sauvegardée, à défaut l'originale.
- Deux actions serveur, réservées à `base.group_system` (Paramètres › Technique › Actions serveur, bouton
  « Exécuter ») : « RPBM : activer la garde de la règle 8 » et « RPBM : restaurer la règle 8 d'origine ».
  Elles affichent le résultat en notification.

## Recette

Sur une ligne dont le Prix X'Glass est un Prix XGlass HT relevé dans X'Glass et saisi à la main :

1. prix = barème × 1,5 à 4 décimales ;
2. quantité passée à 2 : prix inchangé ;
3. ligne de main-d'œuvre (service) et kit de la catégorie 19 portant un barème : prix non majoré ;
4. valeur de l'action 1510 = garde ; « restaurer » puis « activer » font l'aller-retour.

Les tests de bout en bout de [`tests/test_rule8.py`](../tests/test_rule8.py) sautent si l'automatisation réelle
est absente, inactive ou porte une valeur inattendue.

Voir aussi : [Paramètres](parametres.md) · [Recette](recette.md)

---
Précédent : [Paramètres](parametres.md) · Suivant : [Colisage VSF](colisage.md)
