{
    "name": "RPBM Agent",
    "version": "17.0.250219.0",
    "category": "Tools",
    "description": """""",
    "author": "Paradigme SASU",
    "depends": ["crm", "fleet"],
    'assets':{
        'web.assets_backend': [
            'rpbm_agent/static/src/*',
        ]
    },
    "external_dependencies": {
        "python": ["beautifulsoup4", "python-dotenv"],
    },
}
