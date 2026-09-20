# Champs — `product.product` / `product.template`

Article recherché puis, si nécessaire, créé depuis un résultat VSF sélectionné dans le widget —
voir [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md). Champs déclarés
dans `models/product_template.py`.

| Champ | Type | Rôle |
|---|---|---|
| `product.template.rpbm_eurocode` | char, indexé | Eurocode VSF complet ; clé de recherche du produit (avant le nom) et de la synchronisation VSF. Alimenté aussi par l'import du catalogue (`Jobs/Gestion Stock/import_odoo.py`). |
| `product.template.rpbm_width_mm` | float | Largeur issue de la fiche VSF, en millimètres |
| `product.template.rpbm_length_mm` | float | Longueur issue de la fiche VSF, en millimètres |
| `product.product.rpbm_constructor_reference` | char | Référence constructeur de la pièce (`articleVsf.refConstructeur`) ; vide lorsque VSF retourne la sentinelle `"-"` |

Champs standards également écrits à la création : `name`, `default_code` (référence constructeur,
ou code VSF de repli), `list_price`, `type`, `image_1920`, `description` (note interne structurée
issue de la fiche VSF). Le stock n'est jamais écrit par le widget.

Un `product.supplierinfo` associé est créé dans la foulée (`partner_id` = fournisseur VSF,
`product_name` = désignation VSF, `product_code` = code VSF, `price` = prix d'achat remisé RPBM,
`date_start` = date de création).

## Synchronisation VSF du modèle

`product.template.sync_vsf_information()` relit la fiche à partir de `rpbm_eurocode` sans le
modifier et met à jour `list_price`, `rpbm_width_mm`, `rpbm_length_mm`, `description` et le prix
fournisseur VSF (historisé : une ligne au même prix est enrichie, un nouveau prix clôture la
ligne à J-1 et en ouvre une à J). Désignation, image, type et stock restent inchangés. Le bouton
« Synchroniser VSF » reste masqué (`base.group_no_one`).

## Vue

`rpbm_eurocode`, `rpbm_width_mm` et `rpbm_length_mm` sont affichés sous la référence interne ;
`rpbm_constructor_reference` dans l'onglet « VSF » (`views/product_product_views.xml`).

## Lu/écrit par

- Écriture : [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md) (`/createProduct`)
