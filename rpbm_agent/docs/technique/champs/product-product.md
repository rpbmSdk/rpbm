# Champs — `product.product`

Article recherché puis, si nécessaire, créé depuis un résultat VSF sélectionné dans le widget — voir [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md).

| Champ | Type | Origine | Rôle |
|---|---|---|---|
| `x_studio_reference_constructeur` | char | `pre_init_hook` (nouveau) | Référence constructeur de la pièce, copiée depuis `articleVsf.refConstructeur` (VSF) |
| `product.template.x_studio_eurocode` | char | `pre_init_hook` + migration `17.0.260727.1` | Eurocode VSF complet ; recherché avant le nom afin de réutiliser le bon produit |
| `product.template.x_studio_largeur_mm` | float | `pre_init_hook` + migration `17.0.260727.9` | Largeur issue de la fiche VSF, normalisée en millimètres |
| `product.template.x_studio_longueur_mm` | float | `pre_init_hook` + migration `17.0.260727.9` | Longueur issue de la fiche VSF, normalisée en millimètres |

Champs standards également écrits à la création (non `x_studio_*`, pour mémoire) : `name`, `default_code` (référence constructeur, ou code VSF de repli), `list_price`, `type`, `image_1920`, `description` (note interne structurée issue de la fiche VSF). Le stock n'est jamais écrit par le widget : il reste géré par les mécanismes internes Odoo.

Un `product.supplierinfo` associé est créé dans la foulée (`partner_id` = fournisseur VSF, `price` = prix d'achat remisé RPBM) — aucun champ `x_studio_*` sur ce modèle.

Avant ce module : `createProduct` (`main.py`) était cassé sur toute instance sans `x_studio_reference_constructeur` créé manuellement — voir [état des lieux](../../etat-des-lieux.md).

## Vue

`x_studio_eurocode`, `x_studio_largeur_mm` et `x_studio_longueur_mm` sont affichés sous la référence interne sur la fiche produit. La référence constructeur reste affichée dans l'onglet "VSF" ajouté par `views/product_product_views.xml` (hérite de `product.product_normal_form_view`).

## Lu/écrit par

- Écriture : [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md) (route `/createProduct`)
