# Champs — `product.product` / `product.template`

[Index](../../README.md) › [Champs Odoo par modèle](README.md) › Champs — `product.product` / `product.template`

Article recherché puis, si nécessaire, créé depuis un résultat VSF sélectionné dans le widget —
voir [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md). Champs déclarés
dans `models/product_template.py`.

| Champ | Type | Rôle |
|---|---|---|
| `product.template.rpbm_eurocode` | char, indexé | Eurocode VSF complet ; première clé de recherche du produit (la référence interne et le nom ne servent qu'aux produits sans eurocode, lot E1.1) et clé de la synchronisation VSF. Alimenté aussi par l'import du catalogue (`Jobs/Gestion Stock/import_odoo.py`). |
| `product.template.rpbm_width_mm` | float | Largeur issue de la fiche VSF, en millimètres |
| `product.template.rpbm_length_mm` | float | Longueur issue de la fiche VSF, en millimètres |
| `product.product.rpbm_constructor_reference` | char | Référence constructeur de la pièce (`articleVsf.refConstructeur`) ; vide lorsque VSF retourne la sentinelle `"-"` |

Champs standards également écrits à la création : `name`, `default_code` (eurocode, depuis
`17.0.261022.1` ; la référence constructeur reste dans `rpbm_constructor_reference`), `list_price`, `type`, `image_1920`, `description` (note interne structurée
issue de la fiche VSF). Le stock n'est jamais écrit par le widget.

Un `product.supplierinfo` associé est créé dans la foulée (`partner_id` = fournisseur VSF,
`product_name` = désignation VSF, `product_code` = code VSF, `price` = prix public VSF, `discount` = remise RPBM en % (20),
`date_start` vide : le premier tarif couvre aussi une demande de prix antérieure, voir
[premier tarif VSF](../configuration.md#premier-tarif-vsf-sans-date-de-début-1702610212)).

## Synchronisation VSF du modèle

`product.template.sync_vsf_information()` relit la fiche à partir de `rpbm_eurocode` sans le
modifier et met à jour `list_price`, `rpbm_width_mm`, `rpbm_length_mm`, `description` et le prix
fournisseur VSF (historisé : une ligne au même prix et à la même remise est enrichie, un nouveau prix clôture la
ligne à J-1 et en ouvre une à J ; le premier tarif n'a pas de date de début). Désignation, image, type et stock restent inchangés. Le bouton
« Synchroniser VSF » reste masqué (`base.group_no_one`).

## Vue

`rpbm_eurocode`, `rpbm_width_mm` et `rpbm_length_mm` sont affichés sous la référence interne, avant le
code-barres (`views/product_product_views.xml`) ; `rpbm_constructor_reference` dans l'onglet « VSF ». Le
formulaire article (`views/product_template_views.xml`) affiche `rpbm_eurocode` au même endroit. L'ancre est
`barcode` et non `default_code` : `mrp_plm` remplace ce champ par un bloc sans libellé (avec « Version »).

La recherche des articles propose un filtre « Eurocode » avant la catégorie
(`views/product_template_views.xml`, hérité par les recherches `product.product` et stock). Le
filtre standard « Produit » trouvait déjà la plupart des eurocodes, car la référence interne vaut
l'eurocode pour presque tous les articles ; depuis `17.0.261022.1`, les articles créés par le widget
portent aussi l'eurocode en référence interne (migration : 3527 et 3528 corrigés en pré-prod).

## Lu/écrit par

- Écriture : [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md) (`/createProduct`)

---
Précédent : [Champs — `fleet.vehicle`](fleet-vehicle.md) · Suivant : [Champs — `account.move`](account-move.md)

Voir aussi : [9 — Création du produit (`product.product`)](../../fonctionnel/workflow/09-creation-produit.md)
