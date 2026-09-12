{
    "name": "RPBM Agent",
    "version": "17.0.260912.1",
    "category": "Tools",
    "description": """""",
    "author": "Paradigme SASU",
    "depends": ["base_setup", "crm", "fleet", "product", "sale_crm"],
    "data": [
        "views/crm_lead_views.xml",
        "views/sale_order_views.xml",
        "views/fleet_vehicle_views.xml",
        "views/product_product_views.xml",
        "views/product_template_views.xml",
        "views/res_config_settings_views.xml",
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
