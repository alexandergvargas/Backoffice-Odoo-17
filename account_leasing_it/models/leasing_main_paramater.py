# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class LeasingMainParameter(models.Model):
	_name = 'leasing.main.parameter'

	name = fields.Char(default="Parametros Principales")
	company_id = fields.Many2one('res.company', string=u'Compañía', default=lambda self: self.env.company.id)

	asset_account_id = fields.Many2one('account.account',string='Cuenta de Activo Fijo')
	deferred_interest_account_id = fields.Many2one('account.account',string='Cuenta de Intereses Diferidos')
	deferred_insurance_account_id = fields.Many2one('account.account',string='Cuenta de Seguros Diferidos')
	leasing_payable_account_id = fields.Many2one('account.account',string='Cuenta por Pagar Leasing')
	interest_payable_account_id = fields.Many2one('account.account',string=u'Cuenta por Pagar Intereses')
	insurance_payable_account_id = fields.Many2one('account.account',string='Cuenta por Pagar Seguros')

	purchase_tax_id = fields.Many2one('account.tax',string='Impuesto de Compra')
	interest_expense_account_id = fields.Many2one('account.account',string=u'Cuenta para Gasto de Intereses')
	commission_expense_account_id = fields.Many2one('account.account',string=u'Cuenta para Gasto de Comisiones')
	insurance_expense_account_id = fields.Many2one('account.account',string='Cuenta para Gasto de Seguros')

	purchase_journal_id = fields.Many2one('account.journal',string='Diario Facturas de Compras')
	journal_id = fields.Many2one('account.journal',string='Diario para Devengos y Asiento General')

	@api.model
	def create(self,vals):
		if len(self.search([('company_id', '=', self.env.company.id)])) > 0:
			raise UserError(u'No se puede crear mas de un Parametro Principal por Compañía')
		return super(LeasingMainParameter,self).create(vals)

	def get_main_parameter(self):
		MainParameter = self.search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter:
			raise UserError(u'No se ha creado Parametros Generales para esta Compañía')
		return MainParameter