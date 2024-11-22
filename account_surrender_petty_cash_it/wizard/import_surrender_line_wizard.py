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

class ImportSurrenderLineWizard(models.TransientModel):
	_name = 'import.surrender.line.wizard'

	spt_id = fields.Many2one('account.surrender.petty.cash.it',string=u'Rendicion/Caja')
	type = fields.Selection([('delivery', 'Entregas'),('returns', 'Devoluciones')],string=u"Tipo Operación")
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
				if len(line) == 7:
					date_string = None
					if line[0] != '':
						fecha_base = datetime(1900, 1, 1, tzinfo=pytz.timezone('UTC'))
						delta = timedelta(days=int(float(line[0]))-2)
						date_string = fecha_base + delta
					
					values.update( {'date':date_string,
								'journal_id': line[1],
								'currency_id': line[2] if line[2] else 'PEN',
								'amount': line[3],
								'nro_comp':line[4],
								'catalog_payment_id':line[5],
								'tc':line[6]
								})
				elif len(line) > 7:
					raise UserError('Tu archivo tiene columnas mas columnas de lo esperado.')
				else:
					raise UserError('Tu archivo tiene columnas menos columnas de lo esperado.')

				lineas.append(self.create_surrender_entry_line(values))

		self.spt_id.write({'%s_ids'%self.type: lineas})
		return {'type': 'ir.actions.act_window_close'}

	def create_surrender_entry_line(self,values):
		if values.get("journal_id") == "":
			raise UserError('El campo de Diario no puede estar vacío.')

		journal_id = self.find_journal(values.get("journal_id"))
		catalog_payment_id = None
		currency_id = None

		if values.get("catalog_payment_id"):
			s = str(values.get("catalog_payment_id"))
			code_no = s.rstrip('0').rstrip('.') if '.' in s else s
			catalog_payment_id = self.find_catalog_payment(code_no) if code_no else None
		
		if values.get("currency_id"):
			currency_id = self.find_currency(values.get('currency_id'))

		vals = (0,0,{
			'journal_id': journal_id.id,
			'date': values.get("date"),
			'nro_comp': values.get("nro_comp"),
			'currency_id': currency_id.id,
			'payment_method_id': catalog_payment_id.id if catalog_payment_id else None,
			'amount': float(values.get("amount")) if values.get("amount") else 0,
			'tc': float(values.get("tc")) if values.get("tc") else 0,
			'type':self.type
		})
		return vals
	
	def find_journal(self,code):
		journal_search = self.env['account.journal'].search([('code','=',code),('company_id','=',self.spt_id.company_id.id)],limit=1)
		if journal_search:
			return journal_search
		else:
			raise UserError(_('No existe el diario "%s" en la Compañia.') % code)


	def find_currency(self, name):
		currency_obj = self.env['res.currency']
		currency_search = currency_obj.search([('name', '=', name)],limit=1)
		if currency_search:
			return currency_search
		else:
			raise UserError(_(' "%s" Moneda no disponible.') % name)
		
	def find_catalog_payment(self,code):
		catalog_payment_search = self.env['einvoice.catalog.payment'].search([('code', '=', str(code))],limit=1)
		if catalog_payment_search:
			return catalog_payment_search
		else:
			raise UserError('No existe un Medio de Pago con el Codigo "%s"' % code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_account_surrender_line',
			 'target': 'new',
			 }