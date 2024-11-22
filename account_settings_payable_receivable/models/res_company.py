# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.account.models.company import PEPPOL_LIST


class ResCompany(models.Model):
	_inherit = 'res.company'
	
	account_receivable = fields.Many2one(
		comodel_name="account.account",
		string="Cuenta por cobrar",
		readonly=False,
		check_company=True,
		domain="[('deprecated', '=', False), ('account_type', '=', 'asset_receivable')]")
	account_payable = fields.Many2one(
		comodel_name="account.account",
		string="Cuenta por pagar",
		readonly=False,
		check_company=True,
		domain="[('deprecated', '=', False), ('account_type', '=', 'liability_payable')]")
	
	def write(self, vals):
		res = super().write(vals)
		for i in self:
			i.get_account_receivable()
			i.get_onchange_account_payable()
		return  res
	
	def get_account_receivable(self):
		for i in self:
			if i.account_receivable:
				property_receivable = self.env['ir.property'].search([('name','=',str('property_account_receivable_id'))]).filtered(lambda property: not property.res_id)
				property_receivable.value_reference = 'account.account,'+str(i.account_receivable.id)

	def get_onchange_account_payable(self):
		for i in self:
			if i.account_payable:
				property_receivable = self.env['ir.property'].search([('name','=',str('property_account_payable_id'))]).filtered(lambda property: not property.res_id)
				property_receivable.value_reference = 'account.account,'+str(i.account_payable.id)
