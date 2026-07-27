{
    "name": "RPBM Agent",
    "version": "17.0.260727.9",
    "category": "Tools",
    "description": """""",
    "author": "Paradigme SASU",
    "depends": ["crm", "fleet", "sale_crm"],
    "data": [
        "views/crm_lead_views.xml",
        "views/sale_order_views.xml",
        "views/fleet_vehicle_views.xml",
        "views/product_product_views.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    'assets':{
        'web.assets_backend': [
            'rpbm_agent/static/src/*',
        ]
    },
    "external_dependencies": {
        "python": ["beautifulsoup4", "python-dotenv", "requests"],
    },
}
