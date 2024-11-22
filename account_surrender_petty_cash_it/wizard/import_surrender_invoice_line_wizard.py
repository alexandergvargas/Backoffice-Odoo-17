# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta
import tempfile
import binascii
import pytz
import xlrd
from odoo.exceptions import UserError
from odoo import models, fields, exceptions, api, _
import logging
_logger = logging.getLogger(__name__)
import io
try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')
try:
	import xlwt
except ImportError:
	_logger.debug('Cannot `import xlwt`.')
try:
	import cStringIO
except ImportError:
	_logger.debug('Cannot `import cStringIO`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')

class ImportSurrenderInvoiceLineWizard(models.TransientModel):
	_name = 'import.surrender.invoice.line.wizard'

	spt_id = fields.Many2one('account.surrender.petty.cash.it',string=u'Rendicion/Caja')
	document_file = fields.Binary(string='Excel')
	name_file = fields.Char(string='Nombre de Archivo')

	def importar(self):
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.document_file))
			fp.seek(0)
			values = {}
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)

		except:
			raise UserError("Archivo invalido!")

		lineas = []

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 12:
					date_string = None
					if line[1] != '':
						fecha_base = datetime(1900, 1, 1, tzinfo=pytz.timezone('UTC'))
						delta = timedelta(days=int(float(line[1]))-2)
						date_string = fecha_base + delta
					invoice_date_string = None
					if line[2] != '':
						fecha_base = datetime(1900, 1, 1, tzinfo=pytz.timezone('UTC'))
						delta = timedelta(days=int(float(line[2]))-2)
						invoice_date_string = fecha_base + delta
					invoice_date_due_string = None
					if line[3] != '':
						fecha_base = datetime(1900, 1, 1, tzinfo=pytz.timezone('UTC'))
						delta = timedelta(days=int(float(line[3]))-2)
						invoice_date_due_string = fecha_base + delta
					
					values.update( {'partner_id': line[0],
								'date':date_string,
								'invoice_date':invoice_date_string,
								'invoice_date_due':invoice_date_due_string,
								'currency_id': line[4] if line[4] else 'PEN',
								'type_document_id': line[5],
								'nro_comp':line[6],
								'product_id':line[7],
								'name':line[8],
								'price': line[9],
								'tax_id': line[10],
								'tc':line[11]
								})
				elif len(line) > 12:
					raise UserError('Tu archivo tiene columnas mas columnas de lo esperado.')
				else:
					raise UserError('Tu archivo tiene columnas menos columnas de lo esperado.')

				lineas.append(self.create_surrender_invoice_line(values))

		self.spt_id.write({'invoice_ids': lineas})
		return {'type': 'ir.actions.act_window_close'}

	def create_surrender_invoice_line(self,values):
		if values.get("partner_id") == "":
			raise UserError('El campo de Proveedor no puede estar vacío.')

		partner_id = None
		type_document_id = None
		currency_id = None
		product_id = None
		tax_id = None

		if values.get("partner_id"):
			s = str(values.get("partner_id"))
			vat = s.rstrip('0').rstrip('.') if '.' in s else s
			partner_id = self.find_partner(vat) if vat else None

		if values.get("product_id"):
			s = str(values.get("product_id"))
			code = s.rstrip('0').rstrip('.') if '.' in s else s
			product_id = self.find_product(code) if code else None

		if values.get("type_document_id"):
			s = str(values.get("type_document_id"))
			code = s.rstrip('0').rstrip('.') if '.' in s else s
			type_document_id = self.find_type_document(code)
		
		if values.get("currency_id"):
			currency_id = self.find_currency(values.get('currency_id'))
		
		if values.get("tax_id"):
			tax_id = self.env['account.tax'].search([('name', '=', values.get("tax_id")), ('type_tax_use', '=', 'purchase'),('company_id','=',self.spt_id.company_id.id)])

		vals = (0,0,{
			'partner_id': partner_id.id,
			'date': values.get("date"),
			'invoice_date': values.get("invoice_date"),
			'invoice_date_due': values.get("invoice_date_due"),
			'currency_id': currency_id.id,
			'type_document_id': type_document_id.id if type_document_id else None,
			'nro_comp': values.get("nro_comp"),
			'product_id':product_id.id if product_id else None,
			'name': values.get("name"),
			'price': float(values.get("price")) if values.get("price") else 0,
			'tax_id': tax_id.id if tax_id else None,
			'tc': float(values.get("tc")) if values.get("tc") else 0,
		})
		return vals
	
	def find_partner(self, name):
		partner_obj = self.env['res.partner']
		partner_search = partner_obj.search([('vat', '=', str(name))],limit=1)
		if partner_search:
			return partner_search
		else:
			raise UserError('No existe un Partner con el Nro de Documento "%s"' % name)
	
	def find_product(self, code):
		product_obj = self.env['product.product']
		product_search = product_obj.search([('default_code', '=', str(code))],limit=1)
		if product_search:
			return product_search
		else:
			raise UserError('No existe un Producto con el Codigo Interno "%s"' % code)

	def find_currency(self, name):
		currency_obj = self.env['res.currency']
		currency_search = currency_obj.search([('name', '=', name)],limit=1)
		if currency_search:
			return currency_search
		else:
			raise UserError(_(' "%s" Moneda no disponible.') % name)
		
	def find_type_document(self,code):
		catalog_payment_search = self.env['l10n_latam.document.type'].search([('code', '=', str(code))],limit=1)
		if catalog_payment_search:
			return catalog_payment_search
		else:
			raise UserError('No existe un Tipo de Comprobante con el Codigo "%s"' % code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_invoice_surrender_line',
			 'target': 'new',
			 }