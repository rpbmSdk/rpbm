# RPBM Pricing

Module Odoo 17 au-dessus de `rpbm_agent` : régime du dossier (assurance ou hors assurance), garde de la
règle 8 (automatisation Studio « Tarif x glass »), choix du fournisseur sans le client livré, mode de
transport des achats, colisage VSF et barème X'Glass recopié sur la facture.

- Documentation : [`docs/README.md`](docs/README.md) (paramètres, règle 8, colisage, recette).
- Consignes de développement : [`CLAUDE.md`](CLAUDE.md).
- Tests purs, sans Odoo : `python3 -I rpbm_pricing/tests/run_pure.py`. Les `TransactionCase` tournent sur
  un build Odoo.sh : `odoo-bin -u rpbm_pricing --test-enable --test-tags /rpbm_pricing --stop-after-init
  --http-port=8899 --max-cron-threads=0`.
