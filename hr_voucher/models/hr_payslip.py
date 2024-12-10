# -*- coding:utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
from math import modf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,letter, inch, landscape
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from zipfile import ZipFile
import subprocess
import sys
import calendar
from datetime import *
_logger = logging.getLogger(__name__)

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	from PyPDF2 import PdfFileReader, PdfFileWriter
except:
	install('PyPDF2')

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	date_send = fields.Datetime(string='Fecha Envio Boletas')
	date_confirmation = fields.Datetime(string='Fecha Rpta Confirmacion')
	is_verified = fields.Boolean(string="Rpta de Correo", help="Comprueba si el correo se ha recibido o no")

	def send_vouchers_by_email(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'Boleta.pdf'
		issues = []
		url = self.env['ir.config_parameter'].sudo().search([('key','=','web.base.url')],limit=1).value
		# email_from = self.env.user.email or self.env.user.company_id.email or ''
		for payslip in self:
			if payslip.state in ('done','paid'):
				Employee = payslip.employee_id
				if MainParameter.type_boleta== '1':
					doc = SimpleDocTemplate(route, pagesize=letter,
						rightMargin=30,
						leftMargin=30,
						topMargin=30,
						bottomMargin=20,
						encrypt=Employee.identification_id)
					doc.build(payslip.generate_voucher())
				elif MainParameter.type_boleta == '2':
					objeto_canvas = canvas.Canvas(route, pagesize=A4, encrypt=Employee.identification_id)
					payslip.generate_voucher_v2(objeto_canvas)
					objeto_canvas.save()
				elif MainParameter.type_boleta== '3':
					doc = SimpleDocTemplate(route, pagesize=landscape(letter),
						rightMargin=5,
						leftMargin=5,
						topMargin=50,
						bottomMargin=5,
						encrypt=Employee.identification_id)
					doc.build(payslip.generate_voucher_v3())
				f = open(route, 'rb')

				# template_mail_id = self.env.ref('hr_voucher.email_template_boleta_pago', False)
				# attachment_ids = []
				# attach = {
				# 	'name': 'Boleta de Pago %s.pdf' % Employee.name,
				# 	'type': 'binary',
				# 	'datas': base64.encodebytes(b''.join(f.readlines())),
				# 	'store_fname': base64.encodebytes(b''.join(f.readlines())),
				# 	'mimetype': 'application/pdf',
				# 	'res_model': 'mail.compose.message',
				# }
				# attachment_id = self.env['ir.attachment'].sudo().create(attach)
				# attachment_ids.append(attachment_id.id)
				# try:
				# 	if payslip.employee_id.work_email:
				# 		template_mail_id.sudo().send_mail(payslip.id, email_values={'email_to': Employee.work_email, 'email_from': email_from,'attachment_ids': attachment_ids}, force_send=True)
				# 		# template_mail_id.sudo().send_mail(payslip.id, email_values={'email_to': Employee.work_email, 'email_from': email_from,'attachment_ids': attachment_ids}, email_layout_xmlid='mail.mail_notification_layout')
				# 		# payslip.message_post(body=body_html, attachment_ids=attachment_ids)
				# 		payslip.date_send = fields.Datetime.now()
				# except:
				# 	issues.append(Employee.name)

				try:
					if payslip.employee_id.work_email:
						self.env['mail.mail'].sudo().create({
							'subject': 'Boleta de Remuneraciones del Periodo %s' % (payslip.payslip_run_id.name),
							'body_html': """ 
									<div style="margin: 0px; padding: 0px;">
										<h2 style="margin:0px 0 10px 0;font-size: 1.325rem;line-height:1.2;font-weight: 600;text-align:center;color:rgb(112,141,204);text-transform:uppercase;">
											<b>
												<font class="text-primary">
													BOLETA DE REMUNERACIONES
													<br />
													{periodo}
												</font>
											</b>
										</h2>
										<hr align="left" size="1" width="100%" color="#e8e7e7" />
										<p>Estimado (a) : {name},</p>
										<br />
										<p>Por la presente les comunicamos que la empresa {company}, le ha emitido la siguiente Boleta:</p>
										<br />
										<table>
											<tbody>
												<tr>
													<td style="width:150px;"> Tipo de Comprobante </td>
													<td style="width:12px;"> : </td>
													<td> Boleta de Pago de Remuneraciones </td>
												</tr>
												<tr>
													<td> Número </td>
													<td> : </td>
													<td> {number} </td>
												</tr>
												<tr>
													<td> Empleado </td>
													<td> : </td>
													<td> {name} </td>
												</tr>
												<tr>
													<td> Fecha de envio</td>
													<td> : </td>
													<td> {date} </td>
												</tr>
												<tr>
													<td> Nota </td>
													<td> : </td>
													<td> <strong>Para abrir su boleta es necesario colocar su dni como clave y tambien confirme su recepcion</strong> </td>
												</tr>
											</tbody>
										</table>
										<div style='text-align: center; padding: 16px 0px 16px 0px;'>
											<a href='{url}/payslip_line/{payslip_id}' style='padding: 5px 10px; color: #FFFFFF; text-decoration: none; background-color: #875A7B; border: 1px solid #875A7B; border-radius: 3px'>
												Confirmar Recepcion
											</a>
										</div>
									</div>
									""".format(periodo=payslip.payslip_run_id.name,
											   number=payslip.number,
											   name=payslip.employee_id.name,
											   company=payslip.company_id.name,
											   dni=payslip.employee_id.identification_id,
											   date=fields.Datetime.now() - timedelta(hours=5),
											   url=url,
											   payslip_id=payslip.id
											   ),
							'email_to': Employee.work_email,
							'attachment_ids': [(0, 0, {'name': 'Boleta de Pago %s.pdf' % Employee.name,
													   'datas': base64.encodebytes(b''.join(f.readlines()))}
												)]
						}).send()
						payslip.date_send = fields.Datetime.now()
					f.close()
				except:
					issues.append(Employee.name)
			else:
				return self.env['popup.it'].get_message('Primero debe de cerrar su planilla.')
		if issues:
			return self.env['popup.it'].get_message('No se pudieron enviar las Boletas de los siguientes Empleados: \n %s' % '\n'.join(issues))
		else:
			return self.env['popup.it'].get_message('Se enviaron todas las Boletas satisfactoriamente.')

	def get_vouchers_zip(self, payslips=None):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		elements = []
		afiles=[]
		if MainParameter.type_boleta== '1':
			if payslips:
				for payslip in payslips:
					doc = SimpleDocTemplate(MainParameter.dir_create_file + 'Boleta_'+payslip.employee_id.name+'.pdf', pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)
					afiles.append(MainParameter.dir_create_file + 'Boleta_'+payslip.employee_id.name+'.pdf')
					doc.build(payslip.generate_voucher())
				with ZipFile(MainParameter.dir_create_file +'boletas.zip','w') as zip:
					for file in afiles:
						zip.write(file)
				f = open(MainParameter.dir_create_file + 'boletas.zip', 'rb')
				return self.env['popup.it'].get_file('Boletas.zip',base64.encodebytes(b''.join(f.readlines())))
		elif MainParameter.type_boleta== '2':
			if payslips:
				for payslip in payslips:
					name_file = 'Boleta_'+payslip.employee_id.name+'.pdf'
					objeto_canvas  = canvas.Canvas(MainParameter.dir_create_file + name_file, pagesize=A4)
					payslip.generate_voucher_v2(objeto_canvas)
					afiles.append(MainParameter.dir_create_file + 'Boleta_'+payslip.employee_id.name+'.pdf')
					objeto_canvas.save()
				with ZipFile(MainParameter.dir_create_file +'boletas.zip','w') as zip:
					for file in afiles:
						zip.write(file)
				f = open(MainParameter.dir_create_file + 'boletas.zip', 'rb')
				return self.env['popup.it'].get_file('Boletas.zip',base64.encodebytes(b''.join(f.readlines())))
		elif MainParameter.type_boleta== '3':
			if payslips:
				for payslip in payslips:
					doc = SimpleDocTemplate(MainParameter.dir_create_file + 'Boleta_'+payslip.employee_id.name+'.pdf', pagesize=landscape(letter),
											rightMargin=5, leftMargin=5, topMargin=50, bottomMargin=5)
					afiles.append(MainParameter.dir_create_file + 'Boleta_'+payslip.employee_id.name+'.pdf')
					doc.build(payslip.generate_voucher_v3())
					# print("doc",doc)
				with ZipFile(MainParameter.dir_create_file +'boletas.zip','w') as zip:
					for file in afiles:
						zip.write(file)
				f = open(MainParameter.dir_create_file + 'boletas.zip', 'rb')
				return self.env['popup.it'].get_file('Boletas.zip',base64.encodebytes(b''.join(f.readlines())))


	def get_vouchers(self, payslips=None):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if MainParameter.type_boleta== '1':
			doc = SimpleDocTemplate(MainParameter.dir_create_file + 'Boleta.pdf', pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)
			elements = []
			if payslips:
				for payslip in payslips:
					elements += payslip.generate_voucher()
			else:
				elements += self.generate_voucher()
			doc.build(elements)
			f = open(MainParameter.dir_create_file + 'Boleta.pdf', 'rb')
		elif MainParameter.type_boleta == '2':
			name_file = "Boleta.pdf"
			objeto_canvas  = canvas.Canvas(MainParameter.dir_create_file + name_file, pagesize=A4)
			if payslips:
				for payslip in payslips:
					payslip.generate_voucher_v2(objeto_canvas)
			else:
				self.generate_voucher_v2(objeto_canvas)
			objeto_canvas.save()
			f = open(MainParameter.dir_create_file + name_file, 'rb')
		elif MainParameter.type_boleta== '3':
			doc = SimpleDocTemplate(MainParameter.dir_create_file + 'Boleta.pdf', pagesize=landscape(letter), rightMargin=5, leftMargin=5, topMargin=50,
                    bottomMargin=5)
			elements = []
			if payslips:
				for payslip in payslips:
					elements += payslip.generate_voucher_v3()
			else:
				elements += self.generate_voucher_v3()
			doc.build(elements)
			f = open(MainParameter.dir_create_file + 'Boleta.pdf', 'rb')
		return self.env['popup.it'].get_file('Boleta.pdf',base64.encodebytes(b''.join(f.readlines())))

	def generate_voucher(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_voucher_values()
		ReportBase = self.env['report.base']
		Employee = self.employee_id
		Contract = self.contract_id
		admission_date = self.env['hr.contract'].get_first_contract(Employee, Contract).date_start

		#### WORKED DAYS ####
		DNLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code'))
		DSUB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dsub.mapped('code'))
		EXT = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_ext.mapped('code'))
		DVAC = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dvac.mapped('code'))
		DOM = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('DOM'))
		DLAB = self.get_dlabs()
		# print("DLAB",DLAB)
		DLAB_DEC_INT = modf(DLAB * Contract.resource_calendar_id.hours_per_day)
		EXT_DEC_INT = modf(sum(EXT.mapped('number_of_hours')))
		DLAB = DLAB + sum(DOM.mapped('number_of_days'))

		DIAS_FAL = sum(DNLAB.mapped('number_of_days'))
		DIA_VAC = sum(DVAC.mapped('number_of_days'))
		DIA_SUB = sum(DSUB.mapped('number_of_days'))
		DIAS_NLAB = DIAS_FAL + DIA_VAC + DIA_SUB

		# if DIA_SUB==self.date_to.day:
		# 	DIA_SUB = self.date_to.day
		# 	DLAB = 0
		# 	DIAS_NLAB = DIA_VAC + DIA_SUB
		# elif DIA_VAC==self.date_to.day:
		# 	DIA_VAC = self.date_to.day
		# 	DLAB = 0
		# 	DIAS_NLAB = DIA_VAC + DIA_SUB
		# elif (DIA_SUB+DIA_VAC)==self.date_to.day:
		# 	DIAS_NLAB = self.date_to.day
		# 	DLAB = 0

		#### SALARY RULE CATEGORIES ####
		INCOME = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.income_categories.ids and sr.total > 0)
		DISCOUNTS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.discounts_categories.ids and sr.total > 0)
		CONTRIBUTIONS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_categories.ids and sr.total > 0)
		CONTRIBUTIONS_EMP = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_emp_categories.ids)
		NET_TO_PAY = self.line_ids.filtered(lambda sr: sr.salary_rule_id == MainParameter.net_to_pay_sr_id)
		SRC = {'Ingresos': INCOME, 'Descuentos': DISCOUNTS, 'Aportes Trabajador': CONTRIBUTIONS}

		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9, fontName="times-roman")
		internal_width = [2.5 * cm]
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		bg_color = colors.HexColor("#c5d9f1")
		spacer = Spacer(10, 20)

		I = ReportBase.create_image(self.company_id.logo, MainParameter.dir_create_file + 'logo.jpg', 150.0, 45.0)
		data = [[I if I else '']]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(spacer)

		data = [
				[Paragraph('RUC: %s' % self.company_id.vat or '', style_cell),
				 Paragraph('Empleador: %s' % self.company_id.name or '', style_cell),
				 Paragraph('Periodo: %s - %s' % (datetime.strftime((self.date_from),'%d-%m-%Y') or '', datetime.strftime((self.date_to),'%d-%m-%Y') or ''), style_cell)],
			]
		t = Table(data, [6 * cm, 8 * cm, 6 * cm], [1 * cm])
		t.setStyle(TableStyle([
				('BACKGROUND', (0, 0), (-1, -1), bg_color),
				('ALIGN', (0, 0), (-1, -1), 'CENTER'),
				('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
				('BOX', (0, 0), (-1, -1), 0.25, colors.black)
							]))
		elements.append(t)
		elements.append(spacer)

		if Contract.situation_id.name == 'BAJA':
			if self.date_from <= Contract.date_end <= self.date_to:
				situacion='BAJA'
			else:
				situacion='ACTIVO O SUBSIDIADO'
		else:
			situacion='ACTIVO O SUBSIDIADO'
		first_row = [
				[Paragraph('Documento de Identidad', style_cell), '',
				 Paragraph('Nombres y Apellidos', style_cell), '', '', '',
				 Paragraph(U'Situación', style_cell), ''],
				[Paragraph('Tipo', style_cell),
				 Paragraph(u'Número', style_cell), '', '', '', '', '', ''],
				[Paragraph(Employee.type_document_id.name or '', style_cell),
				 Paragraph(Employee.identification_id or '', style_cell),
				 Paragraph(Employee.name or '', style_cell), '', '', '',
				 Paragraph(situacion or '', style_cell), '']
			]
		first_row_format = [
				('SPAN', (0, 0), (1, 0)),
				('SPAN', (2, 0), (5, 1)),
				('SPAN', (6, 0), (7, 1)),
				('SPAN', (2, 2), (5, 2)),
				('SPAN', (6, 2), (7, 2)),
				('BACKGROUND', (0, 0), (-1, 1), bg_color)
			]
		second_row = [
				[Paragraph('Fecha de Ingreso', style_cell), '',
				 Paragraph('Tipo Trabajador', style_cell), '',
				 Paragraph('Regimen Pensionario', style_cell), '',
				 Paragraph('CUSPP', style_cell), ''],
				[Paragraph(str(datetime.strftime((admission_date),'%d-%m-%Y')) or '', style_cell), '',
				 Paragraph(Contract.worker_type_id.name or '', style_cell), '',
				 Paragraph(self.membership_id.name if self.membership_id.name else Contract.membership_id.name, style_cell), '',
				 Paragraph(Contract.cuspp or '', style_cell), '']
			]
		second_row_format =	[
				('SPAN', (0, 3), (1, 3)),
				('SPAN', (2, 3), (3, 3)),
				('SPAN', (4, 3), (5, 3)),
				('SPAN', (6, 3), (7, 3)),
				('SPAN', (0, 4), (1, 4)),
				('SPAN', (2, 4), (3, 4)),
				('SPAN', (4, 4), (5, 4)),
				('SPAN', (6, 4), (7, 4)),
				('BACKGROUND', (0, 3), (-1, 3), bg_color)
			]
		third_row = [
				[Paragraph(u'Días Laborados', style_cell),
				 Paragraph(u'Días no Laborados', style_cell),
				 Paragraph(u'Días Subsidiados', style_cell),
				 Paragraph(u'Condición', style_cell),
				 Paragraph('Jornada Ordinaria', style_cell), '',
				 Paragraph('Sobretiempo', style_cell), ''],
				['', '', '', '',
				 Paragraph('Total Horas', style_cell),
				 Paragraph('Minutos', style_cell),
				 Paragraph('Total Horas', style_cell),
				 Paragraph('Minutos', style_cell)],
				[Paragraph('%d'% DLAB or '0', style_cell),
				 Paragraph('%d'% DIAS_NLAB or '0', style_cell),
				 Paragraph('%d'% DIA_SUB or '0', style_cell),
				 Paragraph(dict(Employee._fields['condition'].selection).get(Employee.condition) or '', style_cell),
				 Paragraph(str(ReportBase.custom_round(DLAB_DEC_INT[1])) or '0', style_cell),
				 Paragraph(str(ReportBase.custom_round(DLAB_DEC_INT[0] * 60)) or '0', style_cell),
				 Paragraph(str(ReportBase.custom_round(EXT_DEC_INT[1])), style_cell),
				 Paragraph(str(ReportBase.custom_round(EXT_DEC_INT[0] * 60)) or '0', style_cell)]
			]
		third_row_format = [
				('SPAN', (0, 5), (0, 6)),
				('SPAN', (1, 5), (1, 6)),
				('SPAN', (2, 5), (2, 6)),
				('SPAN', (3, 5), (3, 6)),
				('SPAN', (4, 5), (5, 5)),
				('SPAN', (6, 5), (7, 5)),
				('BACKGROUND', (0, 5), (-1, 6), bg_color)
			]
		fourth_row = [
				[Paragraph(u'Otros empleadores por Rentas de 5ta categoría', style_cell), '', '', '',
				 Paragraph('Si' if Contract.other_employers else 'No', style_cell), '', '', '']
			]
		fourth_row_format = [
				('SPAN', (0, 8), (3, 8)),
				('SPAN', (4, 8), (7, 8)),
				('BACKGROUND', (0, 8), (3, 8), bg_color)
			]
		fifth_row = [
				[Paragraph(u'Motivo de Suspensión de Labores', style_cell), '', '', '', '', '', '', ''],
				[Paragraph('Tipo', style_cell),
				 Paragraph('Motivo', style_cell), '', '', '', '', '',
				 Paragraph('Nro Días', style_cell)]
			]
		fifth_row_format = [
				('SPAN', (0, 9), (-1, 9)),
				('SPAN', (1, 10), (6, 10)),
				('BACKGROUND', (0, 9), (-1, 10), bg_color)
			]
		span_limit = 11
		y = 0
		memoria=[]
		for line in Contract.work_suspension_ids.filtered(lambda payslip: payslip.periodo_id.id == self.payslip_run_id.periodo_id.id):
			# print("line",line.suspension_type_id)
			if line.suspension_type_id.code in memoria:
				continue
			total_dias = self.env['hr.work.suspension'].search([('periodo_id', '=', self.payslip_run_id.periodo_id.id),('contract_id', '=',Contract.id),
																('suspension_type_id', '=',line.suspension_type_id.id)]).mapped('days')
			# print("total_dias",sum(total_dias))
			fifth_row += [
				[Paragraph(line.suspension_type_id.code or '', style_cell),
				 Paragraph(line.reason or '', style_cell), '', '', '', '', '',
				 Paragraph(str(sum(total_dias)) or '0', style_cell)]
			]
			fifth_row_format += [('SPAN', (1, span_limit), (6, span_limit))]
			span_limit += 1
			y += 1
			memoria.append(line.suspension_type_id.code)
			# print("memoria",memoria)
		global_format = [
				('ALIGN', (0, 0), (-1, -1), 'CENTER'),
				('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
				('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
				('BOX', (0, 0), (-1, -1), 0.25, colors.black)
			]
		t = Table(first_row + second_row + third_row + fourth_row + fifth_row, 8 * internal_width, (y + 11) * [0.5 * cm])
		t.setStyle(TableStyle(first_row_format + second_row_format + third_row_format + fourth_row_format + fifth_row_format + global_format))
		elements.append(t)
		elements.append(spacer)

		data = [[
				Paragraph(u'Código', style_cell),
				Paragraph('Conceptos', style_cell),
				Paragraph('Ingresos S/.', style_cell),
				Paragraph('Descuentos S/.', style_cell),
				Paragraph('Neto S/.', style_cell)
			]]
		y = 0
		data_format = [('BACKGROUND', (0, 0), (-1, 0), bg_color)]
		for i in SRC:
			data += [[Paragraph(i, style_left), '', '', '', '']]
			y += 1
			data_format += [('SPAN', (0, y), (-1, y)),
							('BACKGROUND', (0, y), (-1, y), bg_color)]
			for line in SRC[i]:
				data += [[
						Paragraph(line.salary_rule_id.sunat_code or '', style_left),
						Paragraph(line.name or '', style_left),
						Paragraph('{:,.2f}'.format(line.total) or '0.00' if line.category_id.type == 'in' else '', style_right),
						Paragraph('{:,.2f}'.format(line.total) or '0.00' if line.category_id.type == 'out' else '', style_right), ''
					]]
				y += 1
		y += 1
		data += [[Paragraph(NET_TO_PAY.salary_rule_id.name or '', style_left), '', '', '', Paragraph('{:,.2f}'.format(NET_TO_PAY.total) or '0.00', style_right)]]
		data_format += [
			('SPAN', (0, y), (3, y)),
			('BACKGROUND', (0, y), (-1, y), bg_color),
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (0, 0), (-1, 0), 0.25, colors.black),
			('BOX', (0, 0), (-1, 0), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]
		t = Table(data, [3 * cm, 8 * cm, 3 * cm, 3 * cm, 3 * cm], (y + 1) * [0.5 * cm])
		t.setStyle(TableStyle(data_format))
		elements.append(t)
		elements.append(spacer)

		data = [[Paragraph('Aportes Empleador', style_left), '', '']]
		data_format = [('SPAN', (0, 0), (-1, 0)),
					   ('BACKGROUND', (0, 0), (-1, 0), bg_color),
					   ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
					   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
					   ('BOX', (0, 0), (-1, 0), 0.25, colors.black),
					   ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]
		y = 1
		for sr in CONTRIBUTIONS_EMP:
			# print("sr.total",sr.total)
			if sr.total != 0:
				data += [[Paragraph(sr.salary_rule_id.sunat_code or '', style_left),
						  Paragraph(sr.name or '', style_left),
						  Paragraph('{:,.2f}'.format(sr.total) or '0.00', style_right)]]
				y += 1

		t = Table(data, [3 * cm, 14 * cm, 3 * cm], y * [0.5 * cm])
		t.setStyle(TableStyle(data_format))
		elements.append(t)
		elements.append(spacer)
		elements.append(spacer)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 130.0, 60.0)
		data = [
			['', I if I else ''],
			[Paragraph('<strong>___________________________________<br/>%s<br/>%s N° %s<br/>Trabajador(a)</strong>' % (
											Employee.name or '', Employee.type_document_id.name or '', Employee.identification_id or ''),
					   style_center),
			 Paragraph('<strong>___________________________________<br/>%s<br/>%s N° %s<br/>Empleador</strong>' % (
											 MainParameter.reprentante_legal_id.name or '',
											 MainParameter.reprentante_legal_id.l10n_latam_identification_type_id.name or '',
											 MainParameter.reprentante_legal_id.vat or ''), style_center)],
		]
		t = Table(data, [10 * cm, 10 * cm], len(data) * [1.1 * cm])
		t.setStyle(TableStyle(simple_style))
		elements.append(t)
		elements.append(PageBreak())
		return elements

	def _get_sql_wd(self,code_unico):
		struct_id = self.struct_id.id
		sql = """
	select T.employee_id,
       		T.identification_id,
       		T.name,
        	T.contract_id,
        	T.code,
        	sum(T.wd_total_dias) as wd_total_dias,
        	sum(T.wd_total_horas) as wd_total_horas
		from (SELECT	
			he.id as employee_id,
			he.identification_id,
			he.name,
			hc.id as contract_id,
			case when hwet.code in ('DLAB','DOM','DLABN') then 'BAS' 
				 when hwet.code in ('DVAC') then 'VAC'
				 else hwet.code end as code,
			hwet.id as wd_type_id,
			sum(coalesce(hpwd.number_of_days,0)) as wd_total_dias,
			sum(coalesce(hpwd.number_of_hours,0)) as wd_total_horas
			from hr_payslip hp 
			inner join hr_employee he on he.id = hp.employee_id 
			inner join hr_contract hc on hc.id = hp.contract_id
			left join hr_payslip_worked_days hpwd on hpwd.payslip_id=hp.id
			left join hr_work_entry_type hwet on hwet.id=hpwd.work_entry_type_id
			where hp.id = {slip}
			and hp.company_id = {company}
			and hp.struct_id = {struct_id}
			and(hpwd.number_of_days <> 0 or hpwd.number_of_hours <> 0)
			group by he.id,he.identification_id,hc.id,hwet.code,hwet.id
			order by he.identification_id)T
		where T.code = '{code}'
		group by T.employee_id,
               	T.identification_id,
               	T.name,
                T.contract_id,
                T.code
			""" .format(
				slip = self.id,
				company = self.company_id.id,
				struct_id = struct_id,
				code = code_unico
			)
		return sql

	def generate_voucher_v2(self,objeto_canvas):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_voucher_values()
		ReportBase = self.env['report.base']
		Employee = self.employee_id
		Contract = self.contract_id
		admission_date = self.env['hr.contract'].get_first_contract(Employee, Contract).date_start

		#### WORKED DAYS ####
		DNLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code'))
		DSUB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dsub.mapped('code'))
		EXT = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_ext.mapped('code'))
		DVAC = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dvac.mapped('code'))
		DOM = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('DOM'))
		DLAB = self.get_dlabs()
		# print("DLAB",DLAB)
		DLAB_DEC_INT = modf(DLAB * Contract.resource_calendar_id.hours_per_day)
		EXT_DEC_INT = modf(sum(EXT.mapped('number_of_hours')))
		DLAB = DLAB + sum(DOM.mapped('number_of_days'))

		DIAS_FAL = sum(DNLAB.mapped('number_of_days'))
		DIA_VAC = sum(DVAC.mapped('number_of_days'))
		DIA_SUB = sum(DSUB.mapped('number_of_days'))
		DIAS_NLAB = DIAS_FAL + DIA_VAC + DIA_SUB

		# if DIA_SUB == 30:
		# 	DIA_SUB = self.date_to.day
		# 	DLAB = 0
		# 	DIAS_NLAB = DIA_VAC + DIA_SUB
		# elif DIA_VAC == 30:
		# 	DIA_VAC = self.date_to.day
		# 	DLAB = 0
		# 	DIAS_NLAB = DIA_VAC + DIA_SUB
		# elif (DIA_SUB + DIA_VAC) == 30:
		# 	DIAS_NLAB = self.date_to.day
		# 	DLAB = 0

		#### SALARY RULE CATEGORIES ####
		INCOME = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.income_categories.ids and sr.total > 0)
		DISCOUNTS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.discounts_categories.ids and sr.total > 0)
		CONTRIBUTIONS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_categories.ids and sr.total > 0)
		CONTRIBUTIONS_EMP = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_emp_categories.ids and sr.total > 0)
		NET_TO_PAY = self.line_ids.filtered(lambda sr: sr.salary_rule_id == MainParameter.net_to_pay_sr_id)

		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=8, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		internal_width = [2.5 * cm]
		bg_color = colors.HexColor("#c5d9f1")
		spacer = Spacer(10, 20)

		width ,height  = A4  # 595 , 842
		wReal = width- 15
		hReal = height - 40
		pagina = 1
		size_widths = [110,50]

		if Contract.situation_id.name == 'BAJA':
			if self.date_from <= Contract.date_end <= self.date_to:
				date_end = Contract.date_end
			else:
				date_end = False
		else:
			date_end = False

		# PRIMERA COPIA BOLETA DE PAGO
		I = ReportBase.create_image(self.company_id.logo, MainParameter.dir_create_file + 'logo.jpg', 110.0, 45.0)
		data = [
			[Paragraph('<strong>%s</strong>' % self.company_id.name or '', style_left),I if I else ''],
			[Paragraph('%s' % self.company_id.street or '', style_left),''],
			[Paragraph('RUC N° %s' % self.company_id.vat or '', style_left),''],
		]
		t = Table(data, [16 * cm, 4 * cm],len(data) * [0.4 * cm])
		t.setStyle(TableStyle([
			('SPAN', (1, 0), (1, -1)),
			# ('SPAN', (2, 2), (-1, -1)),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			# ('BACKGROUND', (2, 1), (2, 1), colors.HexColor("#B0B0B0")),
			# ('BOX', (2, 0), (-1, -1), 0.25, colors.black)
		]))
		t.wrapOn(objeto_canvas,20,500)
		t.drawOn(objeto_canvas,20,hReal-15)

		objeto_canvas.setFont("Helvetica-Bold", 11)
		objeto_canvas.setFillColor(colors.black)
		objeto_canvas.drawCentredString((wReal/2)+20,hReal-30, "BOLETA DE REMUNERACIONES")
		objeto_canvas.setFont("Helvetica-Bold", 10)
		objeto_canvas.drawCentredString((wReal/2)+20,hReal-42, "PLANILLA %s" % self.payslip_run_id.name or '')

		objeto_canvas.setFont("Helvetica", 10)
		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1

		data = [
			[Paragraph('<strong>__________________________________________________________________________________________________________________</strong>', style_left)]
		]
		t = Table(data, [20 * cm],len(data) * [0.12 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 20, 500)
		t.drawOn(objeto_canvas, 20, hReal - 45)

		dias_vaca = 0
		fecha_ing_vac = fecha_fin_vac = ''
		if len(self.accrual_vacation_ids) > 0:
			estado_vaca = 'SI'
			for vacaciones in self.accrual_vacation_ids:
				dias_vaca += vacaciones.days
				fecha_ing_vac = vacaciones.request_date_from
				fecha_fin_vac = vacaciones.request_date_to
		else:
			estado_vaca = 'NO'

		data = [
				[Paragraph('<strong>Trabajador</strong>', style_left),Paragraph(': %s' % Employee.name.title() or '', style_left),
				 Paragraph('<strong>Fecha de Ingreso</strong>', style_left),Paragraph(': %s' % str(datetime.strftime((admission_date),'%d-%m-%Y')) or '', style_left),
				 Paragraph('<strong>Dias Lab</strong>', style_left),Paragraph(': %d' % DLAB or '', style_left)],
				[Paragraph('<strong>Tipo Trab</strong>', style_left),Paragraph(': %s' % Contract.worker_type_id.name.capitalize() if Contract.worker_type_id.name else '', style_left),
				 Paragraph('<strong>Fecha de Cese</strong>', style_left),Paragraph(': %s' % datetime.strftime(date_end,'%d-%m-%Y') if date_end else '', style_left),
				 Paragraph('<strong>Dias Subs</strong>', style_left),Paragraph(': %d'% DIA_SUB or '0', style_left)],
				[Paragraph('<strong>Area</strong>', style_left),Paragraph(': %s' % Contract.department_id.name.capitalize() if Contract.department_id.name else '', style_left),
				 Paragraph('<strong>Periodo Vacac</strong>', style_left),Paragraph(': %s' % estado_vaca or '', style_left),
				 Paragraph('<strong>Dias No Lab</strong>', style_left),Paragraph(': %d'% DIAS_NLAB or '0', style_left)],
				[Paragraph('<strong>Cargo</strong>', style_left),Paragraph(': %s' % Contract.job_id.name.capitalize() if Contract.job_id.name else '', style_left),
				 Paragraph('<strong>&nbsp; &nbsp;&nbsp; &nbsp; Inicio Vac</strong>', style_left),Paragraph(': %s' % datetime.strftime((fecha_ing_vac),'%d-%m-%Y') if fecha_ing_vac != '' else '', style_left),
				 Paragraph('<strong>Dias Vac</strong>', style_left),Paragraph(': %d' % dias_vaca or '0', style_left)],
				[Paragraph('<strong>Centro de Costos</strong>', style_left),Paragraph(': %s' % self.distribution_id.description.capitalize() if self.distribution_id.description else self.distribution_id.name, style_left),
				 Paragraph('<strong>&nbsp; &nbsp;&nbsp; &nbsp; Fin Vac</strong>', style_left),Paragraph(': %s' % datetime.strftime((fecha_fin_vac),'%d-%m-%Y') if fecha_fin_vac != '' else '', style_left),
				 Paragraph('<strong>N° Horas Ord</strong>', style_left),Paragraph(': %s' %str(ReportBase.custom_round(DLAB_DEC_INT[1])) or '0', style_left)],
				[Paragraph('<strong>Tipo de Docum</strong>', style_left),Paragraph(': %s <strong>Nro.</strong> %s' % (Employee.type_document_id.name or '',Employee.identification_id or ''), style_left),
				 Paragraph('<strong>Reg Pensionario</strong>', style_left),Paragraph(': %s' % self.membership_id.name.title() if self.membership_id.name else Contract.membership_id.name, style_left),
				 Paragraph('<strong>N° Horas Ext</strong>', style_left),Paragraph(': %s' %str(ReportBase.custom_round(EXT_DEC_INT[1])) or '', style_left)],
				[Paragraph('<strong>Regimen Laboral</strong>', style_left),Paragraph(': %s' % dict(self._fields['labor_regime'].selection).get(self.labor_regime) or '', style_left),
				 Paragraph('<strong>C.U.S.P.P.</strong>', style_left),Paragraph(': %s' % Contract.cuspp if Contract.cuspp else '', style_left),
				 Paragraph('<strong>Rem Basica</strong>', style_left),Paragraph(': {:,.2f}'.format(self.wage) or '0.00', style_left)],

		]
		t = Table(data, [3 * cm, 6 * cm , 3 * cm, 3 * cm, 3 * cm, 2 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas,20,500)
		t.drawOn(objeto_canvas,20,hReal-135)

		data = [[
				Paragraph('<strong>Dia/Hrs</strong>', style_cell),
				Paragraph('<strong>INGRESOS</strong>', style_cell),
				Paragraph('<strong>DESCUENTOS</strong>', style_cell),
				Paragraph('<strong>APORTES EMPLEADOR</strong>', style_cell)
			]]
		t = Table(data, [1.6 * cm,6.5 * cm,6.5 * cm, 5.4 * cm], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]))
		t.wrapOn(objeto_canvas,18,500)
		t.drawOn(objeto_canvas,18,hReal-160)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				return pagina+1,hReal-142
			else:
				return pagina,posactual-valor

		dias_in = h_ing = h_des = h_apor = hReal - 170
		total_ing = total_des = total_apor = 0
		size_widths = [110, 50]

		for dia in INCOME:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 20

			self.env.cr.execute(self._get_sql_wd(dia.code))
			res_wds = self.env.cr.dictfetchall()
			# print("res_wds",res_wds)
			if len(res_wds) > 0:
				if dia.code == res_wds[0]['code']:
					objeto_canvas.drawRightString(first_pos + 30, dias_in, '%d' % int(res_wds[0]['wd_total_dias']) if res_wds[0]['wd_total_dias'] > 0
					else f"{int(res_wds[0]['wd_total_horas']):02d}:{(int((res_wds[0]['wd_total_horas'] - int(res_wds[0]['wd_total_horas'])) * 60)):02d}")
			first_pos += size_widths[1]
			pagina, dias_in = verify_linea(self, objeto_canvas, wReal, hReal, dias_in, 12, pagina, size_widths)

		for ingreso in INCOME:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 65
			objeto_canvas.drawString(first_pos, h_ing, particionar_text(ingreso.name if ingreso.name else '', 110))
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos + 67, h_ing,'{:,.2f}'.format(ingreso.total) if ingreso.total else '0.00')
			first_pos += size_widths[1]
			total_ing += ingreso.total
			pagina, h_ing = verify_linea(self, objeto_canvas, wReal, hReal, h_ing, 12, pagina, size_widths)

		for descuento in CONTRIBUTIONS:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 250
			objeto_canvas.drawString(first_pos, h_des, particionar_text(descuento.name if descuento.name else '', 110))
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos + 67, h_des,'{:,.2f}'.format(descuento.total) if descuento.total else '0.00')
			first_pos += size_widths[1]
			total_des += descuento.total
			pagina, h_des = verify_linea(self, objeto_canvas, wReal, hReal, h_des, 12, pagina, size_widths)

		for descuento in DISCOUNTS:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 250
			objeto_canvas.drawString(first_pos, h_des, particionar_text(descuento.name if descuento.name else '', 110))
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos + 67, h_des,'{:,.2f}'.format(descuento.total) if descuento.total else '0.00')
			first_pos += size_widths[1]
			total_des += descuento.total
			pagina, h_des = verify_linea(self, objeto_canvas, wReal, hReal, h_des, 12, pagina, size_widths)

		for aporte in CONTRIBUTIONS_EMP:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 434
			objeto_canvas.drawString(first_pos, h_apor, particionar_text(aporte.name if aporte.name else '', 110))
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos + 38, h_apor,'{:,.2f}'.format(aporte.total) if aporte.total else '0.00')
			first_pos += size_widths[1]
			total_apor += aporte.total
			pagina, h_apor = verify_linea(self, objeto_canvas, wReal, hReal, h_apor, 12, pagina, size_widths)

		data = [[
			Paragraph('TOTAL INGRESOS S/', style_title),Paragraph('<strong>{:,.2f}</strong>'.format(total_ing) or '0.00', style_right),
			Paragraph('TOTAL DESCUENTOS S/', style_title),Paragraph('<strong>{:,.2f}</strong>'.format(total_des) or '0.00', style_right),
			Paragraph('TOTAL APORTES S/', style_title),Paragraph('<strong>{:,.2f}</strong>'.format(total_apor) or '0.00', style_right)
		]]
		t = Table(data, [6.1 * cm,2 * cm, 4.6 * cm,2 * cm, 3.3 * cm,2 * cm,], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			# ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (1, -1), 0.25, colors.black),
			('BOX', (2, 0), (3, -1), 0.25, colors.black),
			('BOX', (4, 0), (5, -1), 0.25, colors.black),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 290)

		data = [['',
			Paragraph('<strong>NETO A PAGAR S/</strong>', style_cell),Paragraph('<strong>{:,.2f}</strong>'.format(NET_TO_PAY.total) or '0.00', style_cell),''
		]]
		t = Table(data, [7 * cm,4 * cm, 3 * cm,6 * cm], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (1, 0), (2, -1), 0.25, colors.black),
			('BOX', (1, 0), (2, -1), 0.25, colors.black),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 315)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 130.0, 60.0)
		data = [
				[I if I else '', '', ''],
				[Paragraph('<strong>__________________________</strong>', style_title), '',
				 Paragraph('<strong>__________________________</strong>', style_title)],
				[Paragraph('<strong>EMPLEADOR</strong>', style_title),'',
				 Paragraph('<strong>RECIBI CONFORME <br/> TRABAJADOR</strong>', style_title)]
			]
		t = Table(data, [9 * cm, 2 * cm, 9 * cm], 3 * [0.6 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 380)




		# SEGUNDA COPIA BOLETA DE PAGO
		I = ReportBase.create_image(self.company_id.logo, MainParameter.dir_create_file + 'logo.jpg', 110.0, 45.0)
		data = [
			[Paragraph('<strong>%s</strong>' % self.company_id.name or '', style_left),I if I else ''],
			[Paragraph('%s' % self.company_id.street or '', style_left),''],
			[Paragraph('RUC N° %s' % self.company_id.vat or '', style_left),''],
		]
		t = Table(data, [16 * cm, 4 * cm],len(data) * [0.4 * cm])
		t.setStyle(TableStyle([
			('SPAN', (1, 0), (1, -1)),
			# ('SPAN', (2, 2), (-1, -1)),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			# ('BACKGROUND', (2, 1), (2, 1), colors.HexColor("#B0B0B0")),
			# ('BOX', (2, 0), (-1, -1), 0.25, colors.black)
		]))
		t.wrapOn(objeto_canvas,20,500)
		t.drawOn(objeto_canvas,20,hReal-430)

		objeto_canvas.setFont("Helvetica-Bold", 11)
		objeto_canvas.setFillColor(colors.black)
		objeto_canvas.drawCentredString((wReal/2)+20,hReal-445, "BOLETA DE REMUNERACIONES")
		objeto_canvas.setFont("Helvetica-Bold", 10)
		objeto_canvas.drawCentredString((wReal/2)+20,hReal-457, "PLANILLA %s" % self.payslip_run_id.name or '')

		objeto_canvas.setFont("Helvetica", 10)
		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1

		data = [
			[Paragraph('<strong>__________________________________________________________________________________________________________________</strong>', style_left)]
		]
		t = Table(data, [20 * cm],len(data) * [0.12 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 20, 500)
		t.drawOn(objeto_canvas, 20, hReal - 460)

		data = [
				[Paragraph('<strong>Trabajador</strong>', style_left),Paragraph(': %s' % Employee.name.title() or '', style_left),
				 Paragraph('<strong>Fecha de Ingreso</strong>', style_left),Paragraph(': %s' % str(datetime.strftime((admission_date),'%d-%m-%Y')) or '', style_left),
				 Paragraph('<strong>Dias Lab</strong>', style_left),Paragraph(': %d' % DLAB or '', style_left)],
				[Paragraph('<strong>Tipo Trab</strong>', style_left),Paragraph(': %s' % Contract.worker_type_id.name.capitalize() if Contract.worker_type_id.name else '', style_left),
				 Paragraph('<strong>Fecha de Cese</strong>', style_left),Paragraph(': %s' % datetime.strftime(date_end,'%d-%m-%Y') if date_end else '', style_left),
				 Paragraph('<strong>Dias Subs</strong>', style_left),Paragraph(': %d'% DIA_SUB or '0', style_left)],
				[Paragraph('<strong>Area</strong>', style_left),Paragraph(': %s' % Contract.department_id.name.capitalize() if Contract.department_id.name else '', style_left),
				 Paragraph('<strong>Periodo Vacac</strong>', style_left),Paragraph(': %s' % estado_vaca or '', style_left),
				 Paragraph('<strong>Dias No Lab</strong>', style_left),Paragraph(': %d'% DIAS_NLAB or '0', style_left)],
				[Paragraph('<strong>Cargo</strong>', style_left),Paragraph(': %s' % Contract.job_id.name.capitalize() if Contract.job_id.name else '', style_left),
				 Paragraph('<strong>&nbsp; &nbsp;&nbsp; &nbsp; Inicio Vac</strong>', style_left),Paragraph(': %s' % datetime.strftime((fecha_ing_vac),'%d-%m-%Y') if fecha_ing_vac != '' else '', style_left),
				 Paragraph('<strong>Dias Vac</strong>', style_left),Paragraph(': %d' %dias_vaca or '0', style_left)],
				[Paragraph('<strong>Centro de Costos</strong>', style_left),Paragraph(': %s' % self.distribution_id.description.capitalize() if self.distribution_id.description else self.distribution_id.name, style_left),
				 Paragraph('<strong>&nbsp; &nbsp;&nbsp; &nbsp; Fin Vac</strong>', style_left),Paragraph(': %s' % datetime.strftime((fecha_fin_vac),'%d-%m-%Y') if fecha_fin_vac != '' else '', style_left),
				 Paragraph('<strong>N° Horas Ord</strong>', style_left),Paragraph(': %s' %str(ReportBase.custom_round(DLAB_DEC_INT[1])) or '0', style_left)],
				[Paragraph('<strong>Tipo de Docum</strong>', style_left),Paragraph(': %s <strong>Nro.</strong> %s' % (Employee.type_document_id.name or '',Employee.identification_id or ''), style_left),
				 Paragraph('<strong>Reg Pensionario</strong>', style_left),Paragraph(': %s' % self.membership_id.name.title() if self.membership_id.name else Contract.membership_id.name, style_left),
				 Paragraph('<strong>N° Horas Ext</strong>', style_left),Paragraph(': %s' %str(ReportBase.custom_round(EXT_DEC_INT[1])) or '', style_left)],
				[Paragraph('<strong>Regimen Laboral</strong>', style_left),Paragraph(': %s' % dict(self._fields['labor_regime'].selection).get(self.labor_regime) or '', style_left),
				 Paragraph('<strong>C.U.S.P.P.</strong>', style_left),Paragraph(': %s' % Contract.cuspp if Contract.cuspp else '', style_left),
				 Paragraph('<strong>Rem Basica</strong>', style_left),Paragraph(': {:,.2f}'.format(self.wage) or '0.00', style_left)],

		]
		t = Table(data, [3 * cm, 6 * cm , 3 * cm, 3 * cm, 3 * cm, 2 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas,20,500)
		t.drawOn(objeto_canvas,20,hReal-550)

		data = [[
				Paragraph('<strong>Dia/Hrs</strong>', style_cell),
				Paragraph('<strong>INGRESOS</strong>', style_cell),
				Paragraph('<strong>DESCUENTOS</strong>', style_cell),
				Paragraph('<strong>APORTES EMPLEADOR</strong>', style_cell)
			]]
		t = Table(data, [1.6 * cm,6.5 * cm,6.5 * cm, 5.4 * cm], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]))
		t.wrapOn(objeto_canvas,18,500)
		t.drawOn(objeto_canvas,18,hReal-575)

		dias_in = h_ing = h_des = h_apor = hReal-585
		total_ing = total_des = total_apor = 0
		size_widths = [110,50]

		for dia in INCOME:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 20

			self.env.cr.execute(self._get_sql_wd(dia.code))
			res_wds = self.env.cr.dictfetchall()
			# print("res_wds",res_wds)
			if len(res_wds) > 0:
				if dia.code == res_wds[0]['code']:
					objeto_canvas.drawRightString(first_pos + 30, dias_in, '%d' % int(res_wds[0]['wd_total_dias']) if res_wds[0]['wd_total_dias'] > 0
					else f"{int(res_wds[0]['wd_total_horas']):02d}:{(int((res_wds[0]['wd_total_horas'] - int(res_wds[0]['wd_total_horas'])) * 60)):02d}")
			first_pos += size_widths[1]
			pagina, dias_in = verify_linea(self, objeto_canvas, wReal, hReal, dias_in, 12, pagina, size_widths)

		for ingreso in INCOME:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 65
			objeto_canvas.drawString(first_pos,h_ing,particionar_text(ingreso.name if ingreso.name else '',110) )
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos+67 ,h_ing,'{:,.2f}'.format(ingreso.total) if ingreso.total else '0.00')
			first_pos += size_widths[1]
			total_ing += ingreso.total
			pagina, h_ing = verify_linea(self,objeto_canvas,wReal,hReal,h_ing,12,pagina,size_widths)

		for descuento in CONTRIBUTIONS:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 250
			objeto_canvas.drawString(first_pos,h_des,particionar_text(descuento.name if descuento.name else '',110) )
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos+67 ,h_des,'{:,.2f}'.format(descuento.total) if descuento.total else '0.00')
			first_pos += size_widths[1]
			total_des += descuento.total
			pagina, h_des = verify_linea(self,objeto_canvas,wReal,hReal,h_des,12,pagina,size_widths)

		for descuento in DISCOUNTS:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 250
			objeto_canvas.drawString(first_pos,h_des,particionar_text(descuento.name if descuento.name else '',110) )
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos+67 ,h_des,'{:,.2f}'.format(descuento.total) if descuento.total else '0.00')
			first_pos += size_widths[1]
			total_des += descuento.total
			pagina, h_des = verify_linea(self,objeto_canvas,wReal,hReal,h_des,12,pagina,size_widths)

		for aporte in CONTRIBUTIONS_EMP:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 434
			objeto_canvas.drawString(first_pos,h_apor,particionar_text(aporte.name if aporte.name else '',110) )
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos+38 ,h_apor,'{:,.2f}'.format(aporte.total) if aporte.total else '0.00')
			first_pos += size_widths[1]
			total_apor += aporte.total
			pagina, h_apor = verify_linea(self,objeto_canvas,wReal,hReal,h_apor,12,pagina,size_widths)

		data = [[
			Paragraph('TOTAL INGRESOS S/', style_title),Paragraph('<strong>{:,.2f}</strong>'.format(total_ing) or '0.00', style_right),
			Paragraph('TOTAL DESCUENTOS S/', style_title),Paragraph('<strong>{:,.2f}</strong>'.format(total_des) or '0.00', style_right),
			Paragraph('TOTAL APORTES S/', style_title),Paragraph('<strong>{:,.2f}</strong>'.format(total_apor) or '0.00', style_right)
		]]
		t = Table(data, [6.1 * cm,2 * cm, 4.6 * cm,2 * cm, 3.3 * cm,2 * cm,], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			# ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (1, -1), 0.25, colors.black),
			('BOX', (2, 0), (3, -1), 0.25, colors.black),
			('BOX', (4, 0), (5, -1), 0.25, colors.black),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 705)

		data = [['',
			Paragraph('<strong>NETO A PAGAR S/</strong>', style_cell),Paragraph('<strong>{:,.2f}</strong>'.format(NET_TO_PAY.total) or '0.00', style_cell),''
		]]
		t = Table(data, [7 * cm,4 * cm, 3 * cm,6 * cm], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (1, 0), (2, -1), 0.25, colors.black),
			('BOX', (1, 0), (2, -1), 0.25, colors.black),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 730)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 130.0, 60.0)
		data = [
				[I if I else '', '', ''],
				[Paragraph('<strong>__________________________</strong>', style_title), '',
				 Paragraph('<strong>__________________________</strong>', style_title)],
				[Paragraph('<strong>EMPLEADOR</strong>', style_title),'',
				 Paragraph('<strong>RECIBI CONFORME <br/> TRABAJADOR</strong>', style_title)]
			]
		t = Table(data, [9 * cm, 2 * cm, 9 * cm], 3 * [0.6 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 790)

		objeto_canvas.showPage()

		return objeto_canvas

	def generate_voucher_v3(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_voucher_values()
		ReportBase = self.env['report.base']
		Employee = self.employee_id
		Contract = self.contract_id

		if not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		admission_date = self.env['hr.contract'].get_first_contract(Employee, Contract).date_start

		#### WORKED DAYS ####
		DLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('DLAB','DOM'))
		DVAC = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('DVAC'))
		DMED = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('DMED'))
		DSUB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dsub.mapped('code'))
		FAL = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('FAL'))
		LCGH = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('LCGH'))
		LSGH = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('LSGH'))

		HE25 = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('HE25'))
		HE35 = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('HE35'))
		HE100 = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('HE100'))
		HNOC = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('HNOC'))

		HDLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('DLAB'))
		HDLABN = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('DLABN'))
		TAR = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('TAR'))

		RETE_MES = self.input_line_ids.filtered(lambda wd: wd.code in ('RETE_MES'))
		ADEU_MES = self.input_line_ids.filtered(lambda wd: wd.code in ('ADEU_MES'))

		#Días Laborados
		DIAS_LABORADOS = int(sum(DLAB.mapped('number_of_days')))
		DIAS_VACACIONES = int(sum(DVAC.mapped('number_of_days')))
		DESCANSO_MEDICO = int(sum(DMED.mapped('number_of_days')))
		SUBSIDIO = int(sum(DSUB.mapped('number_of_days')))
		FALTAS = int(sum(FAL.mapped('number_of_days')))
		L_CON_GOCE = int(sum(LCGH.mapped('number_of_days')))
		L_SIN_GOCE = int(sum(LSGH.mapped('number_of_days')))

		# DLAB = self.get_dlabs()
		# DLAB_DEC_INT = modf(DLAB * Contract.resource_calendar_id.hours_per_day)

		HORAS_DIURNAS = sum(HDLAB.mapped('number_of_hours'))
		HORAS_NOCTURNAS = sum(HDLABN.mapped('number_of_hours'))
		HORAS_TARDANZA = sum(TAR.mapped('number_of_hours'))
		HORAS_EXT_25 = sum(HE25.mapped('number_of_hours'))
		HORAS_EXT_35 = sum(HE35.mapped('number_of_hours'))
		HORAS_EXT_100 = sum(HE100.mapped('number_of_hours'))
		HORAS_EXT_NOC = sum(HNOC.mapped('number_of_hours'))
		year = self.date_from.year
		month = self.date_from.month
		days_in_month = calendar.monthrange(year, month)[1]

		INCOME = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.income_categories.ids and sr.total > 0)
		DISCOUNTS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.discounts_categories.ids and sr.total > 0)
		CONTRIBUTIONS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_categories.ids and sr.total > 0)
		CONTRIBUTIONS_EMP = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_emp_categories.ids and sr.total > 0)

		INCOME_TOTAL = modf(sum(INCOME.mapped('total')))

		DISCOUNTS_TOTAL_01 = modf(sum(DISCOUNTS.mapped('total')))
		DISCOUNTS_TOTAL_02 = modf(sum(CONTRIBUTIONS.mapped('total')))
		CONTRIBUTIONS_EMP_TOTAL = modf(sum(CONTRIBUTIONS_EMP.mapped('total')))
		TOTAL_RENU = sum(INCOME_TOTAL)
		TOTAL_DESCU = sum(DISCOUNTS_TOTAL_02 + DISCOUNTS_TOTAL_01)
		TOTAL_APO = sum(CONTRIBUTIONS_EMP_TOTAL)

		NET_TO_PAY = self.line_ids.filtered(lambda sr: sr.salary_rule_id == MainParameter.net_to_pay_sr_id)

		SRC_00 = {'Ingresos': INCOME}
		SRC_01 = {'Descuentos': DISCOUNTS, 'Aportes Trabajador': CONTRIBUTIONS}

		elements = []
		style_totales = ParagraphStyle(name='LEFT', alignment=TA_LEFT, fontSize=6, fontName="times-roman")
		style_cell_totales = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=6, fontName="times-roman")
		style_right_totales = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=6, fontName="times-roman")

		style_cell_sin_espaciado = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=5.3, leading=7,fontName="times-roman")
		style_cell_con_alineacion_abajo = ParagraphStyle(name='Center',	alignment=TA_CENTER,fontSize=5.3,leading=7,	fontName="times-roman",spaceBefore=-7)
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=6, fontName="times-roman")
		style_left_01 = ParagraphStyle(name='LEFT', alignment=TA_LEFT, fontSize=6, fontName="times-roman")
		style_left_name = ParagraphStyle(name='LEFT', alignment=TA_LEFT, fontSize=5.2, fontName="times-roman")
		style_left_cabecera = ParagraphStyle(name='LEFT', alignment=TA_LEFT, fontSize=6, leading=7, fontName="times-roman")

		border_style = ParagraphStyle(name='border_style',borderWidth=1,borderColor=colors.black,fontName='times-roman',fontSize=6,alignment=TA_CENTER,)
		border_style_1 = ParagraphStyle(name='border_style',fontName='times-roman', fontSize=5.0, alignment=TA_CENTER,)

		internal_width = [2.5 * cm]

		bg_color = colors.HexColor("#c5d9f1")
		spacer = Spacer(0, 5)

		I_0 = ReportBase.create_image(self.company_id.logo, MainParameter.dir_create_file + 'logo.jpg', 180.0, 50.0)
		data_header = [[I_0 if I_0 else '',	], ]
		data_header_0 = [[Paragraph(
			'<strong>BOLETA DE PAGO </strong><br/>'
			'%s'% (self.struct_type_id.name or '') + ' - ' + '%s' % (self.payslip_run_id.name or '') + '<br/>' 'del' + ' %s al %s ' % (self.date_from or '', self.date_to or '') +
			'<br/>D.S.001-98-TR<br/>REMUNERACIONES',border_style)], ]

		layout = [[data_header, data_header_0, data_header, data_header_0]]
		elements.append(Table(layout))
		y = 0
		data = [
			[Paragraph('RUC: %s' % self.company_id.vat or '', style_left_cabecera),	Paragraph('', style_left_cabecera),],
			[Paragraph(self.company_id.name or '', style_left_cabecera),	Paragraph('', style_left_cabecera)],
		]
		layout = [[data, data]]
		elements.append(Table(layout))

		data_1 = [
			[Paragraph(Employee.identification_id or '-', style_left_01),
			 Paragraph(Employee.name or '-', style_left_name),
			 Paragraph('Días Laborados:', style_left_01),
			 Paragraph(str(DIAS_LABORADOS) + ' ' + ' día(s)' or '0', style_left_01),
			 Paragraph('Faltas:', style_left_01),
			 Paragraph(str(FALTAS) + ' ' + 'día(s)' or '0', style_left_01)
			 ],
			[Paragraph('Tipo de Personal:', style_left_01),
			 Paragraph(str(Contract.worker_type_id.name) or '', style_left_01),
			 Paragraph('Vac.Gozadas:', style_left_01),
			 Paragraph(str(DIAS_VACACIONES) + ' ' + 'día(s)' or '0', style_left_01),
			 Paragraph('Lic. con Goce', style_left_01),
			 Paragraph(str(L_CON_GOCE) + ' día(s)', style_left_01)
			 ],
			[Paragraph('Departamento:', style_left_01),
			 Paragraph(str(Contract.department_id.name) or '', style_left_01),
			 Paragraph('Des. Médicos:', style_left_01),
			 Paragraph(str(DESCANSO_MEDICO) + ' ' + 'día(s)' or '0', style_left_01),
			 Paragraph('Lic. sin Goce:', style_left_01),
			 Paragraph(str(L_SIN_GOCE) + ' día(s)', style_left_01)
			 ],
			[Paragraph('Ocupación:', style_left_01),
			 Paragraph(str(Contract.job_id.name) or '', style_left_01),
			 Paragraph('Subsidio', style_left_01),
			 Paragraph(str(SUBSIDIO) + ' ' + 'día(s)' or '0', style_left_01),
			 Paragraph('', style_left_01),
			 Paragraph('', style_left_01)
			 ],
			[Paragraph('Reg. Pensiones:', style_left_01),
			 Paragraph(str(Contract.membership_id.name) or '', style_left_01),
			 Paragraph('Hrs.Trabajadas D:', style_left_01),
			 Paragraph("{:.2f}".format(float(HORAS_DIURNAS)) + ' ' + 'Hr(s)' or '0', style_left_01),
			 Paragraph('Tardanza:', style_left_01),
			 Paragraph("{:.2f}".format(float(HORAS_TARDANZA)) + ' ' + 'Hr(s)' or '0', style_left_01)
			 ],
			[Paragraph('Cuspp:', style_left_01),
			 Paragraph(Contract.cuspp or '', style_left_01),
			 Paragraph('Hrs.Trabajadas N:', style_left_01),
			 Paragraph("{:.2f}".format(float(HORAS_NOCTURNAS)) + ' ' + 'Hr(s)' or '0', style_left_01),
			 Paragraph('', style_left_01),
			 Paragraph('', style_left_01)
			 ],
			[Paragraph('Banco:', style_left_01),
			 Paragraph(Employee.wage_bank_account_id.bank_id.name or '', style_left_01),
			Paragraph('Hrs.Extra D:', style_left_01),
			 Paragraph('(25%)' + ' ' + "{:.2f}".format(float(HORAS_EXT_25)) + ' ' + '(35%)' + ' ' + "{:.2f}".format(
					 float(HORAS_EXT_35)) + ' ' + '(100%)' + ' ' + "{:.2f}".format(float(HORAS_EXT_100)), style_left_01),
			 Paragraph('', style_left_01),
			 Paragraph('', style_left_01)
			 ],
			[Paragraph('Cuenta:', style_left_01),
			 Paragraph(Employee.wage_bank_account_id.acc_number or '', style_left_01),
			 Paragraph('Hrs.Extra N:', style_left_01),
			 Paragraph("{:.2f}".format(float(HORAS_EXT_NOC)), style_left_01),
			 Paragraph('', style_left_01),
			 Paragraph('', style_left_01)
			 ],
			[Paragraph('Fecha Ingreso:', style_left_01),
			 Paragraph(str(admission_date) or '', style_left_01),
			 Paragraph('Sueldo:', style_left_01),
			 Paragraph('S/.' + str(Contract.wage or '0.00'), style_left_01),
			 Paragraph('', style_left_01),
			 Paragraph('', style_left_01)
			 ],
		]

		tabla_datas_1 = Table(data_1,
							  colWidths=[2 * cm, 4.4 * cm, 2 * cm, 1.6 * cm, 1.8 * cm, 1.3 * cm],
							  rowHeights=[0.4 * cm] * 9)

		estilo_tablas = [
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('TOPPADDING', (0, 0), (-1, -1), 8),  # Espacio superior de 10 puntos en la primera fila
			('BOX', (0, 0), (-1, 0), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (-1, -2), 0.25, colors.black),
			('BOX', (0, 0), (-1, -3), 0.25, colors.black),
			('BOX', (0, 0), (-1, -4), 0.25, colors.black),
			('BOX', (0, 0), (-1, -5), 0.25, colors.black),
			('BOX', (0, 0), (-1, -6), 0.25, colors.black),
			('BOX', (0, 0), (-1, -7), 0.25, colors.black),
			('BOX', (0, 0), (-1, -8), 0.25, colors.black),
			('BOX', (0, 0), (-1, -9), 0.25, colors.black),
			('LINEBEFORE', (2, 0), (2, 0), 0.25, colors.black),
			('LINEBEFORE', (2, 1), (2, 1), 0.25, colors.black),
			('LINEBEFORE', (2, 2), (2, 2), 0.25, colors.black),
			('LINEBEFORE', (2, 3), (2, 3), 0.25, colors.black),
			('LINEBEFORE', (2, 4), (2, 4), 0.25, colors.black),
			('LINEBEFORE', (2, 5), (2, 5), 0.25, colors.black),
			('LINEBEFORE', (2, 6), (2, 6), 0.25, colors.black),
			('LINEBEFORE', (2, 7), (2, 7), 0.25, colors.black),
			('LINEBEFORE', (2, 8), (2, 8), 0.25, colors.black),

			('LINEBEFORE', (4, 0), (4, 0), 0.25, colors.black),
			('LINEBEFORE', (4, 1), (4, 1), 0.25, colors.black),
			('LINEBEFORE', (4, 2), (4, 2), 0.25, colors.black),
			('LINEBEFORE', (4, 3), (4, 3), 0.25, colors.black),
			('LINEBEFORE', (4, 4), (4, 4), 0.25, colors.black),
			('LINEBEFORE', (4, 5), (4, 5), 0.25, colors.black),
			('LINEBEFORE', (4, 6), (4, 6), 0.25, colors.black),
			('SPAN', (3, 6), (5, 6))
		]

		tabla_datas_1.setStyle(estilo_tablas)
		layout = [[tabla_datas_1, tabla_datas_1]]
		elements.append(Table(layout))

		data_1_1 = [[Paragraph('<strong>INGRESOS</strong>', style_cell_totales),]]
		y = 0
		for i in SRC_00:
			for primera in SRC_00[i]:
				data_1_1 += [[
					Paragraph(primera.name or '', style_left),
					Paragraph("{:.2f}".format(float(primera.total)) or '0.00', style_right),
				]]
				y += 1

		data_2_2 = [[Paragraph('<strong>DESCUENTOS</strong>', style_cell_totales),]]
		y = 0
		for ii in SRC_01:
			for segundo in SRC_01[ii]:
				data_2_2 += [[
					Paragraph(segundo.name or '', style_left),
					Paragraph("{:.2f}".format(float(segundo.total)) or '0.00' if segundo.category_id.type == 'out' else '',style_right),
				]]
				y += 1

		data_3_3 = [[Paragraph('<strong>APORTES</strong>', style_cell_totales),]]
		y = 0
		for iii in CONTRIBUTIONS_EMP:
			data_3_3 += [[
				Paragraph(iii.name or '', style_left),
				Paragraph("{:.2f}".format(float(iii.total)) or '0.00' if iii.category_id.type == 'out' else '',style_right),
			]]
			y += 1

		# Determinar el número máximo de filas que debe tener cada tabla
		max_rows = max(len(data_1_1), len(data_2_2), len(data_3_3))

		# Añadir celdas vacías a las tablas con menos información para completar el tamaño
		for data in [data_1_1, data_2_2, data_3_3]:
			while len(data) < max_rows:
				data.append([''] * len(data[0]))

		tabla_1 = Table(data_1_1, colWidths=[3.1 * cm, 1.4 * cm],rowHeights=[0.4 * cm] * max_rows)
		tabla_2 = Table(data_2_2, colWidths=[3.2 * cm, 1.4 * cm],rowHeights=[0.4 * cm] * max_rows)
		tabla_3 = Table(data_3_3, colWidths=[2.1 * cm, 1.2 * cm],rowHeights=[0.4 * cm] * max_rows)

		estilo_tablas = [('BACKGROUND', (0, 0), (-1, 0), bg_color),
						 ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
						 ('BOX', (0, 0), (-1, 0), 0.25, colors.black),
						 ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
						 ]

		tabla_1.setStyle(estilo_tablas)
		tabla_2.setStyle(estilo_tablas)
		tabla_3.setStyle(estilo_tablas)

		layout = [[tabla_1, tabla_2, tabla_3, tabla_1, tabla_2, tabla_3]]

		elements.append(Table(layout))
		saldo_1 = NET_TO_PAY.total
		saldo_2 = float(sum(RETE_MES.mapped('amount')))
		saldo_3 = float(sum(ADEU_MES.mapped('amount')))
		neto_depositar = float(saldo_1 - saldo_2 + saldo_3)

		data = [
			[Paragraph('<strong>TOTAL INGRESOS</strong>', style_totales),
			 Paragraph('<strong>' + "{:.2f}".format(float(TOTAL_RENU)) + '</strong>', style_cell),
			 Paragraph('<strong>TOTAL DESCUENTOS</strong>', style_totales),
			 Paragraph('<strong>' + "{:.2f}".format(float(TOTAL_DESCU)) + '</strong>', style_right),
			 Paragraph('<strong>TOTAL APORTES</strong>', style_cell_totales),
			 Paragraph('<strong>' + "{:.2f}".format(float(TOTAL_APO)) + '</strong>', style_right_totales),
			 ],
			[Paragraph('<strong>NETO DEL MES</strong>', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('<strong>' + str(NET_TO_PAY.total) + '</strong>', style_right_totales),
			 ],
			[Paragraph('<strong>RETENCIONES DEL MES</strong>', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('<strong>' + "{:.2f}".format(float(sum(RETE_MES.mapped('amount')))) + '</strong>', style_right_totales),
			],
			[Paragraph('<strong>ADEUDOS DE MES ANTERIOR</strong>', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('<strong>' + "{:.2f}".format(float(sum(ADEU_MES.mapped('amount')))) + '</strong>', style_right_totales),
			 ],
			[Paragraph('<strong>NETO A DEPOSITAR</strong>', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('', style_cell_totales),
			 Paragraph('<strong>' + "{:.2f}".format(neto_depositar) + '</strong>', style_right),
			 ],
		]
		tabla_datas_1 = Table(data,
							  colWidths=[3.3 * cm, 1.4 * cm, 3.3 * cm, 1.4 * cm, 2.4 * cm, 1.4 * cm],
							  rowHeights=[0.4 * cm] * 5)

		estilo_tablas = [
			('BACKGROUND', (0, 1), (-1, 1), bg_color),
			('BACKGROUND', (0, 4), (-1, 4), bg_color),
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('TOPPADDING', (0, 0), (-1, -1), 9),  # Espacio superior de 10 puntos en la primera fila
			('BOX', (0, 0), (-1, 0), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (-1, -2), 0.25, colors.black),
			('BOX', (0, 0), (-1, -3), 0.25, colors.black),
			('BOX', (0, 0), (-1, -4), 0.25, colors.black),
			('BOX', (0, 0), (-1, -5), 0.25, colors.black),
			('BOX', (0, 0), (-1, -6), 0.25, colors.black),
			('SPAN', (0, 1), (4, 1)),
			('SPAN', (0, 2), (4, 2)),
			('SPAN', (0, 3), (4, 3)),
			('SPAN', (0, 4), (4, 4)),
			('SPAN', (0, 5), (2, 5)),
			# ('INNERGRID', (0, 0), (-1, 0), 0.25, colors.black)
			('INNERGRID', (0, 1), (-1, 1), 0.25, colors.black),
			('INNERGRID', (0, 2), (-1, 2), 0.25, colors.black),
			('INNERGRID', (0, 3), (-1, 3), 0.25, colors.black),
			('INNERGRID', (0, 4), (-1, 4), 0.25, colors.black)
		]

		tabla_datas_1.setStyle(estilo_tablas)
		layout = [[tabla_datas_1, tabla_datas_1]]
		elements.append(Table(layout))

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 180.0, 60.0)
		data = [
			['', '',],
			[I if I else '', '',],
			[Paragraph('',	style_cell_sin_espaciado),
			 Paragraph('<strong>__________________________</strong><br/><strong>TRABAJADOR</strong><br/>' + Employee.name + '<br/>' +
					   'DNI:' + Employee.identification_id + '<br/><br/>', style_cell_sin_espaciado)],
		]
		tabla_datas_1 = Table(data, colWidths=[2.6 * inch, 2.6 * inch], rowHeights=[0.4 * inch] * 3)
		simple_style = [
			('INNERGRID', (0, 0), (-1, 0), 0.25, colors.black),
			('INNERGRID', (0, 1), (-1, 1), 0.25, colors.black),
			('INNERGRID', (0, 2), (-1, 2), 0.25, colors.black),
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('TOPPADDING', (0, 0), (-1, -1), 7),  # Espacio superior de 10 puntos en la primera fila
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]
		tabla_datas_1.setStyle(simple_style)
		layout = [[tabla_datas_1, tabla_datas_1]]

		elements.append(Table(layout))

		data_header_0 = [[Paragraph('<strong>R.R.H.H.</strong>', border_style_1)], ]
		data_header_1 = [[Paragraph('<strong>TRABAJADOR</strong><br/>', border_style_1)], ]

		tabla_datas_1 = Table(data_header_0, colWidths=[1.5 * inch], rowHeights=[0.2 * inch] * 1)
		tabla_datas_2 = Table(data_header_1, colWidths=[1.5 * inch], rowHeights=[0.2 * inch] * 1)

		simple_styles = [
			('INNERGRID', (0, 0), (-1, 0), 0.25, colors.black),
			('INNERGRID', (0, 1), (-1, 1), 0.25, colors.black),
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('TOPPADDING', (0, 0), (-1, -1), 9),  # Espacio superior de 10 puntos en la primera fila
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]
		tabla_datas_1.setStyle(simple_styles)
		tabla_datas_2.setStyle(simple_styles)

		layout = [[tabla_datas_1, tabla_datas_2]]
		elements.append(Table(layout))

		elements.append(PageBreak())
		return elements
