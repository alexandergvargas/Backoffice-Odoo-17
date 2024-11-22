# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

import codecs
import pprint

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

import time
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import *

class AccountBalancePeriodRep(models.TransientModel):
	_inherit = 'account.balance.period.rep'

	group_partner_id = fields.Many2one('group.partner', string='Grupo')
	sala_id = fields.Many2one('game.sala', string='Sala')
	all_check = fields.Boolean('Mostrar Todo')
	
	@api.onchange('all_check')
	def get_all_dates(self):
		for i in self:
			if i.company_id:
				if i.all_check:					
					fiscal_year = self.env['account.fiscal.year'].search([],order='name asc',limit=1)					
					if fiscal_year:
						i.date_from = fiscal_year.date_from
						i.date_to = self.env['account.fiscal.year'].search([],order='name desc',limit=1).date_to
				else:
					i.get_fiscal_year()

	@api.onchange('company_id')
	def get_fiscal_year(self):
		for i in self:
			if i.company_id:
				today = fields.Date.today()
				fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
				if fiscal_year:
					i.fiscal_year_id = fiscal_year.id
					i.date_from = fiscal_year.date_from
					i.date_to = fiscal_year.date_to
				

	def get_report(self):
		self.domain_dates()
		if self.type_show == 'pantalla':
			self.env.cr.execute("""CREATE OR REPLACE view account_balance_period_book as (%s)"""%(self._get_sql()))
			
			if self.env.context.get('type'):
				
				return {
				'name': 'Saldo por Fecha Contable',
				'type': 'ir.actions.act_window',
				'res_model': 'account.balance.period.book',
				'view_mode': 'tree',	
				'view_id': self.env.ref('account_balance_doc_rep_it_transatlantic.view_account_balance_period_book_tree_new').id,			
				
				}
				
			else:
				return {
					'name': 'Saldo por Fecha Contable',
					'type': 'ir.actions.act_window',
					'res_model': 'account.balance.period.book',
					'view_mode': 'tree',
					'view_type': 'form',
					'views': [(False, 'tree')],
				}

		if self.type_show == 'excel':
			return self.get_excel()

		if self.type_show == 'pdf':
			return self.get_pdf()

	def domain_dates(self):
		if not self.env.context.get('type'):
			if self.date_from:
				if self.fiscal_year_id.date_from.year != self.date_from.year:
					raise UserError("La fecha inicial no esta en el rango del Año Fiscal escogido (Ejercicio).")
			if self.date_to:
				if self.fiscal_year_id.date_from.year != self.date_to.year:
					raise UserError("La fecha final no esta en el rango del Año Fiscal escogido (Ejercicio).")
			if self.date_from and self.date_to:
				if self.date_to < self.date_from:
					raise UserError("La fecha final no puede ser menor a la fecha inicial.")

	def _get_sql(self):
		
		sql_group = """"""
		if self.group_partner_id:
			sql_group = "rp.group_partner_id = %s"%(self.group_partner_id.id)
		sql_salas = """"""
		if self.sala_id:
				sql_salas = "AND ll.sala = %s"%(self.sala_id.id)
		if self.only_pending == 'all':
			sql_type = ""
		elif self.only_pending == 'not_payment':
			sql_type = "AND a1.saldo_mn <> 0"
		else:
			sql_type = "AND a1.saldo_mn = 0"
		
		sql_type_account = """"""
		sql_partner = """"""
		sql_account = """"""

		if self.partner_id:
			sql_partner = """and a1.partner_id = %s""" % (self.partner_id.id)
		if self.account_id:
			sql_account = """and a1.account_id = %s""" % (self.account_id.id)
		if self.type_account:
			sql_type_account = """and a3.type = '%s'""" % (self.type_account)
		sql = """SELECT a1.*,ll.sala as sala_id,
		 		CASE 
					WHEN a1.fecha_ven IS NOT NULL THEN (CURRENT_DATE - a1.fecha_ven)::integer					
				ELSE 0::integer
				END AS days_past_due FROM get_saldos('%s','%s',%d) a1
				LEFT JOIN account_account a2 ON a2.id = a1.account_id
				LEFT JOIN account_account_type a3 ON a3.id = a2.user_type_id
				LEFT JOIN liquidacion_lines ll ON ll.name = a1.nro_comprobante
				LEFT JOIN res_partner rp ON rp.id = a1.partner_id
				WHERE a2.id is not null %s %s %s %s %s %s"""% (
				self.date_from.strftime('%Y/%m/%d'),
				self.date_to.strftime('%Y/%m/%d'),
				self.company_id.id,
				sql_type_account,
				sql_partner,
				sql_account,
				sql_type,
				sql_group,
				sql_salas
			)
		return sql

	
	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Saldo_por_Fecha_Cont.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Saldo por Fecha Contable")
		worksheet.set_tab_color('blue')
		HEADERS = ['PERIODO','FEC CON','LIBRO','VOUCHER','TDP','RUC','PARTNER','TD','NRO COMP','FEC DOC','FEC VEN','CUENTA', 'MONEDA','DEBE','HABER','SALDO MN','SALDO ME']
		if self.env.context.get('type'):
			HEADERS = ['PERIODO','FEC CON','LIBRO','VOUCHER','TDP','RUC','PARTNER','TD','NRO COMP','FEC DOC','FEC VEN','CUENTA', 'MONEDA','DEBE','HABER','SALDO MN','SALDO ME','GRUPO','SALA']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		#Totals#
		debe, haber, saldo_mn, saldo_me = 0, 0, 0, 0
		self.env.cr.execute(self._get_sql())
		res = self.env.cr.dictfetchall()
		
		for line in res:
			worksheet.write(x,0,line['periodo'] if line['periodo'] else '',formats['especial1'])
			worksheet.write(x,1,line['fecha_con'] if line['fecha_con'] else '',formats['dateformat'])
			worksheet.write(x,2,line['libro'] if line['libro'] else '',formats['especial1'])
			worksheet.write(x,3,line['voucher'] if line['voucher'] else '',formats['especial1'])
			worksheet.write(x,4,line['td_partner'] if line['td_partner'] else '',formats['especial1'])
			worksheet.write(x,5,line['doc_partner'] if line['doc_partner'] else '',formats['especial1'])
			worksheet.write(x,6,line['partner'] if line['partner'] else '',formats['especial1'])
			worksheet.write(x,7,line['td_sunat'] if line['td_sunat'] else '',formats['especial1'])
			worksheet.write(x,8,line['nro_comprobante'] if line['nro_comprobante'] else '',formats['especial1'])
			worksheet.write(x,9,line['fecha_doc'] if line['fecha_doc'] else '',formats['dateformat'])
			worksheet.write(x,10,line['fecha_ven'] if line['fecha_ven'] else '',formats['dateformat'])
			worksheet.write(x,11,line['cuenta'] if line['cuenta'] else '',formats['especial1'])
			worksheet.write(x,12,line['moneda'] if line['moneda'] else '',formats['especial1'])
			worksheet.write(x,13,line['debe'] if line['debe'] else 0,formats['numberdos'])
			worksheet.write(x,14,line['haber'] if line['haber'] else 0,formats['numberdos'])
			worksheet.write(x,15,line['saldo_mn'] if line['saldo_mn'] else 0,formats['numberdos'])
			worksheet.write(x,16,line['saldo_me'] if line['saldo_me'] else 0,formats['numberdos'])
			if self.env.context.get('type'):
				worksheet.write(x,17,line['group_partner_id'] if line['group_partner_id'] else 0,formats['especial1'])
				worksheet.write(x,18,line['sala_id'] if line['sala_id'] else 0,formats['especial1'])
				worksheet.write(x,19,line['days_past_due'] if line['days_past_due'] else 0,formats['especial1'])
			x += 1
			debe += line['debe'] if line['debe'] else 0
			haber += line['haber'] if line['haber'] else 0
			saldo_mn += line['saldo_mn'] if line['saldo_mn'] else 0
			saldo_me += line['saldo_me'] if line['saldo_me'] else 0

		worksheet.write(x,13,debe,formats['numbertotal'])
		worksheet.write(x,14,haber,formats['numbertotal'])
		worksheet.write(x,15,saldo_mn,formats['numbertotal'])
		worksheet.write(x,16,saldo_me,formats['numbertotal'])

		widths = [7,10,10,10,4,11,40,4,10,10,10,10,12,12,12,12]
		if self.env.context.get('type'):
			widths = [7,10,10,10,4,11,40,4,10,10,10,10,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Saldo_por_Fecha_Cont.xlsx', 'rb')
		return self.env['popup.it'].get_file('Saldo por Fecha Contable.xlsx',base64.encodebytes(b''.join(f.readlines())))

	