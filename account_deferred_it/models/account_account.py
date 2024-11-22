# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class account_account(models.Model):
	_inherit = 'account.account'
	

	type_deferrend = fields.Selection([
		('no', 'No'),
		('draft', 'Crear como Borrador'),
		('posted','Crear y Validar')
	], string='Opciones de Diferidos', default="no")

	account_deferrend_domain_ids = fields.Many2many(
		"account.deferred",
		compute="get_account_deferrend_domain_ids",
	)
	account_deferrend_id = fields.Many2one('account.deferred',string='Modelo',  domain="[('id','in', account_deferrend_domain_ids)]" )
	

	
	@api.onchange('type_deferrend')
	def get_account_deferrend_domain_ids(self):
		for record in self:
			account_deferrend = self.env['account.deferred']
			deferrends = self.env['account.deferred']
			if record.account_type == "liability_non_current":
				deferrends = self.env['account.deferred'].search([('type', '=', 'income'),('is_model', '=', True)])
			if record.account_type == "asset_prepayments":
				deferrends = self.env['account.deferred'].search([('type', '=', 'expense'),('is_model', '=', True)])
			for deferrend in deferrends:
				account_deferrend |= deferrend
			record.account_deferrend_domain_ids = account_deferrend.ids
