# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import tempfile
import binascii
import xlrd
from datetime import datetime
import base64
_logger = logging.getLogger(__name__)


class ImportInvoiceIt(models.Model):
	_inherit = 'import.invoice.it'
	
	def import_invoice(self):
		if not self.type_import:
			raise UserError('Falta escoger Tipo')
		if not self.account_opt:
			raise UserError('Falta escoger "Cuenta de" en pestaña Cuenta')
		if not self.journal_id:
			raise UserError('Falta escoger "Diario" para la importación')
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.file))
			fp.seek(0)
			values = {}
			invoice_ids=[]
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)
		except Exception:
			raise UserError(_("Please select an XLS file or You have selected invalid file"))
		
		for row_no in range(sheet.nrows):
			val = {}
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if self.account_opt == 'default':
					if len(line) == 31:
						if line[11] == '':
							raise UserError(_('Please assign a date'))
						else:
							a1 = int(float(line[11]))
							a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
							date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
						if line[12] == '':
							raise UserError(_('Please assign a invoice date'))
						else:
							a1_i = int(float(line[12]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							date_invoice_string = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						date_invoice_due_string = date_invoice_string
						if line[17] != '':
							a1_i = int(float(line[17]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							date_invoice_due_string = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						fecha_doc_relac = None
						if line[19] != '':
							a1_i = int(float(line[19]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							fecha_doc_relac = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						fecha_detrac = None
						if line[26] != '':
							a1_i = int(float(line[26]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							fecha_detrac = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						custom_id = False
						if str(line[30]) != '':
							custom_id = self.validate_account_custom(str(line[30]))
						values.update( {'invoice':line[0],
										'customer': str(line[1]),
										'currency': line[2],
										'product': line[3].split('.')[0],
										'quantity': line[4],
										'uom': line[5],
										'description': line[6],
										'price': line[7],
										'discount':line[8],
										'salesperson': line[9],
										'tax': line[10],
										'date': date_string,
										'date_invoice': date_invoice_string,
										'date_invoice_due': date_invoice_due_string,
										'seq_opt':self.sequence_opt,
										'td': str(line[13]),
										'nro_comprobante': str(line[14]),
										'glosa': str(line[15]),
										'analytic_distribution': str(line[16]),
										'td_doc_relac': str(line[18]),
										'fecha_doc_relac': fecha_doc_relac,
										'nro_doc_relac': str(line[20]),
										'monto_me_doc_relac': str(line[21]),
										'total_mn_doc_relac': str(line[22]),
										'base_doc_relac': str(line[23]),
										'igv_doc_relac': str(line[24]),
										'tipo_ope': str(line[25]),
										'fecha_detrac': fecha_detrac,
										'nro_comp_detrac': str(line[27]),
										'monto_detrac': line[28],
										'bien_servi': str(line[29]),
										'personalizadas_id':str(line[30])
										})
					elif len(line) > 31:
						raise UserError(u'Tu archivo tiene más columnas que la plantilla de ejemplo.')
					else:						
						raise UserError(u'Tu archivo tiene menos columnas que la plantilla de ejemplo.')
				else:
					if len(line) == 32:
						if line[12] == '':
							raise UserError(_('Please assign a date'))
						else:
							a1 = int(float(line[12]))
							a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
							date_string = a1_as_datetime.date().strftime('%Y-%m-%d')

						if line[13] == '':
							raise UserError(_('Please assign a invoice date'))
						else:
							a1_i = int(float(line[13]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							date_invoice_string = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						date_invoice_due_string = date_invoice_string
						if line[18] != '':
							a1_i = int(float(line[18]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							date_invoice_due_string = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						fecha_doc_relac = None
						if line[20] != '':
							a1_i = int(float(line[20]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							fecha_doc_relac = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						fecha_detrac = None
						if line[27] != '':
							a1_i = int(float(line[27]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							fecha_detrac = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						custom_id = False
						if str(line[31]) != '':
							custom_id = int(self.validate_account_custom(str(line[31])))
						values.update( {'invoice':line[0],
										'customer': str(line[1]),
										'currency': line[2],
										'product': line[3].split('.')[0],
										'account': line[4],
										'quantity': line[5],
										'uom': line[6],
										'description': line[7],
										'price': line[8],
										'discount':line[9],
										'salesperson': line[10],
										'tax': line[11],
										'date': date_string,
										'date_invoice': date_invoice_string,
										'date_invoice_due': date_invoice_due_string,
										'seq_opt':self.sequence_opt,
										'td': str(line[14]),
										'nro_comprobante': str(line[15]),
										'glosa': str(line[16]),
										'analytic_distribution': str(line[17]),
										'td_doc_relac': str(line[19]),
										'fecha_doc_relac': fecha_doc_relac,
										'nro_doc_relac': str(line[21]),
										'monto_me_doc_relac': str(line[22]),
										'total_mn_doc_relac': str(line[23]),
										'base_doc_relac': str(line[24]),
										'igv_doc_relac': str(line[25]),
										'tipo_ope': str(line[26]),
										'fecha_detrac': fecha_detrac,
										'nro_comp_detrac': str(line[28]),
										'monto_detrac': line[29],
										'bien_servi': str(line[30]),
										'personalizadas_id': custom_id
										})
					elif len(line) > 32:
						raise UserError(u'Tu archivo tiene más columnas que la plantilla de ejemplo.')
					else:
						raise UserError(u'Tu archivo tiene menos columnas que la plantilla de ejemplo.')
				res = self.make_invoice(values)
				res._get_currency_rate()
				res._compute_amount()
				res.flush_model()
				if date_string != date_invoice_string:
					res.write({'date': date_string})
				invoice_ids.append(res)

		if self.stage == 'confirm':
			for res in invoice_ids: 
				if res.state in ['draft']:
					res.action_post()
		for invoice in self.move_ids:
			invoice.invoice_name = None
		self.state = 'import'
	
	def make_invoice(self, vals):
		for i in self:
			res = super(ImportInvoiceIt, i).make_invoice(vals)								
			for i in res:
				i.write({'personalizadas_id':  vals.get('personalizadas_id')})
				if not res.personalizadas_id:
					res.cuenta_p_p=False
			return res
		
	def validate_account_custom(self,val):
		for i in self:
			custom = i.env['account.personalizadas'].search([('name','=',val),('p_type','=', 'asset_receivable' if i.type_import in ('out_invoice','out_refund') else 'liability_payable')],limit=1)
			if custom:
				return custom.id
			else:
				raise UserError("No se encuentro la cuenta personalizada")