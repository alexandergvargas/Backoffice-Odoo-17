# -*- encoding: utf-8 -*-
from odoo import models, fields, exceptions, api, _
import tempfile
import binascii
import xlrd
from odoo.exceptions import UserError
import base64

class ImportTemplateBbss(models.TransientModel):
	_name = 'import.template.bbss'
	_description = 'Importa y Actualiza'

	name = fields.Char('name')
	gratification_id = fields.Many2one('hr.gratification', string='Gratificacion', readonly=True)
	cts_id = fields.Many2one('hr.cts', string='CTS', readonly=True)
	# fortnight_id = fields.Many2one('hr.quincenales', string='Quincena', readonly=True)
	file = fields.Binary('Excel')
	name_file = fields.Char('name_file')
	# type = fields.Selection([
	# 	('income', 'Ingresos'),
	# 	('discounts', 'Descuentos'),
	# 	('out_of_fortnight', 'Fuera de Quincena')
	# ], string='Tipo', default="income")

	def value_fields(self,code):
		# for i in self:
		data = self.env['hr.employee'].sudo().search([('identification_id', '=', code)],limit=1)
		print("data",data)
		if data:
			return data.id
		else:
			raise UserError (u'No se encontro el empleado identificado con (%s)'%(code))


	def action_update(self):
		if self:
			try:
				file_string = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
				file_string.write(binascii.a2b_base64(self.file))
				file_string.close()
				book = xlrd.open_workbook(file_string.name)
				sheet = book.sheet_by_index(0)
			except:
				raise UserError(_("Por favor elija el archivo correcto"))
			starting_line = True
			cont=0
			errors = ''
			for i in range(sheet.nrows):
				if starting_line:
					starting_line = False
				else:
					line = list(sheet.row_values(i))
					# print("line",line)
					cont += 1
					if line[0]:
						employee = self.value_fields(line[0].strip())
						employee_id = self.env['hr.employee'].sudo().search([('id', '=', employee)],limit=1)
						# print("employee_id",employee_id)
						if self.gratification_id:
							lines = []
							if not line[1]:
								lines.append((0, 0, {'employee_id': employee,
													 'contract_id': employee_id.contract_id.id,
													 'admission_date': employee_id.contract_id.date_start,
													 'distribution_id': employee_id.contract_id.distribution_id.name,
													 'months': int(line[3]),
													 'days': int(line[4]),
													 'lacks': int(line[5]),
													 'wage': float(line[6]),
													 'household_allowance': float(line[7]),
													 'commission': float(line[8]),
													 'bonus': float(line[9]),
													 'extra_hours': float(line[10]),
													 'preserve_record': True,
													 }))
								# print("lines",lines)
								self.gratification_id.write({'line_ids': lines})
							else:
								gratification_line = self.gratification_id.line_ids.filtered(lambda l: l.id == int(line[1]))
								# print("gratification_line",gratification_line)
								if gratification_line:
									gratification_line.months = int(line[3])
									gratification_line.days = int(line[4])
									gratification_line.lacks = int(line[5])
									gratification_line.wage = float(line[6])
									gratification_line.household_allowance = float(line[7])
									gratification_line.commission = float(line[8])
									gratification_line.bonus = float(line[9])
									gratification_line.extra_hours = float(line[10])
									gratification_line.preserve_record = True

						elif self.cts_id:
							lines = []
							if not line[1]:
								lines.append((0, 0, {'employee_id': employee,
													 'contract_id': employee_id.contract_id.id,
													 'admission_date': employee_id.contract_id.date_start,
													 'distribution_id': employee_id.contract_id.distribution_id.name,
													 'months': int(line[3]),
													 'days': int(line[4]),
													 'lacks': int(line[5]),
													 'wage': float(line[6]),
													 'household_allowance': float(line[7]),
													 'sixth_of_gratification': float(line[8]),
													 'commission': float(line[9]),
													 'bonus': float(line[10]),
													 'extra_hours': float(line[11]),
													 'preserve_record': True,
													 }))
								self.cts_id.write({'line_ids': lines})
							else:
								cts_line = self.cts_id.line_ids.filtered(lambda l: l.id == int(line[1]))
								if cts_line:
									cts_line.months = int(line[3])
									cts_line.days = int(line[4])
									cts_line.lacks = int(line[5])
									cts_line.wage = float(line[6])
									cts_line.household_allowance = float(line[7])
									cts_line.sixth_of_gratification = float(line[8])
									cts_line.commission = float(line[9])
									cts_line.bonus = float(line[10])
									cts_line.extra_hours = float(line[11])
									cts_line.preserve_record = True
						else:
							pass
					else:
						errors += 'Esta plantilla no tiene ningun Trabajador cargado en la fila %s\n\n'%(str(cont))
			if errors != '':
				raise UserError(_(errors))

			return self.env['popup.it'].get_message('SE ACTUALIZÓ CORRECTAMENTE SUS REGISTROS')


	def download_template(self):
		for i in self:
			if i.gratification_id:
				return {
					'type' : 'ir.actions.act_url',
					'url': '/web/binary/download_template_update_gratification/%d'%(i.gratification_id.id),
					'target': 'new',
				}
			elif i.cts_id:
				return {
					'type' : 'ir.actions.act_url',
					'url': '/web/binary/download_template_update_cts/%d'%(i.cts_id.id),
					'target': 'new',
				}
			else:
				pass
			