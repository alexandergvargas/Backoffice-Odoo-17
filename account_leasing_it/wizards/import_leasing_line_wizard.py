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

class ImportLeasingLineWizard(models.TransientModel):
	_name = 'import.leasing.line.wizard'
	_description = 'Import Leasing Line Wizard'

	leasing_id = fields.Many2one('account.leasing.it',string='Leasing',required=True)
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
				if len(line) == 10:
					date_string = None
					if line[1] != '':
						fecha_base = datetime(1900, 1, 1, tzinfo=pytz.timezone('UTC'))
						delta = timedelta(days=int(float(line[1]))-2)
						date_string = fecha_base + delta
					
					
					values.update( {'quote': int(float(line[0])),
								'date_due': date_string,
								'amortization': line[2],
								'interest': line[3],
								'insurance':line[4],
								'value':line[5],
								'port':line[6],
								'amount_quote':line[7],
								'tax':line[8],
								'total':line[9]
								})
				elif len(line) > 10:
					raise UserError('Tu archivo tiene columnas mas columnas de lo esperado.')
				else:
					raise UserError('Tu archivo tiene columnas menos columnas de lo esperado.')

				lineas.append(self.create_leasing_line(values))

		self.leasing_id.write({'line_ids': lineas})
		return {'type': 'ir.actions.act_window_close'}

	def create_leasing_line(self,values):
		if values.get("quote") == "":
			raise UserError('El campo de Cuota no puede estar vacío.')
		if not values.get("date_due"):
			raise UserError('El campo de Fecha de Venc. no puede estar vacío.')

		vals = (0,0,{
			'quote': values.get("quote"),
			'date_due': values.get("date_due"),
			'amortization': values.get("amortization"),
			'interest': values.get("interest"),
			'insurance': values.get("insurance"),
			'value': values.get("value"),
			'port': values.get("port"),
			'amount_quote': values.get("amount_quote"),
			'tax': values.get("tax"),
			'total': values.get("total")
		})
		return vals

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_leasing_line',
			 'target': 'new',
			 }