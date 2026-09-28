# rpbm

Environnement Python de reference du projet : le `.venv` local a la racine du depot (Python 3.11 du systeme, non versionne). Les commandes `python ...` de la documentation supposent ce venv active (`source .venv/bin/activate`). Pour le (re)creer :

```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r rpbm_agent/controllers/requirements.txt reportlab pillow ipykernel
```

`requirements.txt` est aussi installe par Odoo.sh a chaque build : n'y mettre que les dependances du module, jamais celles des scripts locaux (`reportlab`/`pillow` pour le guide PDF, `ipykernel` pour les notebooks).

## Documentation

- [Cartographie Studio de l'instance RPBM](docs/cartographie/README.md) : inventaire historique des champs, automatisations et dependances connues.
- [Audit Odoo Studio](.paradigme/audits/README.md) : cadre reproductible de snapshot local, d'inventaire et de rafraichissement des personnalisations Studio.
- [Documentation du module `rpbm_agent`](rpbm_agent/docs/README.md) : parcours fonctionnels, architecture et feuille de route du module.
