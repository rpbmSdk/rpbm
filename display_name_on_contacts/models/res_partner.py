# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_complete_name(self):
        self.ensure_one()

        displayed_types = self._complete_name_displayed_types
        type_description = dict(self._fields['type']._description_selection(self.env))

        name = self.name or ''
        if self.company_name or self.parent_id:
            if not name and self.type in displayed_types:
                name = type_description[self.type]
            if not self.is_company:
                name = f"{name}, {self.commercial_company_name or self.sudo().parent_id.name}"
        return name.strip()