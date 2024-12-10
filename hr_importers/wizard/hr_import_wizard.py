# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import base64
import subprocess

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])
try:
	from xlrd import *
except:
	install('xlrd')

class HrImportWizard(models.TransientModel):
	_name = 'hr.import.wizard'
	_description = 'Import Wizard'

	name = fields.Char()
	file = fields.Binary(string='Archivo de Exportacion')
	option = fields.Selection([('employee', 'Empleados'), ('contract', 'Contratos')], default='employee', string='Opcion')

	def get_template(self):
		if self.option == 'employee':
			return self.get_employee_template()
		else:
			return self.get_contract_template()

	def import_template(self):
		if self.option == 'employee':
			return self.import_employee_template()
		else:
			return self.import_contract_template()

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
				'SEXO(R)', 'FECHA DE NACIMIENTO', 'LUGAR DE NACIMIENTO', 'PAIS DE NACIMIENTO', 'CONDICION(R)', 'NACIONALIDAD', 'DOMICILIO', 'ESTADO CIVIL(R)',
				'NRO DE HIJOS',	'NRO DE CUENTA SUELDO/CCI','BANCO PARA SUELDOS', 'NRO DE CUENTA CTS/CCI', 'BANCO PARA CTS']
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
										 'source': self.env['res.country'].search([('code','in',['PE','BR','VE','CL','EC','AR','UY','PY','BO','MX','US'])]).mapped('name')})
		worksheet.data_validation('Q2', {'validate': 'list',
										 'source': list(dict(Employee._fields['condition'].selection).values())})
		worksheet.data_validation('R2', {'validate': 'list',
										 'source': self.env['res.country'].search([('code','in',['PE','BR','VE','CL','EC','AR','UY','PY','BO','MX','US'])]).mapped('name')})
		worksheet.data_validation('T2', {'validate': 'list',
										 'source': list(dict(Employee._fields['marital'].selection).values())})
		worksheet.data_validation('W2', {'validate': 'list',
										 'source': self.env['res.bank'].search([],limit=10).mapped('name')})
		worksheet.data_validation('Y2', {'validate': 'list',
										 'source': self.env['res.bank'].search([],limit=10).mapped('name')})
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
		widths = [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)
		
		worksheet = workbook.add_worksheet('CUENTAS BANCARIAS')
		worksheet.set_tab_color('purple')
		worksheet.write(0, 0, 'NUMERO DE CUENTA', formats['boldbord'])
		worksheet.write(0, 1, 'BANCO', formats['boldbord'])
		worksheet.write(0, 2, 'MONEDA', formats['boldbord'])
		worksheet.write(0, 3, 'N° DE IDENTIFICACION', formats['boldbord'])
		worksheet.data_validation('C2', {'validate': 'list',
										 'source': self.env['res.currency'].search([('active', '=', True)]).mapped('name')})
		widths = 4 * [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		workbook.close()

		f = open(route + 'PLANTILLA DE EMPLEADOS.xlsx', 'rb')
		return self.env['popup.it'].get_file('PLANTILLA DE EMPLEADOS.xlsx', base64.encodebytes(b''.join(f.readlines())))

	def get_contract_template(self):
		import io
		from xlsxwriter.workbook import Workbook
		Contract = self.env['hr.contract']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'PLANTILLA DE CONTRATOS.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('CONTRATOS')
		worksheet.set_tab_color('blue')
		HEADERS = ['NOMBRE DEL CONTRATO(R)', 'N° IDENT. EMPLEADO(R)', 'TIPO DE PLANILLA(R)', 'ESTRUCTURA SALARIAL(R)',  'ORIGEN ENTRADA DE TRABAJO(R)',
				   'TIPO DE TRABAJADOR(R)',	'FECHA INICIO(R)', 'FECHA FINAL', 'SALARIO(R)', 'AFILIACION(R)', 'TIPO DE COMISION AFP','CUSPP', 'SEGURO SOCIAL',
				   'DISTRIBUCION ANALITICA(R)',	'SITUACION(R)', 'REGIMEN LABORAL(R)','ES TRABAJADOR PART-TIME','ES MAYOR A 65 AÑOS', 'OTROS EMPLEADORES',
				   'REM. AFECTA QUINTA A PROY.', 'GRAT. DE JULIO PROYECTADA', 'GRAT. DE DICIEMBRE PROYECTADA']
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
		worksheet.write(1, 0, 'CONTRATO 1 JUAN GARCIA LOPEZ', formats['especial1'])
		worksheet.write(1, 1, '75123456', formats['especial1'])
		worksheet.write(1, 2, 'MENSUAL', formats['especial1'])
		worksheet.write(1, 3, 'BASE', formats['especial1'])
		worksheet.write(1, 4, 'Horario de Trabajo', formats['especial1'])
		worksheet.write(1, 5, 'EMPLEADO', formats['especial1'])
		worksheet.write(1, 6, '', formats['reverse_dateformat'])
		worksheet.write(1, 7, '', formats['reverse_dateformat'])
		worksheet.write(1, 8, 2000.00, formats['numberdos'])
		worksheet.write(1, 9, 'AFP HABITAT', formats['especial1'])
		worksheet.write(1, 10, 'Flujo', formats['especial1'])
		worksheet.write(1, 11, '2351QSWR123', formats['especial1'])
		worksheet.write(1, 12, 'EsSalud', formats['especial1'])
		worksheet.write(1, 13, 'ADM_VEN', formats['especial1'])
		worksheet.write(1, 14, 'ACTIVO O SUBSIDIADO', formats['especial1'])
		worksheet.write(1, 15, 'Regimen General', formats['especial1'])
		worksheet.write(1, 16, 'NO', formats['especial1'])
		worksheet.write(1, 17, 'NO', formats['especial1'])
		worksheet.write(1, 18, 'SI', formats['especial1'])
		worksheet.write(1, 19, 0.0, formats['numberdos'])
		worksheet.write(1, 20, 0.0, formats['numberdos'])
		worksheet.write(1, 21, 0.0, formats['numberdos'])
		# print(self.env['hr.worker.type'].search([]).mapped('name'), self.env['hr.payroll.structure.type'].search([]).mapped('name'))

		worksheet.data_validation('C2', {'validate': 'list',
										 'source': self.env['hr.payroll.structure.type'].search([]).mapped('name')})
		worksheet.data_validation('D2', {'validate': 'list',
										 'source': self.env['hr.payroll.structure'].search([]).mapped('name')})
		worksheet.data_validation('E2', {'validate': 'list',
										 'source': list(dict(Contract._fields['work_entry_source'].selection).values())})
		worksheet.data_validation('F2', {'validate': 'list',
										 'source': self.env['hr.worker.type'].search([], limit=14).mapped('name')})
		worksheet.data_validation('J2', {'validate': 'list',
										 'source': self.env['hr.membership'].search([]).mapped('name')})
		worksheet.data_validation('K2', {'validate': 'list',
										 'source': list(dict(Contract._fields['commision_type'].selection).values())})
		worksheet.data_validation('M2', {'validate': 'list',
										 'source': self.env['hr.social.insurance'].search([]).mapped('name')})
		worksheet.data_validation('O2', {'validate': 'list',
										 'source': self.env['hr.situation'].search([]).mapped('name')})
		worksheet.data_validation('P2', {'validate': 'list',
										 'source': list(dict(Contract._fields['labor_regime'].selection).values())})
		widths = [30] + 21 * [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		worksheet = workbook.add_worksheet('DISTRIBUCIONES ANALITICAS')
		worksheet.set_tab_color('orange')
		worksheet.write(0, 0, 'CODIGO', formats['boldbord'])
		worksheet.write(0, 1, 'DESCRIPCION', formats['boldbord'])
		widths = 2*[18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		workbook.close()

		f = open(route + 'PLANTILLA DE CONTRATOS.xlsx', 'rb')
		return self.env['popup.it'].get_file('PLANTILLA DE CONTRATOS.xlsx', base64.encodebytes(b''.join(f.readlines())))

	def parse_xls_float(self, cell_value):
		if type(cell_value) is float:
			return str(int(cell_value))
		else:
			return cell_value

	def verify_partner_sheet(self, employee_sheet):
		log = ''
		for i in range(1, employee_sheet.nrows):
			j = i + 1
			if not employee_sheet.cell_value(i, 0) or not employee_sheet.cell_value(i, 1) or not employee_sheet.cell_value(i, 2):
				log += 'Faltan Nombres o Apellidos en la linea %d de la hoja EMPLEADOS, estos son campos obligatorios\n' % j
			if not self.env['l10n_latam.identification.type'].search([('name', '=', employee_sheet.cell_value(i, 10))], limit=1):
				log += 'El Tipo de Documento de la linea %d de la hoja EMPLEADOS no existe en el modulo de Contactos del sistema\n' % j
		if log:
			raise UserError('Se han detectado los siguientes errores:\n' + log)

	def verify_employee_sheet(self, employee_sheet, datemode):
		log = ''
		Employee = self.env['hr.employee']
		for i in range(1, employee_sheet.nrows):
			j = i + 1
			if not employee_sheet.cell_value(i, 0) or not employee_sheet.cell_value(i, 1) or not employee_sheet.cell_value(i, 2):
				log += 'Faltan Nombres o Apellidos en la linea %d de la hoja EMPLEADOS, estos son campos obligatorios\n' % j
			if not self.env['hr.department'].search([('name', '=', employee_sheet.cell_value(i, 6))], limit=1):
				log += 'El Departamento de la linea %d de la hoja EMPLEADOS no existe en el sistema\n' % j
			if not self.env['hr.job'].search([('name', '=', employee_sheet.cell_value(i, 7))], limit=1):
				log += 'El Puesto de Trabajo de la linea %d de la hoja EMPLEADOS no existe en el sistema\n' % j
			if not self.env['resource.calendar'].search([('name', '=', employee_sheet.cell_value(i, 9))], limit=1):
				log += 'El Horario de Trabajo de la linea %d de la hoja EMPLEADOS no existe en el sistema\n' % j
			if not self.env['hr.type.document'].search([('name', '=', employee_sheet.cell_value(i, 10))], limit=1):
				log += 'El Tipo de Documento de la linea %d de la hoja EMPLEADOS no existe en el sistema\n' % j
			if employee_sheet.cell_value(i, 12) not in list(dict(Employee._fields['gender'].selection).values()):
				log += 'El Sexo de la linea %d de la hoja EMPLEADOS no existe en el sistema, escoger una de las opciones del Combobox\n' % j
			try:
				if employee_sheet.cell_value(i, 13):
					xldate.xldate_as_datetime(employee_sheet.cell_value(i, 13), datemode)
			except:
				log += 'La Fecha de Nacimiento de la linea %d de la hoja EMPLEADOS tiene un problema.\n' % j
			if employee_sheet.cell_value(i, 15):
				if not self.env['res.country'].search([('name', '=', employee_sheet.cell_value(i, 15))], limit=1):
					log += 'El Pais de Nacimiento de la linea %d de la hoja EMPLEADOS no existe en el sistema\n' % j
			if employee_sheet.cell_value(i, 16) not in list(dict(Employee._fields['condition'].selection).values()):
				log += 'La Condicion de la linea %d de la hoja EMPLEADOS no existe en el sistema\n' % j
			if employee_sheet.cell_value(i, 17):
				if not self.env['res.country'].search([('name', '=', employee_sheet.cell_value(i, 15))], limit=1):
					log += 'El Pais (Nacionalidad) de la linea %d de la hoja EMPLEADOS no existe en el sistema\n' % j
			if employee_sheet.cell_value(i, 19):
				if employee_sheet.cell_value(i, 19) not in list(dict(Employee._fields['marital'].selection).values()):
					log += 'El Estado Civil de la linea %d de la hoja EMPLEADOS no existe en el sistema\n' % j
			if employee_sheet.cell_value(i, 21):
				if not self.env['res.partner.bank'].search([('acc_number', '=', self.parse_xls_float(employee_sheet.cell_value(i, 21)))], limit=1):
					log += 'El Numero de Cuenta Sueldo de la linea %d de la hoja EMPLEADOS no existe en el sistema\n' % j
			if employee_sheet.cell_value(i, 23):
				if not self.env['res.partner.bank'].search([('acc_number', '=', self.parse_xls_float(employee_sheet.cell_value(i, 23)))], limit=1):
					log += 'El Numero de Cuenta CTS de la linea %d de la hoja EMPLEADOS no existe en el sistema\n' % j
		if log:
			raise UserError('Se han detectado los siguientes errores:\n' + log)


	def verify_account_sheet(self, account_sheet):
		log = ''
		for i in range(1, account_sheet.nrows):
			j = i + 1
			if not self.env['res.bank'].search([('name', '=', account_sheet.cell_value(i, 1))], limit=1):
				log += 'El Banco de la linea %d de la hoja CUENTAS BANCARIAS no existe en el sistema\n' % j
			if not self.env['res.currency'].search([('name', '=', account_sheet.cell_value(i, 2))], limit=1):
				log += 'La Moneda de la linea %d de la hoja CUENTAS BANCARIAS no existe en el sistema\n' % j
			if not self.env['res.partner'].search([('vat', '=', self.parse_xls_float(account_sheet.cell_value(i, 3)))], limit=1):
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
		if bank_sheet.ncols != 1:
			raise UserError('La hoja de BANCOS debe tener solo 1 columna.')
		for i in range(1, bank_sheet.nrows):
			Bank = self.env['res.bank'].search([('name', '=', bank_sheet.cell_value(i, 0))], limit=1)
			if not Bank:
				self.env['res.bank'].create({'name': bank_sheet.cell_value(i, 0)})

		####ACCOUNT SHEET####
		employee_sheet = wb.sheet_by_index(0)
		self.verify_partner_sheet(employee_sheet)
		for i in range(1, employee_sheet.nrows):
			partner = self.env['res.partner'].search([('vat', '=', self.parse_xls_float(employee_sheet.cell_value(i, 9)))], limit=1)
			# print("partner", partner.name)
			if not partner:
				self.env['res.partner'].create({
					'is_company': False,
					'type': 'contact',
					'name': employee_sheet.cell_value(i,1) + ' ' + employee_sheet.cell_value(i, 2) + ' ' + employee_sheet.cell_value(i, 0),
					'street': employee_sheet.cell_value(i, 18),
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
		if account_sheet.ncols != 4:
			raise UserError('La hoja de CUENTAS BANCARIAS debe tener solo 4 columnas.')
		for i in range(1, account_sheet.nrows):
			acc_number = self.parse_xls_float(account_sheet.cell_value(i, 0))
			PartnerBank = self.env['res.partner.bank'].search([('acc_number', '=', acc_number)], limit=1)
			if not PartnerBank:
				self.env['res.partner.bank'].create({
												'acc_number': acc_number,
												'company_id': Company.id,
												'bank_id': self.env['res.bank'].search([('name', '=', account_sheet.cell_value(i, 1))], limit=1).id,
												'currency_id': self.env['res.currency'].search([('name', '=', account_sheet.cell_value(i, 2))], limit=1).id,
												'partner_id': self.env['res.partner'].search([('vat', '=', self.parse_xls_float(account_sheet.cell_value(i, 3)))], limit=1).id
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
			Resource = self.env['resource.resource'].create({'name': '%s %s %s' % (employee_sheet.cell_value(i, 1), employee_sheet.cell_value(i, 2), employee_sheet.cell_value(i, 0))})
			WageBank = CTSBank= Bankrem = bankcts = None
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

	def verify_contract_sheet(self, contract_sheet, datemode):
		log = ''
		Contract = self.env['hr.contract']
		for i in range(1, contract_sheet.nrows):
			j = i + 1
			if not contract_sheet.cell_value(i, 0) or \
			   not contract_sheet.cell_value(i, 8):
				log += 'Falta Nombre del contrato o Salario, en la linea %d de la hoja CONTRATOS, estos son campos obligatorios\n' % j
			if not self.env['hr.employee'].search([('identification_id', '=', self.parse_xls_float(contract_sheet.cell_value(i, 1)))], limit=1):
				log += 'El Empleado de la linea %d de la hoja CONTRATOS no existe en el sistema\n' % j
			if not self.env['hr.payroll.structure.type'].search([('name', '=', contract_sheet.cell_value(i, 2))], limit=1):
				log += 'El Tipo de Planilla de la linea %d de la hoja CONTRATOS no existe en el sistema\n' % j
			if not self.env['hr.payroll.structure'].search([('name', '=', contract_sheet.cell_value(i, 3))], limit=1):
				log += 'La Estructura Salarial de la linea %d de la hoja CONTRATOS no existe en el sistema\n' % j
			if contract_sheet.cell_value(i, 4) not in list(dict(Contract._fields['work_entry_source'].selection).values()):
				log += 'El Origen de Entrada de Trabajo de la linea %d de la hoja CONTRATOS no existe en el sistema\n' % j
			if not self.env['hr.worker.type'].search([('name', '=', contract_sheet.cell_value(i, 5))], limit=1):
				log += 'El Tipo de Trabajador de la linea %d de la hoja CONTRATOS no existe en el sistema\n' % j
			try:
				xldate.xldate_as_datetime(contract_sheet.cell_value(i, 6), datemode)
				if contract_sheet.cell_value(i, 7):
					xldate.xldate_as_datetime(contract_sheet.cell_value(i, 7), datemode)
			except:
				log += 'Alguna de las fechas de la linea %d de la hoja CONTRATOS tienen un problema. La fecha de inicio es Obligatorio\n' % j
			if not self.env['hr.membership'].search([('name', '=', contract_sheet.cell_value(i, 9))], limit=1):
				log += 'La Afliacion de la linea %d de la hoja CONTRATOS no existe en el sistema\n' % j
			if contract_sheet.cell_value(i, 10):
				if contract_sheet.cell_value(i, 10) not in list(dict(Contract._fields['commision_type'].selection).values()):
					log += 'El Tipo de Comision de la linea %d de la hoja CONTRATOS no existe en el sistema\n' % j
			if not self.env['hr.social.insurance'].search([('name', '=', contract_sheet.cell_value(i, 12))], limit=1):
				log += 'El Seguro Social de la linea %d de la hoja CONTRATOS no existe en el sistema\n' % j
			if not self.env['hr.analytic.distribution'].search([('name', '=', contract_sheet.cell_value(i, 13))], limit=1):
				log += 'La Distribucion Analitica de la linea %d de la hoja CONTRATOS no existe en el sistema\n' % j
			if not self.env['hr.situation'].search([('name', '=', contract_sheet.cell_value(i, 14))], limit=1):
				log += 'La Situacion de la linea %d de la hoja CONTRATOS no existe en el sistema\n' % j
			if contract_sheet.cell_value(i, 15) not in list(dict(Contract._fields['labor_regime'].selection).values()):
				log += 'El Regimen Laboral de la linea %d de la hoja CONTRATOS no existe en el sistema\n' % j
		if log:
			raise UserError('Se han detectado los siguientes errores:\n' + log)

	def import_contract_template(self):
		if not self.file:
			raise UserError('Es necesario especificar un archivo de importacion para este proceso')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'Import_Contract_Template.xlsx'
		Company = self.env.company
		Contract = self.env['hr.contract']
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.file))
		tmp.close()
		wb = open_workbook(route)

		####DISTRIBUTION SHEET####
		dist_sheet = wb.sheet_by_index(1)
		if dist_sheet.ncols != 2:
			raise UserError('La hoja de DISTRIBUCIONES ANALITICAS debe tener solo 2 columnas.')
		for i in range(1, dist_sheet.nrows):
			Distribution = self.env['hr.analytic.distribution'].search([('name', '=', dist_sheet.cell_value(i, 0))], limit=1)
			if not Distribution:
				self.env['hr.analytic.distribution'].create({'name': dist_sheet.cell_value(i, 0),
															 'description': dist_sheet.cell_value(i, 1)})

		####CONTRACT SHEET####
		contract_sheet = wb.sheet_by_index(0)
		self.verify_contract_sheet(contract_sheet, wb.datemode)
		WorkEntry = dict(Contract._fields['work_entry_source'].selection)
		Commision = dict(Contract._fields['commision_type'].selection)
		Regime = dict(Contract._fields['labor_regime'].selection)
		if contract_sheet.ncols != 22:
			raise UserError('La hoja de CONTRATOS debe tener solo 22 columnas.')
		for i in range(1, contract_sheet.nrows):
			self.env['hr.contract'].create({
				'name': contract_sheet.cell_value(i, 0),
				'state': 'open',
				'employee_id': self.env['hr.employee'].search([('identification_id', '=', self.parse_xls_float(contract_sheet.cell_value(i, 1)))], limit=1).id,
				'resource_calendar_id': self.env['hr.employee'].search([('identification_id', '=', self.parse_xls_float(contract_sheet.cell_value(i, 1)))], limit=1).resource_calendar_id.id if contract_sheet.cell_value(i, 1) else None,
				'department_id': self.env['hr.employee'].search([('identification_id', '=', self.parse_xls_float(contract_sheet.cell_value(i, 1)))], limit=1).department_id.id if contract_sheet.cell_value(i, 1) else None,
				'job_id': self.env['hr.employee'].search([('identification_id', '=', self.parse_xls_float(contract_sheet.cell_value(i, 1)))], limit=1).job_id.id if contract_sheet.cell_value(i, 1) else None,
				'company_id': Company.id,
				'structure_type_id': self.env['hr.payroll.structure.type'].search([('name', '=', contract_sheet.cell_value(i, 2))], limit=1).id,
				'structure_id': self.env['hr.payroll.structure'].search([('name', '=', contract_sheet.cell_value(i, 3))], limit=1).id,
				'work_entry_source': [key for key, val in WorkEntry.items() if val == contract_sheet.cell_value(i, 4)][0],
				'worker_type_id': self.env['hr.worker.type'].search([('name', '=', contract_sheet.cell_value(i, 5))], limit=1).id,
				'date_start': xldate.xldate_as_datetime(contract_sheet.cell_value(i, 6), wb.datemode),
				'date_end': xldate.xldate_as_datetime(contract_sheet.cell_value(i, 7), wb.datemode) if contract_sheet.cell_value(i, 7) else None,
				'wage': contract_sheet.cell_value(i, 8),
				'membership_id': self.env['hr.membership'].search([('name', '=', contract_sheet.cell_value(i, 9))], limit=1).id,
				'commision_type': [key for key, val in Commision.items() if val == contract_sheet.cell_value(i, 10)][0] if contract_sheet.cell_value(i, 10) else '',
				'cuspp': contract_sheet.cell_value(i, 11),
				'social_insurance_id': self.env['hr.social.insurance'].search([('name', '=', contract_sheet.cell_value(i, 12))], limit=1).id,
				'distribution_id': self.env['hr.analytic.distribution'].search([('name', '=', contract_sheet.cell_value(i, 13))], limit=1).id,
				'situation_id': self.env['hr.situation'].search([('name', '=', contract_sheet.cell_value(i, 14))], limit=1).id,
				'labor_regime': [key for key, val in Regime.items() if val == contract_sheet.cell_value(i, 15)][0],
				'less_than_four': True if contract_sheet.cell_value(i, 16)=='SI' else False,
				'is_older': True if contract_sheet.cell_value(i, 17)=='SI' else False,
				'other_employers': True if contract_sheet.cell_value(i, 18)=='SI' else False,
				'fifth_rem_proyected': contract_sheet.cell_value(i, 19),
				'grat_july_proyected': contract_sheet.cell_value(i, 20),
				'grat_december_proyected': contract_sheet.cell_value(i, 21)
			})

		return self.env['popup.it'].get_message('Se importaron todos los contratos satisfactoriamente')