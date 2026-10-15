# Tests

[RPBM Pricing](../../README.md) › [Documentation](../README.md) › [Manuel technique](README.md) › Tests

Le module a 35 tests : 11 purs, qui tournent sans Odoo, et 24 `TransactionCase`, qui tournent sous Odoo.
Décompte relu dans le code (`grep "def test_"`) ; il correspond à la recette du 2026-10-13 (35 tests, 0 échec
sur le build `rpbm-pre-prod-39736343`).

| Fichier | Tests | Sous Odoo | Sujet |
|---|---|---|---|
| [`test_regime_pure.py`](../../tests/test_regime_pure.py) | 4 | non | régime du dossier et du modèle, avertissements |
| [`test_colisage_pure.py`](../../tests/test_colisage_pure.py) | 7 | non | références de factures, lignes, coefficient, seuils, mode bateau |
| [`test_regime.py`](../../tests/test_regime.py) | 4 | oui | régime sur de vrais enregistrements, mise en place idempotente |
| [`test_rule8.py`](../../tests/test_rule8.py) | 9 | oui | garde, prix, exclusions, filtre de régime, quantité, ligne facturée |
| [`test_supplier_choice.py`](../../tests/test_supplier_choice.py) | 4 | oui | client jamais fournisseur, brouillon bateau, confirmation sans transporteur |
| [`test_colisage.py`](../../tests/test_colisage.py) | 5 | oui | reprise, montants, coefficient annuel, unicité |
| [`test_invoice.py`](../../tests/test_invoice.py) | 2 | oui | barème recopié, PDF sans net ni remise |

## Tests purs

Logique de `lib/`, sans import d'Odoo. En local :

```sh
python3 -I rpbm_pricing/tests/run_pure.py
```

[`tests/run_pure.py`](../../tests/run_pure.py) charge chaque `tests/test_*_pure.py` par son chemin (le paquet
`tests` importe Odoo) et met `rpbm_pricing/` dans `sys.path` pour `from lib import ...`. Il sort en erreur si un
test échoue ou si aucun test n'a tourné. Le 2026-10-13 : 11 tests, tous passés.

Les fichiers purs ont un en-tête à double entrée : sous Odoo, `BaseCase` ; en local, `unittest.TestCase`.
Sans cela, Odoo ignorerait ces tests : le sélecteur de balises saute tout test sans attribut `test_tags`, donc non dérivé de
`BaseCase` (`/root/git/odoo17/odoo/odoo/tests/tag_selector.py:66-68`). Les tests purs de `rpbm_agent`, qui héritent de
`unittest.TestCase`, sont dans ce cas.

Autres contrôles locaux avant un commit :

- `python3 -I -m py_compile` sur tous les `.py` du module ;
- analyse des XML : `python3 -I -c "import sys,xml.etree.ElementTree as E;[E.parse(f) for f in sys.argv[1:]]" $(find rpbm_pricing -name '*.xml')` ;
- `git check-ignore --no-index rpbm_pricing/security/ir.model.access.csv rpbm_pricing/docs/README.md` ne
  renvoie rien (les fichiers du module ne sont pas ignorés).

## Tests sous Odoo

Tous les `TransactionCase` sont `@tagged("post_install", "-at_install")`. Ils sont écrits pour tourner sur la
base de préprod ([`tests/common.py`](../../tests/common.py)) :

- `RpbmPricingCase` crée un transporteur fixe (`rpbm_agent` refuse de confirmer un devis sans
  transporteur) et un partenaire VSF de test, posé dans `rpbm_agent.vsf_partner_id` : les tests ne dépendent
  pas du VSF réel (5708) ;
- les colisages de test sont datés 2099 ;
- ce qui exige un champ Studio ou l'automatisation réelle fait `skipTest` au lieu d'échouer ;
- les tests de mise en place de la règle 8 travaillent sur une action de test, pas sur l'action 1510.

### Commande du webshell

Dans le webshell du build Odoo.sh :

```sh
odoo-bin -u rpbm_pricing --test-enable --test-tags /rpbm_pricing --stop-after-init --http-port=8899 --max-cron-threads=0
```

| Option | Raison |
|---|---|
| `-u rpbm_pricing` | met à jour le module avant les tests |
| `--test-enable --test-tags /rpbm_pricing` | tests du module seulement |
| `--stop-after-init` | quitte à la fin |
| `--http-port=8899` | avec `--test-enable`, Odoo démarre le serveur HTTP même avec `--stop-after-init` (`/root/git/odoo17/odoo/odoo/service/server.py:584-587`) ; il faut un port distinct de celui du build |
| `--max-cron-threads=0` | aucun cron pendant les tests |

Les tests tournent sur la base de préprod et sont annulés (rollback). **`-u` committe en revanche la mise à
jour du module** : elle est idempotente, mais c'est une écriture réelle.

Lire le bilan en fin de sortie : zéro échec et zéro erreur attendus sur 35 tests. Les tests sautés (`skipTest`)
sont signalés dans le journal et ne comptent pas comme des échecs.

Voir aussi : [Conventions de développement](conventions.md)

---
Précédent : [Installation et déploiement](installation.md) · Suivant : [Recette Jev](recette-jev.md)
