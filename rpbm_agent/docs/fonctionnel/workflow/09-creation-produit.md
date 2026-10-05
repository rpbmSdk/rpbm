# 9 — Création du produit (`product.product`)

Après la sélection d'un article VSF, le widget cherche le produit dans Odoo, dans cet ordre (lot E1.1, `17.0.261005.4`) :

1. le **code VSF** : `product.template.rpbm_eurocode` égal au code de l'article ;
2. la **référence interne** : `default_code` égal à la référence constructeur de l'article, ou à son code VSF si elle est absente, pour un produit **sans eurocode** seulement (le premier trouvé, si plusieurs produits sans eurocode portent cette référence) ;
3. le **nom exact**, insensible à la casse, pour un **ancien produit sans eurocode** seulement, et seulement s'il est **unique**.

Un produit qui porte l'eurocode d'un autre article n'est jamais retenu, quelle que soit sa référence ou son nom. Avant le lot E1.1, l'ordre était « référence interne, eurocode, nom » et le nom suffisait : la suggestion VSF `6108AXSR` « GEL CAPTEUR SILICONE » s'affichait « Produit Odoo trouvé (nom) » sur le produit de code `6574AXSH`, qui est le gel d'un autre article. « Ajouter au devis » aurait mis ce produit sur la ligne, et « Créer le produit » l'aurait réutilisé. Désormais cette suggestion apparaît « absente de la base Odoo » tant qu'aucun produit ne porte son eurocode, ni ne la rejoint par la référence ou le nom (rangs 2 et 3, réservés aux produits sans eurocode).

Le résultat et le critère trouvé (« eurocode », « référence interne » ou « nom ») sont visibles dans la ligne de détail de chaque article sélectionné ; en l'absence de résultat, l'utilisateur peut créer le produit.

- **Route de recherche** : `POST /doesProductExists` (`main.py::doesProductExists`), qui applique la recherche ci-dessus (`_find_existing_product`, voir [backend](../../technique/backend.md#rattachement-dun-article-vsf-à-un-produit-lot-e11)).
- **Route de création** : `POST /createProduct` (`main.py::createProduct`). Elle renvoie le produit existant, trouvé par la même recherche donc jamais un produit d'un autre article, ou le produit créé ; une création concurrente est sérialisée par code VSF, évitant les doublons de `default_code` et de `product.supplierinfo`.

| Champ écrit (`product.product`) | Source |
|---|---|
| `name` | `articleVsf.name` |
| `default_code` | `articleVsf.refConstructeur`, ou `articleVsf.code` si la référence constructeur est absente (`None`, vide ou `"-"` VSF) |
| `product.template.rpbm_eurocode` | `articleVsf.code` |
| `product.template.rpbm_width_mm` | Largeur de fiche VSF normalisée en millimètres |
| `product.template.rpbm_length_mm` | Longueur de fiche VSF normalisée en millimètres |
| `list_price` | `articleVsf.prixVente` |
| `type` | `'product'` (littéral) |
| `rpbm_constructor_reference` | `articleVsf.refConstructeur`, vide lorsque VSF retourne `"-"` |
| `image_1920` | image pleine taille signée par VSF (`p=xlg`), avec repli sur la miniature si elle est indisponible |
| `description` | note interne HTML échappée : lien fiche VSF, identifiants, prix, stock, dimensions et toutes les caractéristiques libellé/valeur visibles sur la fiche |

| Champ écrit (`product.supplierinfo`) | Source |
|---|---|
| `partner_id` | fournisseur VSF configuré (`rpbm_agent.vsf_partner_id`, défaut `5708`) |
| `product_id` | produit venant d'être créé |
| `delay` / `min_qty` | `1` / `0` (littéraux) |
| `price` | `articleVsf.prixVenteRPBM` (remise `rpbm_agent.vsf_discount`, défaut `0.2`) |

## Synchronisation ultérieure d'un article existant

La méthode batch `product.template.sync_vsf_information()` relit la fiche à partir de `rpbm_eurocode`. Elle ne modifie ni cet identifiant, ni `name`, ni l'image. Elle actualise le prix de vente, les dimensions, la note interne `description` et la ligne fournisseur VSF.

Le prix fournisseur est historisé : une ligne active au même prix est conservée et enrichie (`product_name`/`product_code`) ; un nouveau prix clôture la ligne existante à la veille et démarre une nouvelle ligne à la date du jour. Le bouton de fiche correspondant est livré masqué (`base.group_no_one`) en attente d'une décision d'ouverture aux utilisateurs.

Sur un devis lié à une opportunité, le bouton « Ajouter au devis » ajoute une nouvelle ligne `sale.order.line` avec `default_product_id`, `product_uom_qty = 1` et `rpbm_xglass_price = articleVsf.prixVenteRPBM`. Les `onchange` Odoo calculent les champs dépendants ; le module recopie le prix vers `x_studio_prix_x_glass`, d'où l'automatisation Studio « Tarif x glass » calcule le prix unitaire. Le widget ne met jamais à jour le stock du produit.

Les dimensions sans unité du bloc VSF « Dimensions » sont interprétées en millimètres ; les unités explicites restent converties vers cette même unité.

Détail du champ : [technique/champs/product-product.md](../../technique/champs/product-product.md).
