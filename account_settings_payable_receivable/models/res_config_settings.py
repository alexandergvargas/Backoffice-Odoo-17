# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

from odoo.addons.account.models.company import PEPPOL_LIST


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	account_receivable = fields.Many2one(
		comodel_name="account.account",
		string="Cuenta por cobrar",
		related='company_id.account_receivable',
		readonly=False,
		check_company=True,
		domain="[('deprecated', '=', False), ('account_type', '=', 'asset_receivable')]")
	account_payable = fields.Many2one(
		comodel_name="account.account",
		string="Cuenta por pagar",
		readonly=False,
		related='company_id.account_payable',
		check_company=True,
		domain="[('deprecated', '=', False), ('account_type', '=', 'liability_payable')]")
	

