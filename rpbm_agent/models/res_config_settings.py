from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    rpbm_xglass_user = fields.Char(
        string="Identifiant X'Glass",
        config_parameter="XGLASS_USER",
        groups="base.group_system",
    )
    rpbm_xglass_pass = fields.Char(
        string="Mot de passe X'Glass",
        config_parameter="XGLASS_PASS",
        groups="base.group_system",
    )
    rpbm_vsf_login = fields.Char(
        string="Identifiant VSF",
        config_parameter="VSF_LOGIN",
        groups="base.group_system",
    )
    rpbm_vsf_password = fields.Char(
        string="Mot de passe VSF",
        config_parameter="VSF_PASSWORD",
        groups="base.group_system",
    )
