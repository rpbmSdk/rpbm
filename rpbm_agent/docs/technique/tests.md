# Tests

[Index](../README.md) › Technique › Tests

Le module a trois familles de tests. Seule la première demande une base Odoo.

| Famille | Fichiers | Nombre | Lanceur |
|---|---|---|---|
| Tests Odoo | `tests/test_*.py` | 57 méthodes `test_` : 34 `TransactionCase` (lancées par Odoo) et 23 `unittest.TestCase` (ignorées par Odoo) | `odoo-bin --test-enable` pour les 34 ; les 23 se lancent à la main |
| Tests portails sans réseau | `test_portal_auth.py` | 36 fonctions `test_` | `python test_portal_auth.py` (Odoo ne les lance pas, voir ci-dessous) |
| Tests du widget sans navigateur | `test_widget_vsf.mjs` | un script d'assertions | `node test_widget_vsf.mjs` |

Les décomptes viennent des fichiers au 2026-10-13 (version `17.0.261013.1`). Un résultat d'exécution n'est
pas consigné ici : il dépend du build où le lanceur tourne.

## Tests Odoo (`tests/`)

`tests/__init__.py` importe les dix modules. 34 méthodes sont des `TransactionCase` (base PostgreSQL requise),
23 des `unittest.TestCase` simples. **Sous `--test-enable`, seules les 34 `TransactionCase` tournent** : le
sélecteur de tests d'Odoo écarte toute classe sans attribut `test_tags`
(`/root/git/odoo17/odoo/odoo/tests/tag_selector.py:66-68`), posé seulement par la métaclasse de
`BaseCase` (`odoo/tests/common.py:228-236`). Les 23 méthodes `TestCase` ne sont donc pas jouées par Odoo ;
lancez-les avec `python -m unittest` depuis le venv, ou passez ces classes à `odoo.tests.common.BaseCase`
comme dans [`rpbm_pricing`](../../../rpbm_pricing/docs/technique/tests.md).

