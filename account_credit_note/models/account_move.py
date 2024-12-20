# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	def _post(self, soft=True):
		res = super(AccountMove, self)._post(soft=soft)
		for record in self:
			if record.move_type in ('out_refund','in_refund'):
				if record.payment_state in ('paid'):
					for mm in record.line_ids:
						mm.remove_move_reconcile()
		return res
						

	def make_credit_note_it(self):
		for i in self:
			if i.move_type not in ('in_refund','out_refund'):
				raise UserError('Solo se aplica a Facturas Rectificativas.')

			if i.state not in ('posted'):
				raise UserError('La Factura debe estar publicada')

			if i.payment_state in ('paid'):
				for mm in i.line_ids:
					mm.remove_move_reconcile()
			
			lines = i.doc_invoice_relac
			filtered_line = i.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable','liability_payable'))

			lineas = []

			vals = (0,0,{
				'account_id': filtered_line.account_id.id,
				'partner_id':filtered_line.partner_id.id,
				'type_document_id':filtered_line.type_document_id.id,
				'nro_comp': filtered_line.nro_comp,
				'name': 'APLICACION NOTA DE CREDITO',
				'currency_id': i.currency_id.id,
				'amount_currency': filtered_line.amount_currency * -1,
				'debit': filtered_line.credit,
				'credit': filtered_line.debit,
				'date_maturity':False,
				'company_id': i.company_id.id,
				'reconciled':False,
			})
			lineas.append(vals)

			for doc in lines:
				amount_cy = None
				if doc.amount_currency != 0:
					amount_cy = doc.amount_currency * -1  if i.move_type == 'out_refund' else doc.amount_currency
				if doc.amount == 0 or not doc.amount:
					raise UserError(u'El campo Total MN debe ser diferente a 0.')
				vals = (0,0,{
				'account_id': filtered_line.account_id.id,
				'partner_id':i.partner_id.id,
				'type_document_id':doc.type_document_id.id,
				'nro_comp': doc.nro_comprobante,
				'name': 'APLICACION NOTA DE CREDITO',
				'currency_id': i.currency_id.id if doc.amount_currency != 0 else self.env.company.currency_id.id,
				'amount_currency': amount_cy if doc.amount_currency != 0 else (doc.amount if i.move_type == 'in_refund' else doc.amount*-1),
				'debit': doc.amount if i.move_type == 'in_refund' else 0,
				'credit': doc.amount if i.move_type == 'out_refund' else 0,
				'date_maturity':False,
				'company_id': i.company_id.id,
				'reconciled':False,
				})
				lineas.append(vals)
				#raise UserError(str(vals))

			credit_journal = self.env['account.main.parameter'].search([('company_id','=',i.company_id.id)],limit=1).credit_journal
			if not credit_journal:
				raise UserError(u'No existe Diario para Notas de Crédito en los Parametros Principales de Contabilidad para su Compañía')
			
			move_id = self.env['account.move'].create({
			'company_id': i.company_id.id,
			'partner_id': i.partner_id.id,
			'journal_id': credit_journal.id,
			'date': i.invoice_date,
			'line_ids':lineas,
			'nro_comp': (i.l10n_latam_document_number or ''),
			'l10n_latam_document_type_id': i.l10n_latam_document_type_id.id,
			'glosa':'APLICACION NOTA DE CREDITO %s' % (i.l10n_latam_document_number or ''),
			'move_type':'entry'})
			
			ids_conciliation = []
			ids_conciliation.append(filtered_line.id)

			for line in move_id.line_ids:
				if line.account_id == filtered_line.account_id and line.nro_comp == filtered_line.nro_comp and line.type_document_id == filtered_line.type_document_id and line.partner_id.id == filtered_line.partner_id.id:
					ids_conciliation.append(line.id)
			
			move_id._post()
			

			if len(ids_conciliation)>1:
				self.env['account.move.line'].browse(ids_conciliation).reconcile()
		

			return self.env['popup.it'].get_message("SE GENERO EL ASIENTO DE NC CORRECTAMENTE.")