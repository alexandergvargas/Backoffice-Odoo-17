# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _

class GetAccountMultipaymentLineWizard(models.TransientModel):
	_name = "get.account.multipayment.line.wizard"
	
	retention_comp = fields.Many2one('account.retention.comp',string='Comp de Retencion')
	partner_id = fields.Many2one('res.partner',related='retention_comp.partner_id')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	lines = fields.Many2many('multipayment.advance.it.line','get_account_multipayment_invoice_wizard_rel',string=u'Multipayment Lines', required=True, 
	domain="[('partner_id','=',partner_id),('amount_retention','>',0),('main_id.company_id','=',company_id),('retention_id','=',False)]")
		
	def insert(self):
		vals=[]
		for l in self.lines:
			val = {
				'main_id': self.retention_comp.id,
				'type_document_id': l.tipo_documento.id,
				'invoice_id': l.invoice_id.id,
				'invoice_date_it': l.invoice_id.move_id.invoice_date,
				'amount_total_signed': abs(l.invoice_id.move_id.amount_total_signed),
				'debit': l.debe,
				'amount_retention': l.amount_retention,
				'multipayment_line_id': l.id,
			}
			l.write({'retention_id':self.retention_comp.id})
			vals.append(val)
		self.env['account.retention.comp.line'].create(vals)