import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.rpbm_agent.controllers.vsf_config import get_vsf_partner_id

from ..lib import colisage as colisage_lib
from . import params

_logger = logging.getLogger(__name__)

MODES = [("plane", "Avion"), ("boat", "Bateau")]
# Acheteurs seuls : en préprod tous les vendeurs sont dans « Facturation », exclu jusqu'à Q-23.
ATTACH_GROUPS = "purchase.group_purchase_user"


class RpbmColisage(models.Model):
    _name = "rpbm.colisage"
    _description = "Colisage VSF"
    _inherit = ["mail.thread"]
    _order = "date desc, id desc"

    name = fields.Char("N° MARCH", required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", "Fournisseur", default=lambda self: self._rpbm_default_partner())
    company_id = fields.Many2one("res.company", "Société", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id")
    rpbm_mode = fields.Selection(MODES, "Mode", required=True, default="plane", tracking=True)
    date = fields.Date("Date")
    year = fields.Integer("Année", compute="_compute_year", store=True)
    march_move_id = fields.Many2one("account.move", "Facture MARCH", tracking=True)
    move_ids = fields.One2many("account.move", "rpbm_colisage_id", "Factures et avoirs")
    picking_ids = fields.One2many("stock.picking", "rpbm_colisage_id", "Réceptions")
    dau_ids = fields.One2many("rpbm.colisage.dau", "colisage_id", "DAU")
    # Raccourci assumé : montants en devise de la société (les factures VSF sont en euros).
    amount_pieces = fields.Monetary("Pièces", compute="_compute_amounts", store=True)
    amount_fees = fields.Monetary("Frais", compute="_compute_amounts", store=True)
    # Jamais additionné en regroupement (P-41).
    coefficient = fields.Float("Coefficient", digits=(16, 4), compute="_compute_amounts", store=True,
                               group_operator=False)
    is_retained = fields.Boolean("Retenu", compute="_compute_amounts", store=True)

    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "Ce numéro de MARCH a déjà son colisage."),
        ("march_move_uniq", "UNIQUE(march_move_id)", "Cette facture MARCH a déjà son colisage."),
    ]

    @api.model
    def _rpbm_default_partner(self):
        try:
            return get_vsf_partner_id(self.env)
        except UserError as error:
            _logger.warning("rpbm_pricing: fournisseur VSF introuvable pour le colisage (%s)", error)
            return False

    @api.depends("date")
    def _compute_year(self):
        for colisage in self:
            colisage.year = colisage.date.year if colisage.date else 0

    # Les seuils ne sont pas des dépendances : la reprise recalcule tous les colisages.
    @api.depends("move_ids.state", "move_ids.move_type", "move_ids.ref",
                 "move_ids.invoice_line_ids.price_subtotal", "move_ids.invoice_line_ids.account_id",
                 "move_ids.invoice_line_ids.name")
    def _compute_amounts(self):
        min_pieces = params.get_float(self.env, *params.COLISAGE_MIN_PIECES)
        min_fees = params.get_float(self.env, *params.COLISAGE_MIN_FEES)
        for colisage in self:
            moves = colisage.move_ids.filtered(lambda move: (
                move.state == "posted" and move.move_type in ("in_invoice", "in_refund")
                and colisage_lib.parse_bill_ref(move.ref)[0] != colisage_lib.PACK_VIN))
            pieces, fees = colisage_lib.totals(
                (line.account_id.code, line.name, line.price_subtotal, line.move_id.move_type == "in_refund")
                for line in moves.invoice_line_ids if line.display_type == "product")
            colisage.amount_pieces = pieces
            colisage.amount_fees = fees
            colisage.coefficient = colisage_lib.coefficient(pieces, fees)
            colisage.is_retained = colisage_lib.is_retained(pieces, fees, min_pieces, min_fees)

    @api.model
    def _rpbm_import_history(self, since="2025-01-01"):
        """Crée les colisages depuis les factures VSF postées et y rattache MARCH et COMPL ; rejouable.

        Un rattachement existant n'est jamais modifié. Renvoie
        ``{created, attached, refunds_to_attach, exceptions}`` (références des factures non rattachées).
        """
        moves = self.env["account.move"].search([
            ("move_type", "in", ("in_invoice", "in_refund")),
            ("state", "=", "posted"),
            ("partner_id", "child_of", get_vsf_partner_id(self.env)),
            ("date", ">=", since),
        ], order="date, id")
        # MARCH d'abord (tri stable) : une COMPL peut être passée en comptabilité avant sa MARCH.
        moves = moves.sorted(lambda move: colisage_lib.parse_bill_ref(move.ref)[0] != colisage_lib.MARCH)
        boat_numbers = {number.strip() for number in
                        params.get_str(self.env, *params.COLISAGE_BOAT_MARCHS).split(",") if number.strip()}
        by_name = {colisage.name: colisage for colisage in self.search([])}
        report = {"created": 0, "attached": 0, "refunds_to_attach": 0, "exceptions": []}
        for move in moves:
            if move.rpbm_colisage_id:
                continue
            if move.move_type == "in_refund":
                report["refunds_to_attach"] += 1
                continue
            kind, number = colisage_lib.parse_bill_ref(move.ref)
            texts = [move.ref] + move.invoice_line_ids.mapped("name")
            if kind == colisage_lib.PACK_VIN:
                continue
            if kind == colisage_lib.MARCH:
                colisage = by_name.get(number) or self.search([("march_move_id", "=", move.id)], limit=1)
                if not colisage:
                    colisage = by_name[number] = self.create({
                        "name": number,
                        "partner_id": move.commercial_partner_id.id,
                        "company_id": move.company_id.id,
                        "date": move.invoice_date or move.date,
                        "march_move_id": move.id,
                        "rpbm_mode": "boat" if colisage_lib.is_boat(number, texts, boat_numbers) else "plane",
                    })
                    report["created"] += 1
                elif not colisage.march_move_id and not self.search_count([("march_move_id", "=", move.id)]):
                    # Colisage saisi à la main avant sa MARCH : on complète sans rien écraser.
                    colisage.write({"march_move_id": move.id, "date": colisage.date or move.invoice_date or move.date})
            elif kind == colisage_lib.COMPL:
                target = next(filter(None, map(colisage_lib.compl_target, texts[1:])), None)
                colisage = by_name.get(target)
                if not colisage:
                    report["exceptions"].append(move.ref or move.name)
                    continue
                if colisage.rpbm_mode != "boat" and colisage_lib.is_boat(target, texts, boat_numbers):
                    colisage.rpbm_mode = "boat"
            else:
                report["exceptions"].append(move.ref or move.name)
                continue
            move.rpbm_colisage_id = colisage
            report["attached"] += 1
        colisages = self.search([])
        for fname in ("amount_pieces", "amount_fees", "coefficient", "is_retained"):
            self.env.add_to_compute(self._fields[fname], colisages)
        colisages.flush_recordset()
        _logger.info("rpbm_pricing: reprise des colisages VSF %s", report)
        return report

    @api.model
    def _rpbm_action_import_history(self):
        """Action serveur « Reprendre l'historique des colisages VSF »."""
        report = self._rpbm_import_history()
        message = _("%(created)s colisage(s) créé(s), %(attached)s facture(s) rattachée(s), "
                    "%(refunds)s avoir(s) à rattacher à la main.",
                    created=report["created"], attached=report["attached"], refunds=report["refunds_to_attach"])
        if report["exceptions"]:
            message += " " + _("Factures en exception : %s.") % ", ".join(report["exceptions"])
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Colisages VSF"),
                "message": message,
                "type": "warning" if report["exceptions"] else "success",
                "sticky": bool(report["exceptions"]),
            },
        }


class RpbmColisageDau(models.Model):
    _name = "rpbm.colisage.dau"
    _description = "DAU d'un colisage VSF"
    _order = "date, id"

    colisage_id = fields.Many2one("rpbm.colisage", "Colisage", required=True, ondelete="cascade", index=True)
    name = fields.Char("N° DAU", required=True)
    date = fields.Date("Date")
    currency_id = fields.Many2one(related="colisage_id.currency_id")
    amount_octroi = fields.Monetary("Octroi de mer")
    # Pour information : la TVA d'importation reste autoliquidée, hors frais d'approche.
    amount_vat_info = fields.Monetary("TVA (information)")


class AccountMove(models.Model):
    _inherit = "account.move"

    rpbm_colisage_id = fields.Many2one(
        "rpbm.colisage", "Colisage VSF", index=True, tracking=True, copy=False, groups=ATTACH_GROUPS,
        domain="[('partner_id', '=', commercial_partner_id)]")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    rpbm_colisage_id = fields.Many2one("rpbm.colisage", "Colisage VSF", index=True, copy=False, groups=ATTACH_GROUPS)
