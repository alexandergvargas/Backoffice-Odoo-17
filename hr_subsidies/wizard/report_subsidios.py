# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class ReportSubsidios(models.TransientModel):
	_name = "report.subsidios"
	_description = "Reporte Subsidios"

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	# type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF')],default='pantalla',string=u'Mostrar en', required=True)
	# payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo')
	employees_ids = fields.Many2many('hr.employee','rel_reporte_subsidios_employee','employee_id','report_id','Empleados')
	allemployees = fields.Boolean('Todos los Empleados',default=True)

	def get_all(self):
		# self.domain_dates()
		option=0
		return self.get_excel(option)

	def get_journals(self):
		# self.domain_dates()
		if self.allemployees == False:
			option=1
			return self.get_excel(option)
		else:
			raise UserError('Debe escoger al menos un Empleado.')

	def _get_sql(self,option):
		sql_employees = "and he.id in (%s) " % (','.join(str(i) for i in self.employees_ids.ids)) if option == 1 else ""
		sql = """
			select  he.id,
				he.identification_id as dni,
				he.name as trabajador,
				extract(year from hp.date_start) as year1,
				hp.name as mes,
				CASE WHEN hs.type = 'maternity' THEN 'MATERNIDAD' ELSE 'ACCIDENTE DE TRABAJO' END AS contingencia,
				CASE WHEN hs.date_start > hp.date_start THEN hs.date_start ELSE hp.date_start END AS inicio,
				CASE WHEN hs.date_end < hp.date_end THEN hs.date_end ELSE hp.date_end END AS termino,
				hsp.days as dias,
				hsp.sub_dia,
				hsp.total_sub,
				CASE WHEN hsp.validation = 'paid out' THEN hsp.total_sub ELSE 0 END AS recuperado,
				CASE WHEN hsp.validation <> 'paid out' THEN hsp.total_sub ELSE 0 END as pendiente,
				CASE WHEN hsp.validation = 'paid out' THEN 'RECUPERADO' ELSE 'CANJE PRESENTADO' END AS tramite
			from hr_subsidies_periodo hsp
			inner join hr_subsidies hs on hs.id = hsp.subsidies_id
			inner join hr_period hp on hp.id = hsp.periodo_id
			inner join hr_employee he on he.id = hsp.employee_id
			left join res_partner rp on rp.id = he.user_partner_id
			where hs.company_id = {company}
			{sql_employees}
			order by he.name
		""".format(
				company = self.company_id.id,
				sql_employees = sql_employees
			)
		return sql

	def get_excel(self,option):
		import io
		from xlsxwriter.workbook import Workbook
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		directory = MainParameter.dir_create_file

		if not directory:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		workbook = Workbook(directory + 'Reporte_subsidios.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Reporte Subsidios")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(0, 0, 0, 7, "Empresa: %s" % self.company_id.partner_id.name or '', formats['especial2'])
		worksheet.merge_range(1, 0, 1, 7, "RUC: %s" % self.company_id.partner_id.vat or '', formats['especial2'])
		worksheet.merge_range(2, 0, 2, 7, "Direccion: %s" % self.company_id.partner_id.street or '', formats['especial2'])
		worksheet.merge_range(3, 1, 3, 8, "*** REPORTE DE SUBSIDIOS ***", formats['especial5'])

		self._cr.execute(self._get_sql(option))
		data = self._cr.dictfetchall()
		# print("data",data)
		x, y = 5, 0

		# estilo personalizado
		boldbord = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		boldbord.set_border(style=1)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		# boldbord.set_align('bottom')
		boldbord.set_text_wrap()
		boldbord.set_font_size(8)
		boldbord.set_bg_color('#99CCFF')

		dateformat = workbook.add_format({'num_format':'dd-mm-yyyy'})
		dateformat.set_align('center')
		dateformat.set_align('vcenter')
		# dateformat.set_border(style=1)
		dateformat.set_font_size(8)
		dateformat.set_font_name('Times New Roman')

		formatCenter = workbook.add_format({'num_format': '0.00', 'font_name': 'Arial', 'align': 'center', 'font_size': 8})
		formatLeft = workbook.add_format({'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': 8})
		numberdos = workbook.add_format({'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		numberdos.set_font_size(8)
		styleFooterSum = workbook.add_format({'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': 9, 'top': 1, 'bottom': 2})
		styleFooterSum.set_bottom(6)

		HEADERS = ['DNI','Apellidos y Nombres','Año','Mes','Contingencia','Inicio','Termino','Dias',
				   'Subsidio Diario','Total','Monto Recuperado','Pendiente','Tramite']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,x,y,boldbord)
		x += 1

		cont = 0
		cuenta = ''
		totals = [0] * 4
		limiter = 9


		for c, line in enumerate(data, 1):
			if cont == 0:
				cuenta = line['trabajador']
				# print("cuenta",cuenta)
				cont += 1
				worksheet.merge_range(x,0,x,4, 'Empleado: ' + str(cuenta) if line['trabajador'] else '',formats['especial2'])
				x += 1

			if cuenta != line['trabajador']:
				worksheet.write(x, limiter-1, 'Total ', formats['especial2'])
				for total in totals:
					worksheet.write(x, limiter, total, styleFooterSum)
					limiter += 1

				x += 1
				totals = [0] * 4
				limiter = 9

				cuenta = line['trabajador']
				worksheet.merge_range(x,0,x,4, 'Empleado: ' + str(cuenta) if line['trabajador'] else '',formats['especial2'])
				x += 1

			# worksheet.write(x, 0, line['sede'] if line['sede'] else '', formatCenter)
			worksheet.write(x, 0, line['dni'] if line['dni'] else '', formatCenter)
			worksheet.write(x, 1, line['trabajador'] if line['trabajador'] else '', formatLeft)
			worksheet.write(x, 2, str(int(line['year1'])) if line['year1'] else '', formatCenter)
			worksheet.write(x, 3, line['mes'] if line['mes'] else '', formatCenter)
			worksheet.write(x, 4, line['contingencia'] if line['contingencia'] else '', formatLeft)
			worksheet.write(x, 5, line['inicio'] if line['inicio'] else '', dateformat)
			worksheet.write(x, 6, line['termino'] if line['termino'] else '', dateformat)
			worksheet.write(x, 7, str(line['dias']) if line['dias'] else '0', formatCenter)
			worksheet.write(x, 8, line['sub_dia'] if line['sub_dia'] else 0.0, numberdos)
			worksheet.write(x, 9, line['total_sub'] if line['total_sub'] else 0.0, numberdos)
			worksheet.write(x, 10, line['recuperado'] if line['recuperado'] else 0.0, numberdos)
			worksheet.write(x, 11, line['pendiente'] if line['pendiente'] else 0.0, numberdos)
			worksheet.write(x, 12, line['tramite'] if line['tramite'] else '', formatCenter)

			totals[0] += line['sub_dia']
			totals[1] += line['total_sub']
			totals[2] += line['recuperado']
			totals[3] += line['pendiente']

			x += 1

		# x += 1

		worksheet.write(x, limiter-1, 'Total ', formats['especial2'])
		for total in totals:
			worksheet.write(x, limiter, total, styleFooterSum)
			limiter += 1

		widths = [14, 30, 10, 14, 20, 13, 13, 10, 13, 13, 13, 13, 17]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(directory + 'Reporte_subsidios.xlsx', 'rb')
		return self.env['popup.it'].get_file('Reporte Subsidios.xlsx', base64.encodebytes(b''.join(f.readlines())))