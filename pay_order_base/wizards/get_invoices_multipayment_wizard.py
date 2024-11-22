# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _

class GetInvoicesMultipaymentWizard(models.TransientModel):
	_inherit = "get.invoices.multipayment.wizard"

	def insert(self):
		vals=[]
		for invoice in self.invoices:
			residual_amount = 0
			if invoice.currency_id:
				residual_amount = invoice.amount_residual_currency
			else:
				residual_amount = invoice.amount_residual
			cta_abono = self.env['res.partner.bank'].search([('partner_id','=',invoice.partner_id.id),('currency_id','=',self.multipayment_id.journal_id.currency_id.id),('is_detraction_account','=',False)],limit=1)
			val = {
				'main_id': self.multipayment_id.id,
				'partner_id': invoice.partner_id.id,
				'tipo_documento': invoice.type_document_id.id,
				'invoice_id': invoice.id,
				'saldo': residual_amount,
				'operation_type': invoice.move_id.type_op_det,
				'good_services': invoice.move_id.detraction_percent_id.code,
				'cta_abono': cta_abono.id if cta_abono else invoice.move_id.acc_number_partner_id.id,
				'payment_type_catalog_id': invoice.partner_id.payment_type_catalog_id.id,
			}
			vals.append(val)
		self.env['multipayment.advance.it.line'].create(vals)