# -*- coding: utf-8 -*-
{
        'name': 'Custom UI GRH',
    'version': '17.0.241009.0',
    'sequence': 1,
    'summary': """
        Customisation de l'UI
    """,
    'description': """
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
        ],
    },
}