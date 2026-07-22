# 9 — Création du produit (`product.product`)

Spécifique à l'Ordre de Vente — pas de flux équivalent sur Piste/Opportunité.

- **Déclencheur** : bouton "Créer" sur un article VSF affiché (`SaleOrderArticleComponent`), si l'article n'existe pas déjà comme produit Odoo (vérifié via `doesProductExists()` → `GET /doesProductExists`).
- **Route** : `POST /createProduct` (`main.py::createProduct`).

| Champ écrit (`product.product`) | Source |
|---|---|
| `name` | `articleVsf.name` |
| `default_code` | `articleVsf.code` |
| `list_price` | `articleVsf.prixVente` |
| `type` | `'product'` (littéral) |
| `x_studio_reference_constructeur` | `articleVsf.refConstructeur` |
| `image_1920` | image téléchargée depuis VSF (premier `absoluteImgUrls`, si HTTP 200) |
| `description` | lien HTML vers la fiche VSF |

| Champ écrit (`product.supplierinfo`) | Source |
|---|---|
| `partner_id` | fournisseur VSF (constante `VSF_PARTNER_ID`) |
| `product_id` | produit venant d'être créé |
| `delay` / `min_qty` | `1` / `0` (littéraux) |
| `price` | `articleVsf.prixVenteRPBM` (prix de vente remisé de 20 %, `remiseRPBM`) |

Ensuite, indépendamment (bouton "Ajouter", `addToSaleOrder()`) : une nouvelle ligne `sale.order.line` est ajoutée à `order_line` avec `default_product_id` en contexte — pas d'écriture de champ `x_studio_*`.

Détail du champ : [technique/champs/product-product.md](../../technique/champs/product-product.md).
