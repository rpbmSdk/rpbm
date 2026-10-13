{
    "name": "RPBM Pricing",
    "version": "17.0.261012.1",
    "category": "Sales",
    "summary": "Régime du dossier, garde de la règle 8, choix du fournisseur et colisage VSF",
    "description": """Socle tarifaire de RPBM au-dessus de rpbm_agent : régime du dossier (assurance ou
hors assurance), garde de l'automatisation Studio « Tarif x glass » (règle 8), choix du fournisseur
sans le client livré, mode de transport des achats, colisage VSF et barème recopié sur la facture.
Documentation : docs/README.md.""",
    "author": "Paradigme SASU",
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "depends": ["rpbm_agent", "sale_management", "purchase_stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/rule8_data.xml",
        "data/rpbm_colisage_data.xml",
        "views/sale_order_regime_views.xml",
        "views/sale_order_template_views.xml",
        "views/purchase_order_views.xml",
        "views/rpbm_colisage_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
