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

class HrImportAnalyticWizard(models.TransientModel):
	_name = 'hr.import.analytic.wizard'
	_description = 'Hr Import Analytic Wizard'

	name = fields.Char()
	file = fields.Binary(string='Archivo de Exportacion')

	def get_template(self):
		return self.get_analytic_template()

	def import_template(self):
		return self.import_analytic_template()


	def get_analytic_template(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Plantilla Distribucion Elemento9.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('DISTRIBUCION  ELEMENTO 9')
		worksheet.set_tab_color('blue')
		HEADERS = ['CODIGO CUENTA ANALITICA', 'CODIGO CUENTA CONTABLE', 'CODIGO REGLA SALARIAL']
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
		worksheet.write(1, 0, '06-S0000-003', formats['especial1'])
		worksheet.write(1, 1, '9511010110', formats['especial1'])
		worksheet.write(1, 2, 'BAS_M', formats['especial1'])

		worksheet.data_validation('C2', {'validate': 'list',
										 'source': self.env['hr.salary.rule'].search([]).mapped('code')})

		widths = 29 * [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		workbook.close()

		f = open(route + 'Plantilla Distribucion Elemento9.xlsx', 'rb')
		return self.env['popup.it'].get_file('Plantilla Distribucion Elemento9.xlsx', base64.encodebytes(b''.join(f.readlines())))

	def verify_analytic_sheet(self, regla_sheet):
		log = ''
		for i in range(1, regla_sheet.nrows):
			j = i + 1
			if not self.env['hr.salary.rule'].search([('code', '=', regla_sheet.cell_value(i, 2))], limit=1):
				log += 'La regla salarial de la linea %d de la hoja DISTRIBUCION ELEMENTO 9 no existe en el sistema\n' % j
			if not self.env['account.analytic.account'].search([('code', '=', regla_sheet.cell_value(i, 0))], limit=1):
				log += 'La cuenta analitica de la linea %d de la hoja DISTRIBUCION ELEMENTO 9 no existe en el sistema\n' % j
			if not self.env['account.account'].search([('code', '=', regla_sheet.cell_value(i, 1))], limit=1):
				log += 'La cuenta contable de la linea %d de la hoja DISTRIBUCION ELEMENTO 9 no existe en el sistema\n' % j

		if log:
			raise UserError('Se han detectado los siguientes errores:\n' + log)

	def import_analytic_template(self):
		if not self.file:
			raise UserError('Es necesario especificar un archivo de importacion para este proceso')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'Import_Elemento9_Template.xlsx'
		Company = self.env.company
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.file))
		tmp.close()
		wb = open_workbook(route)

		####DISTRIBUCION ELEMENTO 9 SHEET####
		regla_sheet = wb.sheet_by_index(0)
		self.verify_analytic_sheet(regla_sheet)

		if regla_sheet.ncols != 3:
			raise UserError('La hoja de DISTRIBUCION ELEMENTO 9 debe tener solo 3 columnas.')
		# verificacion
		log = ''
		for i in range(1, regla_sheet.nrows):
			j = i + 1
			cta_analitic_id = self.env['account.analytic.account'].search([('code', '=', regla_sheet.cell_value(i, 0))], limit=1)
			salary_id = self.env['hr.salary.rule'].search([('code', '=', regla_sheet.cell_value(i, 2))], limit=1)
			dist = self.env['hr.salary.rule.line'].search([('account_analityc', '=', cta_analitic_id.id),('salary_id', '=', salary_id.id)], limit=1)
			# print("dist",dist.account_analityc.name)
			if dist:
				log += 'La Cuenta Analitica %s de la linea %d ya existe en la hoja de distibucion del sistema\n' % (dist.account_analityc.code,j)
		if log:
			raise UserError('Se han detectado los siguientes errores:\n' + log)
		# creacion
		for i in range(1, regla_sheet.nrows):
			self.env['hr.salary.rule.line'].create({
											'salary_id': self.env['hr.salary.rule'].search([('code', '=', regla_sheet.cell_value(i, 2))], limit=1).id,
											'account_analityc': self.env['account.analytic.account'].search([('code', '=', regla_sheet.cell_value(i, 0))], limit=1).id,
											'account_id': self.env['account.account'].search([('code', '=', regla_sheet.cell_value(i, 1))], limit=1).id,
										})
		return self.env['popup.it'].get_message('Se importaron todos las distribuciones satisfactoriamente')