| Fichier | Classes (base) | Méthodes | Ce qui est vérifié |
|---|---|---|---|
| `test_legacy_converters.py` | `TestCase` | 8 | Convertisseurs natif ↔ Studio : nom normalisé, VIN historique, date mois/année, énergie, pièce concernée et lieu, entiers et texte, noms de champs natifs. |
| `test_legacy_sync.py` | `TransactionCase` ×2 | 14 + 1 | Synchronisation avec les champs Studio, dans les deux sens, y compris la priorité du Studio saisi sur un natif vide (`17.0.261013.1`) et les miroirs Studio d'un devis neuf qui n'effacent plus les natifs (`17.0.261015.2`) ; la seconde classe vérifie que le module marche sans aucun champ Studio. Voir [configuration](configuration.md#priorité-en-cas-de-double-saisie). |
| `test_sale_order_carrier.py` | `TestCase`, `TransactionCase`, `TestCase` | 2 + 8 + 1 | Correspondance lieu d'intervention → transporteur (trois lieux), préremplissage à la création et au changement d'opportunité, refus de confirmer sans `carrier_id`, contrat de la vue versionnée. |
| `test_sale_order_report_views.py` | `TestCase` | 6 | Rapports QWeb des devis (AG01-04) : héritage des vues Studio attendues, transporteur affiché une fois avec repli historique, kilométrage et lieu d'assurance intacts, aucune vue Studio remplacée en bloc. |
| `test_product_template_vsf_sync.py` | `TransactionCase` | 4 | Prix fournisseur créé ou mis à jour, historique des prix, un échec n'interrompt pas le lot ; article existant avec un fournisseur local : ligne VSF ajoutée en tête (P-36), `list_price` et fournisseur local intacts, séquence gardée à l'historisation (IMP-3, `17.0.261015.1`). |
| `test_sale_line_prices.py` | `TransactionCase` | 4 | Prix fournisseur de la ligne de devis : fournisseur prioritaire par séquence, net de remise, fournisseur expiré ignoré, valeur fournie conservée jusqu'au changement d'article ; barème de la pièce d'origine en miroir opportunité ↔ devis (`17.0.261015.1`). |
| `test_labor_operations.py` | `TestCase` | 3 | `_labor_operation_payload` : taux T1/T2/T3 vers les produits de service, code d'activité normalisé, opération non ajoutable (durée invalide, taux inconnu, identifiant manquant). |
| `test_create_vehicle_fuel.py` | `TestCase` | 3 | Table énergie X'Glass vers `fuel_type` Fleet (chaînes reçues ; énergie inconnue ou invalide laissée vide). |
| `test_find_existing_product.py` | `TransactionCase` | 6 | Rattachement d'un article VSF à un produit existant (lot E1.1) : voir [backend](backend.md#rattachement-dun-article-vsf-à-un-produit-lot-e11). |
| `test_portal_parsing.py` | `TestCase` | 0 propre | Recopie les 36 fonctions de `test_portal_auth.py` dans une `TestCase` ; Odoo l'ignore (voir ci-dessous). |

### Lancer

Sur un build avec base de test, par exemple :

```
odoo-bin -u rpbm_agent --test-enable --test-tags /rpbm_agent --stop-after-init --http-port=8899 --max-cron-threads=0
```

`/rpbm_agent` sélectionne les tests standard du module (`odoo/tests/tag_selector.py` : un filtre `/module`
implique le tag `standard`). Le même mécanisme est utilisé par [`rpbm_pricing`](../../../rpbm_pricing/README.md).
Le build de staging met le module à jour sans `--test-enable` : les tests ne tournent pas à une mise à jour
ordinaire.

## Tests portails sans réseau

[`test_portal_auth.py`](../../test_portal_auth.py) vérifie sans réseau l'authentification des agents, le
parsing des réponses X'Glass et VSF, la reconnexion VSF à la demande et la gestion des sessions, avec des portails
simulés d'après des traces réelles (voir [configuration](configuration.md#authentification-des-portails)).

`tests/test_portal_parsing.py` copie chaque fonction `test_*` de ce fichier dans une classe `TestCase`, dans
l'intention de les faire passer au lanceur Odoo ([Débogage des portails](configuration.md#débogage-des-portails)).
Cette classe dérive de `unittest.TestCase` : Odoo l'ignore, les 36 fonctions ne s'ajoutent donc pas aux tests
Odoo. Elles ne tournent que par `python test_portal_auth.py`.

Hors Odoo, dans le venv du dépôt : `python test_portal_auth.py` affiche une ligne `ok` par test puis
« Tous les tests passent. ».

## Tests du widget

[`test_widget_vsf.mjs`](../../test_widget_vsf.mjs) charge les sources de `static/src/` dans un contexte `vm` Node,
avec des crochets OWL simulés (`useEffect` rejoués à la main) et des appels `rpc` enregistrés. Il vérifie le
comportement du dialog sans navigateur : recherches VSF, absence d'authentification X'Glass à l'ouverture d'un
devis, données écrites par `getRecordData`, aperçu des images, barème et prix fournisseur posés par « Ajouter au devis » (accessoires sans barème, ajout maintenu si VSF échoue), base Eurocode dérivée d'un eurocode seulement (`17.0.261015.1`). Aucune dépendance : `node test_widget_vsf.mjs`
(Node 22 sur le poste de développement) sort en code 0 si toutes les assertions passent. Détail des cas :
[frontend](frontend.md#vsf-dabord-xglass-à-la-demande-lot-e2).

## Recettes dans l'interface

Les tests ci-dessus ne remplacent pas la recette sur un build : les scénarios jouables sur l'instance
(plaques, bases Eurocode, articles) sont dans le [jeu de test](../jeu-de-test.md).

---
Précédent : [Configuration & déploiement](configuration.md) · Suivant : [Interaction avec rpbm_pricing](rpbm-pricing.md)

Voir aussi : [Backend](backend.md) · [RPBM Pricing](../../../rpbm_pricing/README.md) · [Frontend (OWL)](frontend.md) · [Jeu de test — Assistant véhicule RPBM](../jeu-de-test.md)
