# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _

class GetInvoicesLettersWizard(models.TransientModel):
	_name = "get.invoices.letters.wizard"
	
	type_selection = fields.Selection([('asset_receivable','Ingresos'),('liability_payable','Egresos')],string='Seleccionar',default='asset_receivable')
	letters_id = fields.Many2one('account.exchange.letters',string='Letras')
	partner_id = fields.Many2one('res.partner',string='Partner',related='letters_id.partner_id')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	invoices = fields.Many2many('account.move.line',string=u'Line Invoices', required=True, 
	domain="[('display_type','not in',['line_section','line_note']),('parent_state','=','posted'),('partner_id','=',partner_id),('type_document_id','!=',False),('reconciled','=',False),('account_type', '=', type_selection),('company_id','=',company_id),'|',('amount_residual', '!=', 0.0),('amount_residual_currency', '!=', 0.0)]")
		
	def insert(self):
		vals=[]
		for invoice in self.invoices:
			residual_amount = 0
			if invoice.currency_id:
				residual_amount = invoice.amount_residual_currency
			else:
				residual_amount = invoice.amount_residual
			val = {
				'main_id': self.letters_id.id,
				'tipo_documento': invoice.type_document_id.id,
				'invoice_id': invoice.id,
				'saldo': residual_amount,
			}
			vals.append(val)
		self.env['account.exchange.letters.line'].create(vals)