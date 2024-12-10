# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
import subprocess

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])
try:
	from xlrd import *
except:
	install('xlrd')

class HrImportWizard(models.TransientModel):
	_inherit = 'hr.import.wizard'

	def get_employee_template(self):
		import io
		from xlsxwriter.workbook import Workbook
		Employee = self.env['hr.employee']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'PLANTILLA DE EMPLEADOS.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('EMPLEADOS')
		worksheet.set_tab_color('blue')
		HEADERS = ['NOMBRES(R)', 'APELLIDO PATERNO(R)', 'APELLIDO MATERNO(R)', 'CELULAR DE TRABAJO', 'TELEFONO DE TRABAJO', 'CORREO LABORAL',
				   'DEPARTAMENTO(R)', 'PUESTO DE TRABAJO(R)', 'UBICACION DE TRABAJO', 'HORARIO DE TRABAJO(R)', 'TIPO DE DOCUMENTO(R)', 'NRO IDENTIFICACION(R)',
				   'SEXO(R)', 'FECHA DE NACIMIENTO', 'LUGAR DE NACIMIENTO', 'PAIS DE NACIMIENTO', 'CONDICION(R)','NACIONALIDAD', 'DOMICILIO', 'ESTADO CIVIL(R)',
				   'NRO DE HIJOS', 'NRO DE CUENTA SUELDO/CCI', 'BANCO PARA SUELDOS', 'NRO DE CUENTA CTS/CCI', 'BANCO PARA CTS']
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
		worksheet.write(1, 0, 'JUAN CARLOS', formats['especial1'])
		worksheet.write(1, 1, 'GARCIA', formats['especial1'])
		worksheet.write(1, 2, 'LOPEZ', formats['especial1'])
		worksheet.write(1, 3, '998836898', formats['especial1'])
		worksheet.write(1, 4, '054-465632', formats['especial1'])
		worksheet.write(1, 5, 'juan@gmail.com', formats['especial1'])
		worksheet.write(1, 6, 'CONTABILIDAD', formats['especial1'])
		worksheet.write(1, 7, 'Asistente Contable', formats['especial1'])
		worksheet.write(1, 8, "Oficina", formats['especial1'])
		worksheet.write(1, 9, "Jornada Laboral 6 dias", formats['especial1'])
		worksheet.write(1, 10, 'DNI', formats['especial1'])
		worksheet.write(1, 11, '75123456', formats['especial1'])
		worksheet.write(1, 12, 'Male', formats['especial1'])
		worksheet.write(1, 13, '', formats['especial1'])
		worksheet.write(1, 14, 'Hospital Goyeneche', formats['especial1'])
		worksheet.write(1, 15, 'Perú', formats['especial1'])
		worksheet.write(1, 16, 'Domiciliado', formats['especial1'])
		worksheet.write(1, 17, 'Perú', formats['especial1'])
		worksheet.write(1, 18, 'Av. Ejercito 201', formats['especial1'])
		worksheet.write(1, 19, 'Single', formats['especial1'])
		worksheet.write(1, 20, 2, formats['especial1'])
		worksheet.write(1, 21, '19146612479019', formats['especial1'])
		worksheet.write(1, 22, 'BCP', formats['especial1'])
		worksheet.write(1, 23, '00219112068687002653', formats['especial1'])
		worksheet.write(1, 24, 'BANBIF', formats['especial1'])

		worksheet.data_validation('G2', {'validate': 'list',
										 'source': self.env['hr.department'].search([]).mapped('name')})
		worksheet.data_validation('H2', {'validate': 'list',
										 'source': self.env['hr.job'].search([]).mapped('name')})
		worksheet.data_validation('I2', {'validate': 'list',
										 'source': self.env['hr.work.location'].search([]).mapped('name')})
		worksheet.data_validation('J2', {'validate': 'list',
										 'source': self.env['resource.calendar'].search([]).mapped('name')})
		worksheet.data_validation('K2', {'validate': 'list',
										 'source': self.env['hr.type.document'].search([]).mapped('name')})
		worksheet.data_validation('M2', {'validate': 'list',
										 'source': list(dict(Employee._fields['gender'].selection).values())})
		worksheet.data_validation('P2', {'validate': 'list',
										 'source': self.env['res.country'].search([('code', 'in',['PE', 'BR', 'VE', 'CL', 'EC', 'AR', 'UY', 'PY', 'BO', 'MX', 'US'])]).mapped('name')})
		worksheet.data_validation('Q2', {'validate': 'list',
										 'source': list(dict(Employee._fields['condition'].selection).values())})
		worksheet.data_validation('R2', {'validate': 'list',
										 'source': self.env['res.country'].search([('code', 'in',['PE', 'BR', 'VE', 'CL', 'EC', 'AR', 'UY', 'PY', 'BO', 'MX', 'US'])]).mapped('name')})
		worksheet.data_validation('T2', {'validate': 'list',
										 'source': list(dict(Employee._fields['marital'].selection).values())})
		worksheet.data_validation('W2', {'validate': 'list',
										 'source': self.env['res.bank'].search([], limit=10).mapped('name')})
		worksheet.data_validation('Y2', {'validate': 'list',
										 'source': self.env['res.bank'].search([], limit=10).mapped('name')})
		widths = [25] + 25 * [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		worksheet = workbook.add_worksheet('DEPARTAMENTOS')
		worksheet.set_tab_color('green')
		worksheet.write(0, 0, 'NOMBRE', formats['boldbord'])
		widths = [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		worksheet = workbook.add_worksheet('PUESTOS DE TRABAJO')
		worksheet.set_tab_color('yellow')
		worksheet.write(0, 0, 'NOMBRE', formats['boldbord'])
		widths = [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		worksheet = workbook.add_worksheet('BANCOS')
		worksheet.set_tab_color('orange')
		worksheet.write(0, 0, 'NOMBRE', formats['boldbord'])
		worksheet.write(0, 1, 'CODIGO DEL BANCO', formats['boldbord'])
		worksheet.write(0, 2, 'FORMATO TXT', formats['boldbord'])

		worksheet.write(1, 0, 'BCP', formats['especial1'])
		worksheet.write(1, 1, '002', formats['especial1'])
		worksheet.write(1, 2, 'Formato BCP', formats['especial1'])
		worksheet.write(2, 0, 'BANBIF', formats['especial1'])
		worksheet.write(2, 1, '002', formats['especial1'])
		worksheet.write(2, 2, 'Formato BCP', formats['especial1'])

		worksheet.data_validation('C2', {'validate': 'list',
										 'source': list(dict(self.env['res.bank']._fields['format_bank'].selection).values())})
		widths = 3 * [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		worksheet = workbook.add_worksheet('CUENTAS BANCARIAS')
		worksheet.set_tab_color('purple')
		worksheet.write(0, 0, 'NUMERO DE CUENTA/CCI', formats['boldbord'])
		worksheet.write(0, 1, 'BANCO', formats['boldbord'])
		worksheet.write(0, 2, 'TIPO DE CUENTA', formats['boldbord'])
		worksheet.write(0, 3, 'MONEDA', formats['boldbord'])
		worksheet.write(0, 4, 'N° DE IDENT. EMPLEADO', formats['boldbord'])

		worksheet.write(1, 0, '19146612479019', formats['especial1'])
		worksheet.write(1, 1, 'BCP', formats['especial1'])
		worksheet.write(1, 2, 'Ahorros', formats['especial1'])
		worksheet.write(1, 3, 'PEN', formats['especial1'])
		worksheet.write(1, 4, '75123456', formats['especial1'])
		worksheet.write(2, 0, '00219112068687002653', formats['especial1'])
		worksheet.write(2, 1, 'BANBIF', formats['especial1'])
		worksheet.write(2, 2, 'CCI', formats['especial1'])
		worksheet.write(2, 3, 'PEN', formats['especial1'])
		worksheet.write(2, 4, '75123456', formats['especial1'])

		worksheet.data_validation('C2', {'validate': 'list',
										 'source': list(dict(self.env['res.partner.bank']._fields['type_of_account'].selection).values())})
		worksheet.data_validation('D2', {'validate': 'list',
										 'source': self.env['res.currency'].search([('active', '=', True)]).mapped('name')})
		widths = 5 * [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		workbook.close()

		f = open(route + 'PLANTILLA DE EMPLEADOS.xlsx', 'rb')
		return self.env['popup.it'].get_file('PLANTILLA DE EMPLEADOS.xlsx', base64.encodebytes(b''.join(f.readlines())))

	def verify_account_sheet(self, account_sheet):
		log = ''
		for i in range(1, account_sheet.nrows):
			j = i + 1
			if not self.env['res.bank'].search([('name', '=', account_sheet.cell_value(i, 1))], limit=1):
				log += 'El Banco de la linea %d de la hoja CUENTAS BANCARIAS no existe en el sistema\n' % j
			if account_sheet.cell_value(i, 2) not in list(dict(self.env['res.partner.bank']._fields['type_of_account'].selection).values()):
				log += 'El Tipo de Cuenta de la linea %d de la hoja CUENTAS BANCARIAS no existe en el sistema\n' % j
			if not self.env['res.currency'].search([('name', '=', account_sheet.cell_value(i, 3))], limit=1):
				log += 'La Moneda de la linea %d de la hoja CUENTAS BANCARIAS no existe en el sistema\n' % j
			if not self.env['res.partner'].search([('vat', '=', self.parse_xls_float(account_sheet.cell_value(i, 4)))], limit=1):
				log += 'Falta el N° de identificacion del empleado en la linea %d de la hoja CUENTAS BANCARIAS\n' % j
		if log:
			raise UserError('Se han detectado los siguientes errores:\n' + log)

	def import_employee_template(self):
		if not self.file:
			raise UserError('Es necesario especificar un archivo de importacion para este proceso')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'Import_Employee_Template.xlsx'
		Company = self.env.company
		Employee = self.env['hr.employee']
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.file))
		tmp.close()
		wb = open_workbook(route)
		####DEPARTMENT SHEET####
		department_sheet = wb.sheet_by_index(1)
		if department_sheet.ncols != 1:
			raise UserError('La hoja de DEPARTAMENTOS debe tener solo 1 columna.')
		for i in range(1, department_sheet.nrows):
			Department = self.env['hr.department'].search([('name', '=', department_sheet.cell_value(i, 0))], limit=1)
			if not Department:
				self.env['hr.department'].create({'name': department_sheet.cell_value(i, 0)})

		####JOB SHEET####
		job_sheet = wb.sheet_by_index(2)
		if job_sheet.ncols != 1:
			raise UserError('La hoja de PUESTOS DE TRABAJO debe tener solo 1 columna.')
		for i in range(1, job_sheet.nrows):
			Job = self.env['hr.job'].search([('name', '=', job_sheet.cell_value(i, 0))], limit=1)
			if not Job:
				self.env['hr.job'].create({'name': job_sheet.cell_value(i, 0)})

		####BANK SHEET####
		bank_sheet = wb.sheet_by_index(3)
		FormatBank = dict(self.env['res.bank']._fields['format_bank'].selection)
		if bank_sheet.ncols != 3:
			raise UserError('La hoja de BANCOS debe tener solo 3 columnas.')
		for i in range(1, bank_sheet.nrows):
			Bank = self.env['res.bank'].search([('name', '=', bank_sheet.cell_value(i, 0))], limit=1)
			if not Bank:
				self.env['res.bank'].create({'name': bank_sheet.cell_value(i, 0),
											 'bic': bank_sheet.cell_value(i, 1),
											 'format_bank': [key for key, val in FormatBank.items() if val == bank_sheet.cell_value(i, 2)][0]})

		####ACCOUNT SHEET####
		employee_sheet = wb.sheet_by_index(0)
		self.verify_partner_sheet(employee_sheet)
		for i in range(1, employee_sheet.nrows):
			partner = self.env['res.partner'].search([('vat', '=', self.parse_xls_float(employee_sheet.cell_value(i, 11)))], limit=1)
			# print("partner", partner.name)
			if not partner:
				self.env['res.partner'].create({
					'is_company': False,
					'type': 'contact',
					'name': employee_sheet.cell_value(i,1) + ' ' + employee_sheet.cell_value(i, 2) + ' ' + employee_sheet.cell_value(i, 0),
					'street': employee_sheet.cell_value(i, 17),
					'email': employee_sheet.cell_value(i, 5),
					'phone': self.parse_xls_float(employee_sheet.cell_value(i, 4)),
					'mobile': self.parse_xls_float(employee_sheet.cell_value(i, 3)),
					'l10n_latam_identification_type_id': self.env['l10n_latam.identification.type'].search([('name', '=', employee_sheet.cell_value(i, 10))], limit=1).id,
					'vat': self.parse_xls_float(employee_sheet.cell_value(i, 11)),
					'ref': self.parse_xls_float(employee_sheet.cell_value(i, 11)),
					'country_id': self.env['res.country'].search([('name', '=', employee_sheet.cell_value(i, 17))], limit=1).id,
					'function': employee_sheet.cell_value(i, 7),
					'employee': True,
					'is_employee': True, #campos personalizados
					'name_p': employee_sheet.cell_value(i, 0),
					'last_name': employee_sheet.cell_value(i, 1),
					'm_last_name': employee_sheet.cell_value(i, 2),
				})

		account_sheet = wb.sheet_by_index(4)
		self.verify_account_sheet(account_sheet)
		TypeAccount = dict(self.env['res.partner.bank']._fields['type_of_account'].selection)
		if account_sheet.ncols != 5:
			raise UserError('La hoja de CUENTAS BANCARIAS debe tener solo 5 columnas.')
		for i in range(1, account_sheet.nrows):
			acc_number = self.parse_xls_float(account_sheet.cell_value(i, 0))
			PartnerBank = self.env['res.partner.bank'].search([('acc_number', '=', acc_number)], limit=1)
			if not PartnerBank:
				self.env['res.partner.bank'].create({
					'acc_number': acc_number,
					'company_id': Company.id,
					'bank_id': self.env['res.bank'].search([('name', '=', account_sheet.cell_value(i, 1))], limit=1).id,
					'type_of_account': [key for key, val in TypeAccount.items() if val == account_sheet.cell_value(i, 2)][0],
					'currency_id': self.env['res.currency'].search([('name', '=', account_sheet.cell_value(i, 3))],limit=1).id,
					'partner_id': self.env['res.partner'].search([('vat', '=', self.parse_xls_float(account_sheet.cell_value(i, 4)))], limit=1).id
				})

		####EMPLOYEE SHEET####
		# employee_sheet = wb.sheet_by_index(0)
		self.verify_employee_sheet(employee_sheet, wb.datemode)
		Condition = dict(Employee._fields['condition'].selection)
		Gender = dict(Employee._fields['gender'].selection)
		Marital = dict(Employee._fields['marital'].selection)
		if employee_sheet.ncols != 25:
			raise UserError('La hoja de EMPLEADOS debe tener solo 25 columnas.')
		for i in range(1, employee_sheet.nrows):
			Resource = self.env['resource.resource'].create({'name': '%s %s %s' % (
			employee_sheet.cell_value(i, 1), employee_sheet.cell_value(i, 2), employee_sheet.cell_value(i, 0))})
			WageBank = CTSBank = Bankrem = bankcts = None
			if employee_sheet.cell_value(i, 21):
				WageBank = self.env['res.partner.bank'].search([('acc_number', '=', self.parse_xls_float(employee_sheet.cell_value(i, 21)))], limit=1).id
			if employee_sheet.cell_value(i, 22):
				Bankrem = self.env['res.bank'].search([('name', '=', self.parse_xls_float(employee_sheet.cell_value(i, 22)))], limit=1).id
			if employee_sheet.cell_value(i, 23):
				CTSBank = self.env['res.partner.bank'].search([('acc_number', '=', self.parse_xls_float(employee_sheet.cell_value(i, 23)))], limit=1).id
			if employee_sheet.cell_value(i, 24):
				bankcts = self.env['res.bank'].search([('name', '=', self.parse_xls_float(employee_sheet.cell_value(i, 24)))], limit=1).id

			self.env['hr.employee'].create({
				'resource_id': Resource.id,
				'user_partner_id': self.env['res.partner'].search([('vat', '=', self.parse_xls_float(employee_sheet.cell_value(i, 11)))], limit=1).id,
				'names': employee_sheet.cell_value(i, 0),
				'last_name': employee_sheet.cell_value(i, 1),
				'm_last_name': employee_sheet.cell_value(i, 2),
				'mobile_phone': self.parse_xls_float(employee_sheet.cell_value(i, 3)),
				'work_phone': self.parse_xls_float(employee_sheet.cell_value(i, 4)),
				'work_email': employee_sheet.cell_value(i, 5),
				'company_id': Company.id,
				'department_id': self.env['hr.department'].search([('name', '=', employee_sheet.cell_value(i, 6))], limit=1).id,
				'job_id': self.env['hr.job'].search([('name', '=', employee_sheet.cell_value(i, 7))], limit=1).id,
				'job_title': employee_sheet.cell_value(i, 7),
				'work_location_id': self.env['hr.work.location'].search([('name', '=', employee_sheet.cell_value(i, 8))], limit=1).id if employee_sheet.cell_value(i, 8) else None,
				'resource_calendar_id': self.env['resource.calendar'].search([('name', '=', employee_sheet.cell_value(i, 9))], limit=1).id,
				'type_document_id': self.env['hr.type.document'].search([('name', '=', employee_sheet.cell_value(i, 10))], limit=1).id,
				'identification_id': self.parse_xls_float(employee_sheet.cell_value(i, 11)),
				'gender': [key for key, val in Gender.items() if val == employee_sheet.cell_value(i, 12)][0],
				'birthday': xldate.xldate_as_datetime(employee_sheet.cell_value(i, 13), wb.datemode) if employee_sheet.cell_value(i, 13) else None,
				'place_of_birth': employee_sheet.cell_value(i, 14),
				'country_of_birth': self.env['res.country'].search([('name', '=', employee_sheet.cell_value(i, 15))], limit=1).id if employee_sheet.cell_value(i, 15) else None,
				'condition': [key for key, val in Condition.items() if val == employee_sheet.cell_value(i, 16)][0],
				'country_id': self.env['res.country'].search([('name', '=', employee_sheet.cell_value(i, 17))], limit=1).id if employee_sheet.cell_value(i, 17) else None,
				'private_street': employee_sheet.cell_value(i, 18),
				'marital': [key for key, val in Marital.items() if val == employee_sheet.cell_value(i, 19)][0],
				'children': employee_sheet.cell_value(i, 20),
				'wage_bank_account_id': WageBank,
				'bank_export_paymet': Bankrem,
				'cts_bank_account_id': CTSBank,
				'bank_export_cts': bankcts
			})

		return self.env['popup.it'].get_message('Se importaron todos los empleados satisfactoriamente')