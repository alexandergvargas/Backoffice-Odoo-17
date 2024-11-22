# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

periods = {'00':'opening',
		   '01':'january',
		   '02':'february',
		   '03':'march',
		   '04':'april',
		   '05':'may',
		   '06':'june',
		   '07':'july',
		   '08':'august',
		   '09':'september',
		   '10':'october',
		   '11':'november',
		   '12':'december',
		   '13':'closing'}

def lpad(s, length, char=' '):
		padding = char * (length - len(s))
		return padding + s

class AccountDetractionsWizard(models.TransientModel):
	_name = 'account.detractions.wizard'

	fecha = fields.Date(string='Fecha')
	monto = fields.Float(string='Monto',digits=(12,2))

	def generar(self):
		invoice = self.env['account.move'].browse(self.env.context['invoice_id'])
		m = self.env['account.main.parameter'].search([('company_id','=',invoice.company_id.id)],limit=1)

		if not m.detraction_journal.id:
			raise UserError(u"No esta configurado el Diario de Detracción en Parametros Principales de Contabilidad para su Compañía")

		if not invoice.type_op_det:
			raise UserError(u"Tipo de Operación Obligatorio al generar la detracción")
		if not invoice.detraction_percent_id:
			raise UserError(u"Bien o Servicio Obligatorio al generar la detracción")
		flag_ver = True
		datee = fields.Date.context_today(self)
		data = {
			'journal_id': m.detraction_journal.id,
			'partner_id': invoice.partner_id.id,
			'ref':(invoice.l10n_latam_document_number if invoice.l10n_latam_document_number else 'Borrador'),
			'date': datee if self.fecha > datee else self.fecha,
			'invoice_date': invoice.invoice_date,
			'invoice_date_due': invoice.invoice_date,
			'company_id': invoice.company_id.id,
			'glosa': 'PROVISION DE LA DETRACCION DE LA FACTURA ' + invoice.l10n_latam_document_number,
			'currency_rate': invoice.currency_rate,
			'type_op_det': invoice.type_op_det,
			'detraction_percent_id': invoice.detraction_percent_id.id,
		}
		if invoice.name_move_detraccion and invoice.diario_move_detraccion.id == m.detraction_journal.id and invoice.fecha_move_detraccion == invoice.invoice_date:
			data['name']= invoice.name_move_detraccion
			flag_ver = False
		else:
			invoice.diario_move_detraccion= m.detraction_journal.id
			invoice.fecha_move_detraccion = invoice.invoice_date
			flag_ver = True
		lines = []
		doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)

		if len(invoice.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable','liability_payable'))) > 1:
			raise UserError(u'En el caso de tener una factura con diferentes Plazos de pago, las detracciones se realizan en el menú: Tesoreria / Tesoreria / Pagos Múltiples')
		
		filtered_line = invoice.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable','liability_payable'))
		if invoice.move_type == 'in_invoice':
			if not m.detractions_account.id:
				raise UserError(u"No esta configurada la Cuenta de Detracción para Proveedor en Parametros Principales de Contabilidad para su Compañía")
			line_cc = (0,0,{
				'account_id': filtered_line.account_id.id,
				'debit': round(self.monto * invoice.currency_rate) if invoice.currency_id != invoice.company_id.currency_id else round(self.monto),
				'credit':0,
				'name':'DETRACCION - '+(invoice.l10n_latam_document_number or ''),
				'partner_id': invoice.partner_id.id,
				'nro_comp': (invoice.l10n_latam_document_number or ''),
				'type_document_id': invoice.l10n_latam_document_type_id.id,
				'currency_id': invoice.currency_id.id,
				'amount_currency': self.monto if invoice.currency_id != invoice.company_id.currency_id else round(self.monto),
				'tc': invoice.currency_rate if invoice.currency_id != invoice.company_id.currency_id else 1,
				'company_id': invoice.company_id.id,			
				})
			lines.append(line_cc)

			line_cc = (0,0,{
				'account_id': m.detractions_account.id ,
				'debit': 0,
				'credit':round(self.monto * invoice.currency_rate) if invoice.currency_id != invoice.company_id.currency_id else round(self.monto),
				'name':'DETRACCION - '+(invoice.l10n_latam_document_number or ''),
				'partner_id': invoice.partner_id.id,
				'nro_comp': (invoice.l10n_latam_document_number or ''),
				'type_document_id': doc.id,
				'currency_id': invoice.company_id.currency_id.id,
				'amount_currency': round(self.monto * invoice.currency_rate)*-1 if invoice.currency_id != invoice.company_id.currency_id else round(self.monto)*-1,
				'company_id': invoice.company_id.id,
				'invoice_date_it': datee if self.fecha > datee else self.fecha,
				'cta_cte_origen': True,
				})
			lines.append(line_cc)

		if invoice.move_type == 'out_invoice':
			if not m.customer_account_detractions.id:
				raise UserError(u"No esta configurada la Cuenta de Detracción para Clientes en Parametros Principales de Contabilidad para su Compañía")
			line_cc = (0,0,{
				'account_id': m.customer_account_detractions.id ,
				'debit': round(self.monto * invoice.currency_rate) if invoice.currency_id != invoice.company_id.currency_id else round(self.monto),
				'credit':0,
				'name':'DETRACCION - '+(invoice.l10n_latam_document_number or ''),
				'partner_id': invoice.partner_id.id,
				'nro_comp': (invoice.l10n_latam_document_number or ''),
				'type_document_id': doc.id,
				'currency_id': invoice.company_id.currency_id.id,
				'amount_currency': round(self.monto * invoice.currency_rate) if invoice.currency_id != invoice.company_id.currency_id else round(self.monto),
				'company_id': invoice.company_id.id,
				'invoice_date_it': datee if self.fecha > datee else self.fecha,
				'cta_cte_origen': True,
				})
			lines.append(line_cc)

			line_cc = (0,0,{
				'account_id': filtered_line.account_id.id,
				'debit': 0,
				'credit':round(self.monto * invoice.currency_rate) if invoice.currency_id != invoice.company_id.currency_id else round(self.monto),
				'name':'DETRACCION - '+(invoice.l10n_latam_document_number or ''),
				'partner_id': invoice.partner_id.id,
				'nro_comp': (invoice.l10n_latam_document_number or ''),
				'type_document_id': invoice.l10n_latam_document_type_id.id,
				'currency_id': invoice.currency_id.id,
				'amount_currency': self.monto*-1 if invoice.currency_id != invoice.company_id.currency_id else round(self.monto)*-1,
				'tc': invoice.currency_rate if invoice.currency_id != invoice.company_id.currency_id else 1,
				'company_id': invoice.company_id.id,	
				})
			lines.append(line_cc)

		data['line_ids'] = lines
		tt = self.env['account.move'].create(data)
		if not flag_ver:
			tt.name = invoice.name_move_detraccion
		ids_conciliation = []
		ids_conciliation.append(filtered_line.id)

		for line in tt.line_ids:
			if line.account_id == filtered_line.account_id and line.nro_comp == filtered_line.nro_comp and line.type_document_id == filtered_line.type_document_id and line.partner_id.id == filtered_line.partner_id.id:
				ids_conciliation.append(line.id)

		if tt.state =='draft':
			tt._post()

		if len(ids_conciliation)>1:
			self.env['account.move.line'].browse(ids_conciliation).reconcile()

		invoice.move_detraccion_id = tt.id
		

		if flag_ver:
			if self.fecha > datee:
				tt.write({'date':self.fecha})
				if self.fecha.year != datee.year or self.fecha.month != datee.month:
					reg = self.env['account.journal.sequence'].search([('journal_id','=',tt.journal_id.id),('fiscal_year_id','=',self.env['account.fiscal.year'].search([('name','=',str(tt.date.year))],limit=1).id)],limit=1)
					if not reg:
						raise UserError(u'No existe una secuencia para el diario y la fecha seleccionada.')
					seq = reg[periods[tt.date.strftime('%m')]]
					tt.vou_number = lpad(str(seq), 6, '0')
					reg.write({periods[tt.date.strftime('%m')]: seq + 1})
		
			invoice.name_move_detraccion = tt.vou_number

		return True