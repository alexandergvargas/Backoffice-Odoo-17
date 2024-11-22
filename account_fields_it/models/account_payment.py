# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountPayment(models.Model):
	_inherit = 'account.payment'
	
	@api.depends('is_internal_transfer')
	def _compute_is_internal_transfer(self):
		for payment in self:
			payment.is_internal_transfer = payment.is_internal_transfer
	
	def _default_type_doc_cash_id(self):
		others = self.env['account.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).others_document_type
		return others
		
	cash_flow_id = fields.Many2one('account.cash.flow',string='Flujo de Caja')
	catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago')
	type_doc_cash_id = fields.Many2one('l10n_latam.document.type',string='Tipo Documento Caja', default=_default_type_doc_cash_id)
	cash_nro_comp = fields.Char(string='Nro. de Op. Caja',size=42)
	type_document_id = fields.Many2one('l10n_latam.document.type',string='Tipo Documento')
	nro_comp = fields.Char(string='Nro. Comprobante')
	is_personalized_change = fields.Boolean(string='T.C. Personalizado',default=False)
	type_change = fields.Float(string='Tipo de Cambio',digits=(12,4),default=1)
	
class AccountPaymentRegister(models.TransientModel):
	_inherit = 'account.payment.register'

	def _default_type_doc_cash_id(self):
		others = self.env['account.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).others_document_type
		return others

	cash_flow_id = fields.Many2one('account.cash.flow',string='Flujo de Caja')
	catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago')
	type_doc_cash_id = fields.Many2one('l10n_latam.document.type',string='Tipo Documento Caja', default=_default_type_doc_cash_id)
	cash_nro_comp = fields.Char(string='Nro. de Op. Caja',size=42)
	type_document_id = fields.Many2one('l10n_latam.document.type',string='Tipo Documento')
	nro_comp = fields.Char(string='Nro. Comprobante')
	is_personalized_change = fields.Boolean(string='T.C. Personalizado',default=False)
	type_change = fields.Float(string='Tipo de Cambio',digits=(12,4),default=1)
