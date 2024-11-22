# -*- coding: utf-8 -*-

import tempfile
import binascii
import xlrd
from odoo.exceptions import UserError
from odoo import models, fields, _

class ImportAccountWizard(models.TransientModel):
	_name = "import.account.amarr.wizard"

	file_slect = fields.Binary(string="Archivo")
	
	def import_file(self):
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.file_slect))
			fp.seek(0)
			values = {}
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)

		except:
			raise UserError(_("Archivo invalido!"))

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))

				values.update( {'code' : line[0],
								'a_debe' : line[1],
								'a_haber' : line[2],
								})

				res = self.create_chart_accounts(values)
		
		return self.env['popup.it'].get_message(u'SE ACTUALIZARON CON EXITO LAS CUENTAS')
	
	def create_chart_accounts(self,values):

		if values.get("code") == "":
			raise UserError(_('El campo de code no puede estar vacío.') )

		account_obj = self.env['account.account']
		account_search = account_obj.search([
			('code', '=', values.get("code")),('company_id','=',self.env.company.id)
			])

		if account_search:
			if values.get("a_debe") or values.get("a_debe") != "":
				a_debe = self.find_account(str(values.get('a_debe')))
				account_search.write({'a_debit':a_debe})
			if values.get("a_haber") or values.get("a_haber") != "":
				a_haber = self.find_account(str(values.get('a_haber')))
				account_search.write({'a_credit':a_haber})
			return account_search
		else:
			raise UserError(u'No existe la cuenta {account} en la compañía {company}.'.format(
				account=values.get("code"),
				company=self.env.company.name))

# --------------------cuenta--------------------

	def find_account(self,account):
		account_search = self.env['account.account'].search([('code','=',account),('company_id','=',self.env.company.id)],limit=1)
		if account_search:
			return account_search.id
		else:
			if account == "":
				pass
			else:
				raise UserError(_(' %s Cuenta Contable no disponible.') % account)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_account_amarr',
			 'target': 'new',
			 }