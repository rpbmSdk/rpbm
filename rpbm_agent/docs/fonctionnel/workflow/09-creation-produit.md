# 9 — Création du produit (`product.product`)

Après la sélection d'un article VSF, le widget le cherche dans Odoo dans cet ordre : référence interne (`default_code`), eurocode (`product.template.x_studio_eurocode`), puis nom exact insensible à la casse. Le résultat et le critère trouvé sont visibles sur chaque carte sélectionnée ; en l'absence de résultat, l'utilisateur peut créer le produit.

- **Route de recherche** : `POST /doesProductExists` (`main.py::doesProductExists`).
- **Route de création** : `POST /createProduct` (`main.py::createProduct`). Elle renvoie le produit existant ou créé ; une création concurrente est sérialisée par code VSF, évitant les doublons de `default_code` et de `product.supplierinfo`.

| Champ écrit (`product.product`) | Source |
|---|---|
| `name` | `articleVsf.name` |
| `default_code` | `articleVsf.refConstructeur`, ou `articleVsf.code` si la référence constructeur est absente (`None`, vide ou `"-"` VSF) |
| `product.template.x_studio_eurocode` | `articleVsf.code` |
| `product.template.x_studio_largeur_mm` | Largeur de fiche VSF normalisée en millimètres |
| `product.template.x_studio_longueur_mm` | Longueur de fiche VSF normalisée en millimètres |
| `list_price` | `articleVsf.prixVente` |
| `type` | `'product'` (littéral) |
| `x_studio_reference_constructeur` | `articleVsf.refConstructeur`, vide lorsque VSF retourne `"-"` |
| `image_1920` | image pleine taille signée par VSF (`p=xlg`), avec repli sur la miniature si elle est indisponible |
| `description` | note interne HTML échappée : lien fiche VSF, identifiants, prix, stock, dimensions et toutes les caractéristiques libellé/valeur visibles sur la fiche |

| Champ écrit (`product.supplierinfo`) | Source |
|---|---|
| `partner_id` | fournisseur VSF configuré (`rpbm_agent.vsf_partner_id`, défaut `5708`) |
| `product_id` | produit venant d'être créé |
| `delay` / `min_qty` | `1` / `0` (littéraux) |
| `price` | `articleVsf.prixVenteRPBM` (remise `rpbm_agent.vsf_discount`, défaut `0.2`) |

Sur un devis lié à une opportunité, le bouton « Ajouter au devis » ajoute une nouvelle ligne `sale.order.line` avec `default_product_id`, `product_uom_qty = 1` et `x_studio_prix_x_glass = articleVsf.prixVenteRPBM`. Les `onchange` Odoo calculent les champs dépendants ; l'automatisation Studio « Tarif x glass » calcule ensuite le prix unitaire. Le widget ne met jamais à jour le stock du produit.

Les dimensions sans unité du bloc VSF « Dimensions » sont interprétées en millimètres ; les unités explicites restent converties vers cette même unité.

Détail du champ : [technique/champs/product-product.md](../../technique/champs/product-product.md).
