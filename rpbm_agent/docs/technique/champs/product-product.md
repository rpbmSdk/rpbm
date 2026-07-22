# Champs — `product.product`

Article créé depuis un résultat VSF, uniquement sur Ordre de Vente (bouton "Créer" sur un article VSF) — voir [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md).

| Champ | Type | Origine | Rôle |
|---|---|---|---|
| `x_studio_reference_constructeur` | char | `pre_init_hook` (nouveau) | Référence constructeur de la pièce, copiée depuis `articleVsf.refConstructeur` (VSF) |

Champs standards également écrits à la création (non `x_studio_*`, pour mémoire) : `name`, `default_code`, `list_price`, `type`, `image_1920`, `description` (lien vers la fiche VSF).

Un `product.supplierinfo` associé est créé dans la foulée (`partner_id` = fournisseur VSF, `price` = prix d'achat remisé RPBM) — aucun champ `x_studio_*` sur ce modèle.

Avant ce module : `createProduct` (`main.py`) était cassé sur toute instance sans `x_studio_reference_constructeur` créé manuellement — voir [état des lieux](../../etat-des-lieux.md).

## Vue

Affiché dans l'onglet "VSF" ajouté par `views/product_product_views.xml` (hérite de `product.product_normal_form_view`).

## Lu/écrit par

- Écriture : [9 — Création du produit](../../fonctionnel/workflow/09-creation-produit.md) (route `/createProduct`)
