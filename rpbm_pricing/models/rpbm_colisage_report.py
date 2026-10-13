from odoo import fields, models, tools


class RpbmColisageYearReport(models.Model):
    """Coefficient global annuel des colisages retenus (P-41), une ligne par année.

    Le coefficient se calcule à partir des sommes de l'année, jamais en additionnant ceux des colisages :
    pas de vue pivot.
    """
    _name = "rpbm.colisage.year.report"
    _description = "Coefficient annuel des colisages VSF"
    _auto = False
    _order = "year desc"
    _rec_name = "year"

    year = fields.Integer("Année", readonly=True)
    colisage_count = fields.Integer("Colisages retenus", readonly=True)
    amount_pieces = fields.Float("Pièces", digits=(16, 2), readonly=True)
    amount_fees = fields.Float("Frais", digits=(16, 2), readonly=True)
    coefficient = fields.Float("Coefficient", digits=(16, 4), readonly=True, group_operator=False)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE VIEW %s AS (
                SELECT MIN(c.id) AS id,
                       c.year,
                       COUNT(*) AS colisage_count,
                       SUM(c.amount_pieces) AS amount_pieces,
                       SUM(c.amount_fees) AS amount_fees,
                       (SUM(c.amount_pieces) + SUM(c.amount_fees)) / NULLIF(SUM(c.amount_pieces), 0) AS coefficient
                  FROM rpbm_colisage c
                 WHERE c.is_retained
              GROUP BY c.year
            )
        """ % self._table)
