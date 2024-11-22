# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
	_inherit = 'account.move'
	
	def _post(self, soft=True):
		res = super(AccountMove,self)._post(soft=soft)
		for move in self:
			if move.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
				#PARA ANTICIPOS
				advance_product = self.env['account.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).advance_product
				if advance_product:
					for invoice_line in move.invoice_line_ids.filtered(lambda l: l.product_id.id == advance_product.id and l.price_subtotal > 0):
						invoice_line.cta_cte_origen = True
						invoice_line.invoice_date_it = move.invoice_date
				#############
				if move.name and len(move.name)>1 and move.name.find(' '):
					index = move.name.find(' ')
					move.name = move.name[index+1:]
				if move.payment_reference and len(move.payment_reference)>1 and move.payment_reference.find(' '):
					index = move.payment_reference.find(' ')
					move.payment_reference = move.payment_reference[index+1:]
				if not move.ref:
					move.ref = move.name
				apply_correlative = False
				if len(move.line_ids.filtered(lambda l: l.account_id.account_type in ['asset_receivable','liability_payable']))>1:
					apply_correlative = True
				count = 1
				for line in move.line_ids:
					if not line.type_document_id:
						line.type_document_id = move.l10n_latam_document_type_id.id or None
					if line.account_id.account_type not in ('asset_receivable','liability_payable'):
						if not line.nro_comp:
							line.nro_comp = move.l10n_latam_document_number or None
					if line.account_id.account_type in ('asset_receivable','liability_payable'):
						line.cta_cte_origen = True
						line.invoice_date_it = move.invoice_date
						if apply_correlative:
							line.nro_comp = move.l10n_latam_document_number + ' - C' + str(count)
							line.name = move.l10n_latam_document_number + ' - C' + str(count)
							count += 1
						else:
							line.nro_comp = move.l10n_latam_document_number or None
							line.name = move.l10n_latam_document_number or None

						
		return res
	
	def button_draft(self):
		res = super(AccountMove, self).button_draft()
		for move in self:
			if move.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
				for line in move.line_ids:
					line.type_document_id = None
					line.nro_comp = None
					if line.account_id.account_type in ('asset_receivable','liability_payable'):
						line.name = None
		return res