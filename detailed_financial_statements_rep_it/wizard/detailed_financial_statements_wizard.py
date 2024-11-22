# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
import base64
from io import BytesIO
import re
import uuid

class DetailedFinancialStatementsWizard(models.TransientModel):
	_name = "detailed.financial.statements.wizard"

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final',required=True)
	currency_id = fields.Many2one('res.currency', string='Moneda',required=True, default=lambda self: self.env.company.currency_id.id)
	type_show =  fields.Selection([('excel','Excel'),('txt','TXT'),('screen','Pantalla')],string=u'Mostrar en', required=True, default='excel')


	def get_report(self):
		for i in self:
			if i.type_show == 'excel':
				return i.get_excel()
			elif i.type_show == 'txt':
				return i.get_txt()
			else:
				return i.get_screen()
	
	def get_screen(self):
		self.env.cr.execute("""
					   DROP VIEW IF EXISTS detailed_financial_statements_screen CASCADE;
					   CREATE OR REPLACE view detailed_financial_statements_screen as (SELECT row_number() OVER () AS id, T.* FROM ("""+self._get_sql()+""")T)""")
		return {
				'name': 'Detalle de Estados Financieros',
				'type': 'ir.actions.act_window',
				'res_model': 'detailed.financial.statements.screen',
				'view_mode': 'tree',
			}

		
	
	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'detalle_estados_financieros.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("DETALLE DE EF")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','LIBRO ','VOUCHER','GRUPO','CUENTA','DEBE','HABER','BALANCE','IMPORTE MONEDA','MONEDA','FECHA','TD','NRO_COMP','TIPO ESTADO FINANCIERO']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		#Totals#
		debe, haber, balance= 0, 0, 0
		self.env.cr.execute(self._get_sql())
		res = self.env.cr.dictfetchall()

		for line in res:
			worksheet.write(x,0,line['periodo'] if line['periodo'] else '',formats['especial1'])
			worksheet.write(x,1,line['libro'] if line['libro'] else '',formats['especial1'])
			worksheet.write(x,2,line['voucher'] if line['voucher'] else '',formats['especial1'])
			worksheet.write(x,3,line['group'] if line['group'] else 0,formats['especial1'])
			worksheet.write(x,4,line['account'] if line['account'] else 0,formats['especial1'])
			worksheet.write(x,5,line['debe'] if line['debe'] else 0,formats['numberdos'])
			worksheet.write(x,6,line['haber'] if line['haber'] else 0,formats['numberdos'])
			worksheet.write(x,7,line['balance'] if line['balance'] else 0,formats['numberdos'])
			worksheet.write(x,8,line['amount_currency'] if line['amount_currency'] else 0,formats['numberdos'])
			worksheet.write(x,9,line['currency_id'] if line['currency_id'] else 0,formats['especial1'])
			worksheet.write(x,10,line['date'] if line['date'] else 0,formats['dateformat'])
			worksheet.write(x,11,line['td'] if line['td'] else 0,formats['especial1'])
			worksheet.write(x,12,line['nro_comp'] if line['nro_comp'] else 0,formats['especial1'])
			worksheet.write(x,14,line['type_ef'] if line['type_ef'] else '',formats['numberdos'])
			x += 1
			debe += line['debe'] if line['debe'] else 0
			haber += line['haber'] if line['haber'] else 0
			balance += line['balance'] if line['balance'] else 0

		worksheet.write(x,5,debe,formats['numbertotal'])
		worksheet.write(x,6,haber,formats['numbertotal'])
		worksheet.write(x,7,balance,formats['numbertotal'])
		
		widths = [12,12,12,12,25,12,12,12,12,12,12,12,12,40]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'detalle_estados_financieros.xlsx', 'rb')
		return self.env['popup.it'].get_file('Detalle de Estados Financieros.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def _get_sql(self):
		for i in self:
			if i.currency_id.name == 'PEN':
				sql ="""
						SELECT 
							vst1.periodo,
							vst1.libro,
							vst1.voucher,
							LEFT(aa.code,2) as group,
							CONCAT(aa.code,' ',aa.name->>'es_PE'::character varying) as account,
							vst1.debe,
							vst1.haber,
							vst1.balance,
							aml.amount_currency as amount_currency,
							vst1.moneda as currency_id,
							vst1.fecha as date,
							vst1.td_sunat as td,
							vst1.nro_comprobante as nro_comp,
							ati.name as type_ef
						FROM get_diariog('%s','%s',%d) vst1
						LEFT JOIN account_account aa ON aa.id = vst1.account_id
						LEFT JOIN account_type_it ati ON ati.id = aa.account_type_it_id
						LEFT JOIN account_move_line aml ON aml.id = vst1.move_line_id
						WHERE ati.id is not null
						""" % (i.period_from.date_start.strftime('%Y/%m/%d'),
							i.period_to.date_end.strftime('%Y/%m/%d'),
							i.company_id.id)
			else:
				sql ="""
						SELECT 
							vst1.periodo,
							vst1.libro,
							vst1.voucher,
							LEFT(aa.code,2) as group,
							CONCAT(aa.code,' ',aa.name->>'es_PE'::character varying) as account,
							vst1.debe,
							vst1.haber,
							vst1.balance,
							aml.amount_currency as amount_currency,
							vst1.moneda as currency_id,
							vst1.fecha as date,
							vst1.td_sunat as td,
							vst1.nro_comprobante as nro_comp,
							ati.name as type_ef
						FROM get_diariog_usd('%s','%s',%d) vst1
						LEFT JOIN account_account aa ON aa.id = vst1.account_id
						LEFT JOIN account_type_it ati ON ati.id = aa.account_type_it_id
						LEFT JOIN account_move_line aml ON aml.id = vst1.move_line_id
						WHERE ati.id is not null
						""" % (i.period_from.date_start.strftime('%Y/%m/%d'),
							i.period_to.date_end.strftime('%Y/%m/%d'),
							i.company_id.id)
			return sql

	def get_txt(self):
		sql = self._get_sql()
		self.env.cr.execute(sql)
		sql = "COPY (%s) TO STDOUT WITH %s" % (sql, "CSV DELIMITER '|'")	
		output = BytesIO()		
		self.env.cr.copy_expert(sql, output)		
		csv_content = output.getvalue().decode('utf-8')
		csv_lines = csv_content.split('\n')
		csv_lines.pop(len(csv_lines)-1)
		csv_lines_with_cr = [line + '\r' for line in csv_lines]
		csv_content_with_cr = '\n'.join(csv_lines_with_cr)
		csv_content_with_cr += '\n'
		res = base64.b64encode(csv_content_with_cr.encode('utf-8'))
		output.close()
		name_doc = "detalle_estados_financieros.txt"		
		res = res if res else base64.encodebytes(b"== Sin Registros ==")
		return self.env['popup.it'].get_file(name_doc,res)