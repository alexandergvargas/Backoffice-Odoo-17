# -*- coding: utf-8 -*-

import time
from datetime import datetime
import tempfile
import binascii
from unicodedata import category
import xlrd
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo.osv import osv
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

class ImportAssetWizard(models.TransientModel):
	_inherit = 'import.asset.wizard'
	

	def importar(self):
		if not self.document_file:
			raise UserError('Tiene que cargar un archivo.')
		
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.document_file))
			fp.seek(0)
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)
		except:
			raise UserError("Archivo invalido!")

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 15:
					date_string = None
					if line[5] != '':
						a1 = int(float(line[5]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					date_start_string = None
					if line[6] != '':
						a1 = int(float(line[6]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_start_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					date_at = None
					if line[6] != '':
						a1 = int(float(line[12]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_at = a1_as_datetime.date().strftime('%Y-%m-%d')
					values = ({'code':line[0],
								'name':line[1],
								'categ':line[2],
								'partner_id': line[3],
								'currency':line[4],
								'date':date_string,
								'date_start':date_start_string,
								'amount':line[7],
								'salvage_value':line[8],
								'tc':line[9],
								'amount_usd':line[10],
								'state':line[11],
								'date_at':date_at,
								'valor_at':line[13],
								'depreciacion_at':line[14],
								})
				elif len(line) > 15:
					raise UserError(_('Tu archivo tiene columnas mas columnas de lo esperado.'))
				else:
					raise UserError(_('Tu archivo tiene columnas menos columnas de lo esperado.'))
				
				self.create_asset(values)

		return self.env['popup.it'].get_message(u'SE IMPORTARON CORRECTAMENTE LOS ACTIVOS.')

	def create_asset(self, values):
		asset_obj = self.env['account.asset.asset']
		if str(values.get('categ')) == '':
			raise UserError(_('El campo "Categoria" no puede estar vacio.'))
		if str(values.get('date')) == '':
			raise UserError(_('El campo "Fecha Compra" no puede estar vacio.'))
		if str(values.get('date_start')) == '':
			raise UserError(_('El campo "Fecha Inicio Depreciacion" no puede estar vacio.'))
		if str(values.get('amount')) == '':
			raise UserError(_('El campo "Valor de Compra" no puede estar vacio.'))
		if str(values.get('currency')) == '':
			raise UserError(_('El campo "Moneda" no puede estar vacio.'))

		partner_id = False
		if str(values.get('partner_id')):
			s = str(values.get('partner_id'))
			ruc = s.rstrip('0').rstrip('.') if '.' in s else s
			partner_id = self.find_partner(ruc)
		
		category_id = self.find_categ(str(values.get('categ')))
		currency_id = self.find_currency(values.get('currency'))

		asset_id = asset_obj.create({
			'category_id': category_id.id,
			'code': values.get('code'),
			'name': values.get('name'),
			'partner_id': partner_id.id if partner_id else None,
			'currency_id': currency_id.id,
			'date': values.get('date'),
			'first_depreciation_manual_date': values.get('date_start'),
			'value': values.get('amount'),
			'salvage_value': values.get('salvage_value'),
			'tipo_cambio_d': values.get('tc'),
			'bruto_dolares': values.get('amount_usd'),
			'date_at': values.get('date_at'),
			'valor_at': values.get('valor_at'),
			'depreciacion_at': values.get('depreciacion_at'),
		})
		asset_id.onchange_category_id()
		asset_id.change_method_number()
		asset_id.change_years_depreciations()
		asset_id.compute_depreciation_board()
		if values.get('state') == 'EJECUTANDO':
			asset_id.validate()
		return asset_id

	