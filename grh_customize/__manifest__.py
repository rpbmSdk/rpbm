# -*- coding: utf-8 -*-
{
        'name': 'Custom UI GRH',
    'version': '17.0.260211.1',
    'sequence': 1,
    'summary': """
        Customisation de l'UI
    """,
    'description': """
- 260211.1: Ajout d'un bouton pour basculer toutes les entreprises

- 241009.0: Initial version
 - Effacement du titre de la page
 - [ref](https://github.com/guohuadeng/app-odoo/tree/18.0/app_odoo_customize)
    """,
    'author': 'Paradigme',
    'maintainer': 'Paradigme',
    'depends': [
        'web'
    ],
    'assets': {
        'web.assets_backend': [
            'grh_customize/static/src/js/webclient.js',
            'grh_customize/static/src/switch_company_menu/switch_company_menu.js',
            'grh_customize/static/src/switch_company_menu/switch_company_menu.xml',
        ],
    },
}