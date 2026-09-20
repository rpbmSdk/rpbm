{
    "name": "RPBM Agent",
    "version": "17.0.260921.7",
    "category": "Tools",
    "summary": "Assistant véhicule et pièces X'Glass / VSF pour les pistes et devis",
    "description": """Widget Odoo qui interroge les portails X'Glass (véhicule, catégories, pièces,
temps de main-d'œuvre) et VSF (articles par eurocode) depuis une piste CRM ou un devis,
crée le véhicule Fleet et les produits correspondants, puis reporte les données
normalisées dans ses champs natifs, synchronisés avec les champs Studio historiques. Documentation : docs/README.md.""",
    "author": "Paradigme SASU",
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "depends": ["base_setup", "crm", "delivery", "fleet", "product", "sale_crm", "sale_stock"],
    "data": [
        "views/crm_lead_views.xml",
        "views/sale_order_views.xml",
        "views/sale_order_carrier_views.xml",
        "views/sale_order_report_views.xml",
        "views/fleet_vehicle_views.xml",
        "views/product_product_views.xml",
        "views/product_template_views.xml",
        "views/res_config_settings_views.xml",
    ],
    'assets':{
        'web.assets_backend': [
            'rpbm_agent/static/src/*',
        ]
    },
    "external_dependencies": {
        "python": ["beautifulsoup4", "requests"],
    },
}
