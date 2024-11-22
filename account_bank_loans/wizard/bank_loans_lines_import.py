# -*- coding: utf-8 -*-

import binascii
import tempfile
import xlrd
from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

class bank_loans_lines_import(models.TransientModel):
	_name = 'bank.loans.lines.import'
	_description = 'Importador Lineas de Prestamos Wizard'
	

	loan_id = fields.Many2one('bank.loans', string='Prestamo')
	file = fields.Binary('Archivo')
	name_file = fields.Char('name_file')

	def importar(self):
		if self:
			try:
				file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
				file_string.write(binascii.a2b_base64(self.file))
				book = xlrd.open_workbook(file_string.name)
				sheet = book.sheet_by_index(0)
			except:
				raise UserError(_("Por favor elija el archivo correcto"))
			starting_line = True
			cont=0
			for i in range(sheet.nrows):
				if starting_line:
					starting_line = False
				else:
					line = list(sheet.row_values(i))
					cont+=1
					
					if line[0] or line[1] or line[2] or line[3] or line[4]:	
						if line[0] == '':
							raise UserError('Por favor ingresa el campo Fecha')
						else:
							date_format = self.convert_date(line[1])	
						self.env['bank.loans.lines'].sudo().create({ 
							'loan_id': self.loan_id.id,
							'month': line[0],
							'date':date_format,
							'amount_amort': line[2],
							'inters': line[3],
							'quota': line[4],
							'amount_debt':line[5]
						})						
					else:
						raise ValidationError(_('EN LA FILA %s FALTA DATOS'%(str(cont))))
			return self.env['popup.it'].get_message('SE IMPORTARON CORRECTAMENTE SUS LINEAS DE PRESTAMO')


	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_import_loans_lines',
			 'target': 'new',
			 }

	def convert_date(self, date):
		try:
			numeric_date = float(str(date))
			seconds = (numeric_date - 25569) * 86400.0
			d = datetime.utcfromtimestamp(seconds)
			return d.strftime('%Y-%m-%d')  
		except ValueError:
			for fmt in ("%d-%m-%Y", "%Y/%m/%d", "%b %d, %Y", "%d %B %Y","%d/%m/%Y"):
				try:
					return datetime.strptime(str(date), fmt).strftime("%Y-%m-%d")
				except ValueError:
					continue
			raise UserError(f"Formato no reconocido para la fecha: {str(date)}")