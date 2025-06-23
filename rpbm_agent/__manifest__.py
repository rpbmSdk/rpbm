{
    "name": "RPBM Agent",
    "version": "17.0.250623.1",
    "category": "Tools",
    "description": """""",
    "author": "Paradigme SASU",
    "depends": ["crm", "fleet", "sale_crm"],
    'assets':{
        'web.assets_backend': [
            'rpbm_agent/static/src/*',
        ]
    },
    "external_dependencies": {
        "python": ["beautifulsoup4", "python-dotenv"],
    },
}
