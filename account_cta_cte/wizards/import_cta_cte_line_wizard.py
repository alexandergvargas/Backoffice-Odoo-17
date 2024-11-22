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

class ImportCtaCteLineWizard(models.TransientModel):
	_name = 'import.cta.cte.line.wizard'

	cta_cte_id = fields.Many2one('account.cta.cte',string='SI',required=True)
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
				if len(line) == 13:
					invoice_date_format=None
					if line[0] != '':
						fecha_base = datetime(1900, 1, 1, tzinfo=pytz.timezone('UTC'))
						delta = timedelta(days=int(float(line[9]))-2)
						invoice_date_format = fecha_base + delta
					date_maturity_format=None
					if line[0] != '':
						fecha_base = datetime(1900, 1, 1, tzinfo=pytz.timezone('UTC'))
						delta = timedelta(days=int(float(line[10]))-2)
						date_maturity_format = fecha_base + delta
					
					values.update( {
					 			'journal_id': line[0],
								'account_id': line[1],
								'debit': line[2],
								'credit': line[3],
								'currency_id': (line[4] or 'PEN'),
								'amount_currency':line[5],
								'partner_id':line[6],
								'type_document_id':line[7],
								'nro_comp':line[8],
								'invoice_date':invoice_date_format,
								'date_maturity':date_maturity_format,
								'name':line[11],
								'invoice_user_id':line[12]
								})
				elif len(line) > 13:
					raise UserError('Tu archivo tiene columnas mas columnas de lo esperado.')
				else:
					raise UserError('Tu archivo tiene columnas menos columnas de lo esperado.')

				lineas.append(self.create_journal_entry_line(values))

		self.cta_cte_id.write({'line_ids': lineas})
		return {'type': 'ir.actions.act_window_close'}

	def create_journal_entry_line(self,values):
		if values.get("account_id") == "":
			raise UserError('El campo de account_id no puede estar vacío.')

		type_document_id = None
		partner_id = None
		invoice_user_id = None
		journal_id = None

		if values.get("type_document_id"):
			s = str(values.get("type_document_id"))
			code_no = s.rstrip('0').rstrip('.') if '.' in s else s
			type_document_id = self.find_type_document(code_no)

		if values.get("partner_id"):
			s = str(values.get("partner_id"))
			vat = s.rstrip('0').rstrip('.') if '.' in s else s
			partner_id = self.find_partner(vat) if vat else None

		if values.get("invoice_user_id"):
			invoice_user_id = self.find_res_user(values.get("invoice_user_id"))
		
		if values.get("journal_id"):
			journal_id = self.find_journal(values.get("journal_id"))

		account_id = self.find_account(values.get("account_id"))

		currency = self.env['res.currency'].search([('name','=',values.get("currency_id"))],limit=1)
		vals = (0,0,{
			'journal_id': journal_id.id if journal_id else None,
			'account_id': account_id.id if account_id else None,
			'debit': float(values.get("debit")) if values.get("debit") else 0,
			'credit': float(values.get("credit")) if values.get("credit") else 0,
			'currency_id': currency.id,
			'amount_currency': float(values.get("amount_currency")) if values.get("amount_currency") else 0,
			'partner_id': partner_id.id if partner_id else None,
			'type_document_id':type_document_id.id if type_document_id else None,
			'nro_comp': values.get("nro_comp"),
			'invoice_date':values.get("invoice_date"),
			'date_maturity':values.get("date_maturity"),
			'glosa': values.get("name"),
			'invoice_user_id': invoice_user_id.id if invoice_user_id else None
		})
		return vals
	
	def find_partner(self, name):
		partner_obj = self.env['res.partner']
		partner_search = partner_obj.search([('vat', '=', name)],limit=1)
		if partner_search:
			return partner_search
		else:
			raise UserError('No existe un Partner con el Nro de Documento "%s"'% name) 

	def find_account(self, code):
		account_obj = self.env['account.account']
		account_search = account_obj.search([('code', '=', code),('company_id','=',self.cta_cte_id.company_id.id)],limit=1)
		if account_search:
			return account_search
		else:
			raise UserError('No existe una Cuenta con el Codigo "%s" en esta Compañia'% code)

	def find_type_document(self,code):
		td_search = self.env['l10n_latam.document.type'].search([('code', '=', code)],limit=1)
		if td_search:
			return td_search
		else:
			raise UserError('No existe un Tipo de Comprobante con el Codigo "%s"'% code)
		
	def find_res_user(self,name):
		user_search = self.env['res.users'].search([('name', '=', name)],limit=1)
		if user_search:
			return user_search
		else:
			raise UserError('No existe un Usuario con el nombre "%s"'% name)

	def find_journal(self,code):
		journal_search = self.env['account.journal'].search([('code','=',code),('company_id','=',self.cta_cte_id.company_id.id)],limit=1)
		if journal_search:
			return journal_search
		else:
			raise UserError(_('No existe el diario "%s" en la Compañia.') % code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_cta_cte_line',
			 'target': 'new',
			 }