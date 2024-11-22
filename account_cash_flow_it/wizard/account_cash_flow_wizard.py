# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from datetime import datetime, timedelta
import locale
import os
import calendar

locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

class AccountCashFlowWizard(models.TransientModel):
	_name = 'account.cash.flow.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio Fiscal',required=True)
	type = fields.Selection([('month','Meses'),('week','Semanas')],default='month',string='En base a')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def get_report(self):
		parameters = self.env['account.main.parameter'].search([('company_id', '=', self.company_id.id)], limit=1)
		import io
		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Flujo_Caja.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		title = workbook.add_format({'bold': True})
		title.set_align('center')
		title.set_align('vcenter')
		title.set_bg_color('#5b2b84')
		title.set_font_color('#ffffff')
		title.set_font_size(16)
		title.set_font_name('Calibri')

		subtitle_purple10 = workbook.add_format({'bold': True})
		subtitle_purple10.set_align('center')
		subtitle_purple10.set_align('vcenter')
		subtitle_purple10.set_bg_color('#5b2b84')
		subtitle_purple10.set_font_color('#ffffff')
		subtitle_purple10.set_font_size(10)
		subtitle_purple10.set_font_name('Calibri')

		subtitle_purple12 = workbook.add_format({'bold': True})
		subtitle_purple12.set_align('left')
		subtitle_purple12.set_align('vcenter')
		subtitle_purple12.set_bg_color('#5b2b84')
		subtitle_purple12.set_font_color('#ffffff')
		subtitle_purple12.set_font_size(12)
		subtitle_purple12.set_font_name('Calibri')

		subtitle_green10 = workbook.add_format({'bold': True})
		subtitle_green10.set_align('center')
		subtitle_green10.set_align('vcenter')
		subtitle_green10.set_bg_color('#519226')
		subtitle_green10.set_font_color('#ffffff')
		subtitle_green10.set_font_size(10)
		subtitle_green10.set_font_name('Calibri')

		footitle_orange12 = workbook.add_format({'bold': True})
		footitle_orange12.set_align('left')
		footitle_orange12.set_align('vcenter')
		footitle_orange12.set_bg_color('#eaab01')
		footitle_orange12.set_font_color('#ffffff')
		footitle_orange12.set_font_size(10)
		footitle_orange12.set_font_name('Calibri')

		footitle_gray12 = workbook.add_format({'bold': True})
		footitle_gray12.set_align('left')
		footitle_gray12.set_align('vcenter')
		footitle_gray12.set_bg_color('#a6a6a6')
		footitle_gray12.set_font_color('#ffffff')
		footitle_gray12.set_font_size(10)
		footitle_gray12.set_font_name('Calibri')

		category_style = workbook.add_format({'bold': True,'border': 1,'border_color': '#D9D9D9'})
		category_style.set_align('left')
		category_style.set_align('vcenter')
		category_style.set_font_size(10)
		category_style.set_font_name('Calibri')

		subcategory_style = workbook.add_format({'italic': True,'border': 1,'border_color': '#D9D9D9'})
		subcategory_style.set_align('left')
		subcategory_style.set_align('vcenter')
		subcategory_style.set_font_size(9)
		subcategory_style.set_font_name('Calibri')

		head_style = workbook.add_format({'bold': True,'border': 1,'border_color': '#D9D9D9'})
		head_style.set_align('center')
		head_style.set_align('vcenter')
		head_style.set_font_size(10)
		head_style.set_font_name('Calibri')

		numbersiproy = workbook.add_format({'num_format':'0.00','border': 1,'border_color': '#D9D9D9'})
		numbersiproy.set_align('right')
		numbersiproy.set_align('vcenter')
		numbersiproy.set_font_size(12)
		numbersiproy.set_font_name('Calibri')

		numbersireal = workbook.add_format({'bold': True,'num_format':'0.00','border': 1,'border_color': '#D9D9D9'})
		numbersireal.set_align('right')
		numbersireal.set_align('vcenter')
		numbersireal.set_bg_color('#ffe699')
		numbersireal.set_font_color('#ff0000')
		numbersireal.set_font_size(12)
		numbersireal.set_font_name('Calibri')

		numberproy = workbook.add_format({'num_format':'0.00','border': 1,'border_color': '#D9D9D9'})
		numberproy.set_align('right')
		numberproy.set_align('vcenter')
		numberproy.set_font_size(10)
		numberproy.set_font_name('Calibri')

		numberreal = workbook.add_format({'num_format':'0.00','border': 1,'border_color': '#D9D9D9'})
		numberreal.set_align('right')
		numberreal.set_align('vcenter')
		numberreal.set_bg_color('#fce4d6')
		numberreal.set_font_size(10)
		numberreal.set_font_name('Calibri')

		subnumberproy = workbook.add_format({'bold': True,'num_format':'0.00','border': 1,'border_color': '#D9D9D9'})
		subnumberproy.set_align('right')
		subnumberproy.set_align('vcenter')
		subnumberproy.set_bg_color('#d9e1f2')
		subnumberproy.set_font_size(12)
		subnumberproy.set_font_name('Calibri')

		subnumberreal = workbook.add_format({'bold': True,'num_format':'0.00','border': 1,'border_color': '#D9D9D9'})
		subnumberreal.set_align('right')
		subnumberreal.set_align('vcenter')
		subnumberreal.set_bg_color('#f4b084')
		subnumberreal.set_font_size(12)
		subnumberreal.set_font_name('Calibri')

		totalnumberproy = workbook.add_format({'bold': True,'num_format':'0.00','border': 1,'border_color': '#D9D9D9'})
		totalnumberproy.set_align('right')
		totalnumberproy.set_align('vcenter')
		totalnumberproy.set_bg_color('#fce4d6')
		totalnumberproy.set_font_size(12)
		totalnumberproy.set_font_name('Calibri')

		totalnumberreal = workbook.add_format({'bold': True,'num_format':'0.00','border': 1,'border_color': '#D9D9D9'})
		totalnumberreal.set_align('right')
		totalnumberreal.set_align('vcenter')
		totalnumberreal.set_bg_color('#f8cbad')
		totalnumberreal.set_font_size(12)
		totalnumberreal.set_font_name('Calibri')

		totaltotalnumberproy = workbook.add_format({'bold': True,'num_format':'0.00','border': 1,'border_color': '#D9D9D9'})
		totaltotalnumberproy.set_align('right')
		totaltotalnumberproy.set_align('vcenter')
		totaltotalnumberproy.set_bg_color('#bdd7ee')
		totaltotalnumberproy.set_font_size(12)
		totaltotalnumberproy.set_font_name('Calibri')

		totaltotalnumberreal = workbook.add_format({'bold': True,'num_format':'0.00','border': 1,'border_color': '#D9D9D9'})
		totaltotalnumberreal.set_align('right')
		totaltotalnumberreal.set_align('vcenter')
		totaltotalnumberreal.set_bg_color('#f4b084')
		totaltotalnumberreal.set_font_size(12)
		totaltotalnumberreal.set_font_name('Calibri')

		numberpercent = workbook.add_format({'num_format':'0.00%','border': 1,'border_color': '#D9D9D9'})
		numberpercent.set_align('right')
		numberpercent.set_align('vcenter')
		numberpercent.set_font_size(10)
		numberpercent.set_font_name('Calibri')

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("FLUJO CAJA")
		worksheet.hide_gridlines(option=2)
		worksheet.set_tab_color('brown')

		#logo = os.path.dirname(os.path.abspath(__file__))+'/../static/src/img/vesper.png'
		#worksheet.insert_image('F2', logo,{'x_scale': 0.15, 'y_scale': 0.15})

		worksheet.merge_range(2,1,2,2, "FLUJO DE CAJA %s (REAL Y PROYECTADO)"%('MENSUAL' if self.type == 'month' else 'SEMANAL'), title)
		worksheet.write(3,1,u'Año:')
		worksheet.write(3,2,self.fiscal_year_id.name)

		worksheet.write(6,1,u'Grupo',subtitle_purple10)
		#worksheet.write(6,2,u'Sub Categoria',subtitle_purple10)
		worksheet.write(6,2,u'Moneda',subtitle_purple10)

		worksheet.write(8,1,u'SALDO INICIAL DE CAJA',footitle_orange12)
		worksheet.write(8,2,u'PEN',footitle_orange12)

		x=10

		#################INGRESOS##################################################33

		worksheet.merge_range(x,1,x,2,u'INGRESOS',subtitle_purple12)
		x+=1
		fc = self.env['account.cash.flow'].search([('grupo','=','2')])
		pos_ini_1 = x
		for cash in fc:
			worksheet.write(x,1,cash.name,subcategory_style)
			worksheet.write(x,2,'PEN',subcategory_style)
			x+=1
		pos_fin_1 = x-1

		x+=1

		worksheet.write(x,1,u'Total Ingresos',footitle_gray12)
		worksheet.write(x,2,u'PEN',footitle_gray12)
		pos_ingresos_op = x

		x+=3

		#################EGRESOS##################################################33

		worksheet.merge_range(x,1,x,2,u'EGRESOS',subtitle_purple12)
		x+=1
		fc = self.env['account.cash.flow'].search([('grupo','=','3')])
		pos_ini_4 = x
		for cash in fc:
			worksheet.write(x,1,cash.name,subcategory_style)
			worksheet.write(x,2,'PEN',subcategory_style)
			x+=1
		pos_fin_4 = x-1
		x+=1

		worksheet.write(x,1,u'Total Egresos',footitle_gray12)
		worksheet.write(x,2,u'PEN',footitle_gray12)
		pos_egresos_op = x
		x+=2

		########################################################################################################

		worksheet.write(x,1,u'Flujo Operativo',footitle_orange12)
		worksheet.write(x,2,u'PEN',footitle_orange12)
		pos_flujo_op = x
		x+=3

		#####################################FINANCIAMIENTO##################################################33

		worksheet.merge_range(x,1,x,2,u'FINANCIAMIENTO',subtitle_purple12)
		x+=1
		fc = self.env['account.cash.flow'].search([('grupo','=','4')])
		pos_ini_7 = x
		for cash in fc:
			worksheet.write(x,1,cash.name,subcategory_style)
			worksheet.write(x,2,'PEN',subcategory_style)
			x+=1
		pos_fin_7 = x-1

		x+=1

		worksheet.write(x,1,u'Total Financiamiento',footitle_gray12)
		worksheet.write(x,2,u'PEN',footitle_gray12)
		pos_ing_fin = x
		x+=3

		########################################################################################################

		worksheet.write(x,1,u'Flujo Operativo y Financiero',footitle_orange12)
		worksheet.write(x,2,u'PEN',footitle_orange12)

		x+=3

		worksheet.write(x,1,u'SALDO FINAL DE CAJA',footitle_orange12)
		worksheet.write(x,2,u'PEN',footitle_orange12)

		pos_fin = x

		y = 4

		widths = [1,54,16]
			
		if self.type == 'month':
			periods = self.env['account.period'].search([('fiscal_year_id','=',self.fiscal_year_id.id),('is_opening_close','=',False)])
			for per in periods:
				x = 5
				worksheet.write(x,y,u'Var',head_style)
				worksheet.write(x,y+1,u'Proy. Total',head_style)
				x+=1
				worksheet.write(x,y,u'%',subtitle_purple10)
				worksheet.write(x,y+1,datetime.strptime(per.name, '%B-%Y').strftime('%b-%y'),subtitle_purple10)
				worksheet.write(x,y+2,"%s Real"%datetime.strptime(per.name, '%B-%Y').strftime('%b-%y'),subtitle_green10)

				x+=2
				#SALDO INICIAL
				if per.code[4:] == '01':
					worksheet.write(x,y+1,self.get_saldo('am.date',False,self.fiscal_year_id.date_from,self.fiscal_year_id.date_from,False,opening_close="TRUE"),numbersiproy)
					worksheet.write(x,y+2,self.get_saldo('am.date',False,self.fiscal_year_id.date_from,self.fiscal_year_id.date_from,False,opening_close="TRUE"),numbersireal)
				else:
					worksheet.write_formula(x,y+1, '=' + xl_rowcol_to_cell(pos_fin,y-3), numbersiproy)
					worksheet.write_formula(x,y+2, '=' + xl_rowcol_to_cell(pos_fin,y-2), numbersireal)

				x+=3
				#INGRESOS
				fc = self.env['account.cash.flow'].search([('grupo','=','2')])
				for cash in fc:
					worksheet.write_formula(x,y,'=IF(' + xl_rowcol_to_cell(x,y+1) + '<>0,' + xl_rowcol_to_cell(x,y+2) + '/' + xl_rowcol_to_cell(x,y+1) + ',0)',numberpercent)
					worksheet.write_number(x,y+1,self.get_saldo_proy('aml.date_maturity',(per.date_start),(per.date_end),cta_cte_origen='TRUE',flujo_id=cash.id),numberproy)
					worksheet.write_number(x,y+2,self.get_saldo('aml.date',True,(per.date_start),(per.date_end),True,opening_close="FALSE",flujo_id=cash.id),numberreal)
					x+=1
				x+=1
				worksheet.write_formula(x,y+1, '=sum(' + xl_rowcol_to_cell(pos_ini_1,y+1) +':' +xl_rowcol_to_cell(pos_fin_1,y+1) + ')', subnumberproy)
				worksheet.write_formula(x,y+2, '=sum(' + xl_rowcol_to_cell(pos_ini_1,y+2) +':' +xl_rowcol_to_cell(pos_fin_1,y+2) + ')', subnumberreal)

				x+=4
				#EGRESOS
				fc = self.env['account.cash.flow'].search([('grupo','=','3')])
				for cash in fc:
					worksheet.write_formula(x,y,'=IF(' + xl_rowcol_to_cell(x,y+1) + '<>0,' + xl_rowcol_to_cell(x,y+2) + '/' + xl_rowcol_to_cell(x,y+1) + ',0)',numberpercent)
					worksheet.write_number(x,y+1,self.get_saldo_proy('aml.date_maturity',(per.date_start),(per.date_end),cta_cte_origen='TRUE',flujo_id=cash.id)*-1,numberproy)
					worksheet.write_number(x,y+2,self.get_saldo('aml.date',True,(per.date_start),(per.date_end),True,opening_close="FALSE",flujo_id=cash.id)*-1,numberreal)
					x+=1
				x+=1
				worksheet.write_formula(x,y+1, '=sum(' + xl_rowcol_to_cell(pos_ini_4,y+1) +':' +xl_rowcol_to_cell(pos_fin_4,y+1) + ')', subnumberproy)
				worksheet.write_formula(x,y+2, '=sum(' + xl_rowcol_to_cell(pos_ini_4,y+2) +':' +xl_rowcol_to_cell(pos_fin_4,y+2) + ')', subnumberreal)
				x+=2

				#FLUJO OPERATIVO
				worksheet.write_formula(x,y+1, '='+ xl_rowcol_to_cell(pos_ingresos_op,y+1) + '-' + xl_rowcol_to_cell(pos_egresos_op,y+1), totalnumberproy)
				worksheet.write_formula(x,y+2, '='+ xl_rowcol_to_cell(pos_ingresos_op,y+2) + '-' + xl_rowcol_to_cell(pos_egresos_op,y+2), totalnumberreal)

				x+=4
				#FINANCIAMIENTO
				fc = self.env['account.cash.flow'].search([('grupo','=','4')])
				for cash in fc:
					worksheet.write_formula(x,y,'=IF(' + xl_rowcol_to_cell(x,y+1) + '<>0,' + xl_rowcol_to_cell(x,y+2) + '/' + xl_rowcol_to_cell(x,y+1) + ',0)',numberpercent)
					worksheet.write_number(x,y+1,self.get_saldo_proy('aml.date_maturity',(per.date_start),(per.date_end),cta_cte_origen='TRUE',flujo_id=cash.id),numberproy)
					worksheet.write_number(x,y+2,self.get_saldo('aml.date',True,(per.date_start),(per.date_end),True,opening_close="FALSE",flujo_id=cash.id),numberreal)
					x+=1
				x+=1
				worksheet.write_formula(x,y+1, '=sum(' + xl_rowcol_to_cell(pos_ini_7,y+1) +':' +xl_rowcol_to_cell(pos_fin_7,y+1) + ')', subnumberproy)
				worksheet.write_formula(x,y+2, '=sum(' + xl_rowcol_to_cell(pos_ini_7,y+2) +':' +xl_rowcol_to_cell(pos_fin_7,y+2) + ')', subnumberreal)
				x+=3

				#FLUJO OPERATIVO Y FINANCIERO
				worksheet.write_formula(x,y+1, '='+ xl_rowcol_to_cell(pos_flujo_op,y+1) + '+' + xl_rowcol_to_cell(pos_ing_fin,y+1), totalnumberproy)
				worksheet.write_formula(x,y+2, '='+ xl_rowcol_to_cell(pos_flujo_op,y+2) + '+' + xl_rowcol_to_cell(pos_ing_fin,y+2), totalnumberreal)

				x+=3
				#SALDO FINAL DE CAJA
				worksheet.write_formula(x,y+1, '='+ xl_rowcol_to_cell(8,y+1) + '+' + xl_rowcol_to_cell(x-3,y+1), totaltotalnumberproy)
				worksheet.write_formula(x,y+2, '='+ xl_rowcol_to_cell(8,y+2) + '+' + xl_rowcol_to_cell(x-3,y+2), totaltotalnumberreal)
				widths.append(1)
				widths.append(9)
				widths.append(12)
				widths.append(12)

				y+=4

			##################################################ANUAL##################################################
			x = 5
			worksheet.write(x,y,u'Var',head_style)
			worksheet.write(x,y+1,u'Proy. Total',head_style)
			x+=1
			worksheet.write(x,y,u'%',subtitle_purple10)
			worksheet.write(x,y+1,'Anual-%s'%self.fiscal_year_id.name,subtitle_purple10)
			worksheet.write(x,y+2,'Anual-%s Real'%self.fiscal_year_id.name,subtitle_green10)

			x+=2
			worksheet.write(x,y+1,self.get_saldo('am.date',False,self.fiscal_year_id.date_from,self.fiscal_year_id.date_from,False,opening_close="TRUE"),numbersiproy)
			worksheet.write(x,y+2,self.get_saldo('am.date',False,self.fiscal_year_id.date_from,self.fiscal_year_id.date_from,False,opening_close="TRUE"),numbersireal)

			x+=3
			#INGRESOS
			fc = self.env['account.cash.flow'].search([('grupo','=','2')])
			for cash in fc:
				worksheet.write_formula(x,y,'=IF(' + xl_rowcol_to_cell(x,y+1) + '<>0,' + xl_rowcol_to_cell(x,y+2) + '/' + xl_rowcol_to_cell(x,y+1) + ',0)',numberpercent)
				worksheet.write_number(x,y+1,self.get_saldo_proy('aml.date_maturity',(self.fiscal_year_id.date_from),(self.fiscal_year_id.date_to),cta_cte_origen='TRUE',flujo_id=cash.id),numberproy)
				worksheet.write_number(x,y+2,self.get_saldo('aml.date',True,(self.fiscal_year_id.date_from),(self.fiscal_year_id.date_to),True,opening_close="FALSE",flujo_id=cash.id),numberreal)
				x+=1
			x+=1
			worksheet.write_formula(x,y+1, '=sum(' + xl_rowcol_to_cell(pos_ini_1,y+1) +':' +xl_rowcol_to_cell(pos_fin_1,y+1) + ')', subnumberproy)
			worksheet.write_formula(x,y+2, '=sum(' + xl_rowcol_to_cell(pos_ini_1,y+2) +':' +xl_rowcol_to_cell(pos_fin_1,y+2) + ')', subnumberreal)

			x+=4
			#EGRESOS
			fc = self.env['account.cash.flow'].search([('grupo','=','3')])
			for cash in fc:
				worksheet.write_formula(x,y,'=IF(' + xl_rowcol_to_cell(x,y+1) + '<>0,' + xl_rowcol_to_cell(x,y+2) + '/' + xl_rowcol_to_cell(x,y+1) + ',0)',numberpercent)
				worksheet.write_number(x,y+1,self.get_saldo_proy('aml.date_maturity',(self.fiscal_year_id.date_from),(self.fiscal_year_id.date_to),cta_cte_origen='TRUE',flujo_id=cash.id)*-1,numberproy)
				worksheet.write_number(x,y+2,self.get_saldo('aml.date',True,(self.fiscal_year_id.date_from),(self.fiscal_year_id.date_to),True,opening_close="FALSE",flujo_id=cash.id)*-1,numberreal)
				x+=1
			x+=1
			worksheet.write_formula(x,y+1, '=sum(' + xl_rowcol_to_cell(pos_ini_4,y+1) +':' +xl_rowcol_to_cell(pos_fin_4,y+1) + ')', subnumberproy)
			worksheet.write_formula(x,y+2, '=sum(' + xl_rowcol_to_cell(pos_ini_4,y+2) +':' +xl_rowcol_to_cell(pos_fin_4,y+2) + ')', subnumberreal)
			x+=2

			#FLUJO OPERATIVO
			worksheet.write_formula(x,y+1, '='+ xl_rowcol_to_cell(pos_ingresos_op,y+1) + '-' + xl_rowcol_to_cell(pos_egresos_op,y+1), totalnumberproy)
			worksheet.write_formula(x,y+2, '='+ xl_rowcol_to_cell(pos_ingresos_op,y+2) + '-' + xl_rowcol_to_cell(pos_egresos_op,y+2), totalnumberreal)

			x+=4
			#FINANCIAMIENTO
			fc = self.env['account.cash.flow'].search([('grupo','=','4')])
			for cash in fc:
				worksheet.write_formula(x,y,'=IF(' + xl_rowcol_to_cell(x,y+1) + '<>0,' + xl_rowcol_to_cell(x,y+2) + '/' + xl_rowcol_to_cell(x,y+1) + ',0)',numberpercent)
				worksheet.write_number(x,y+1,self.get_saldo_proy('aml.date_maturity',(self.fiscal_year_id.date_from),(self.fiscal_year_id.date_to),cta_cte_origen='TRUE',flujo_id=cash.id),numberproy)
				worksheet.write_number(x,y+2,self.get_saldo('aml.date',True,(self.fiscal_year_id.date_from),(self.fiscal_year_id.date_to),True,opening_close="FALSE",flujo_id=cash.id),numberreal)
				x+=1
			x+=1
			worksheet.write_formula(x,y+1, '=sum(' + xl_rowcol_to_cell(pos_ini_7,y+1) +':' +xl_rowcol_to_cell(pos_fin_7,y+1) + ')', subnumberproy)
			worksheet.write_formula(x,y+2, '=sum(' + xl_rowcol_to_cell(pos_ini_7,y+2) +':' +xl_rowcol_to_cell(pos_fin_7,y+2) + ')', subnumberreal)
			x+=3

			#FLUJO OPERATIVO Y FINANCIERO
			worksheet.write_formula(x,y+1, '='+ xl_rowcol_to_cell(pos_flujo_op,y+1) + '+' + xl_rowcol_to_cell(pos_ing_fin,y+1), totalnumberproy)
			worksheet.write_formula(x,y+2, '='+ xl_rowcol_to_cell(pos_flujo_op,y+2) + '+' + xl_rowcol_to_cell(pos_ing_fin,y+2), totalnumberreal)

			x+=3
			#SALDO FINAL DE CAJA
			worksheet.write_formula(x,y+1, '='+ xl_rowcol_to_cell(8,y+1) + '+' + xl_rowcol_to_cell(x-3,y+1), totaltotalnumberproy)
			worksheet.write_formula(x,y+2, '='+ xl_rowcol_to_cell(8,y+2) + '+' + xl_rowcol_to_cell(x-3,y+2), totaltotalnumberreal)
			widths.append(1)
			widths.append(9)
			widths.append(20)
			widths.append(20)
		else:
			periods = self.env['account.period'].search([('fiscal_year_id','=',self.fiscal_year_id.id),('is_opening_close','=',False)])
			week_pos = 0
			for per in periods:
				x = 5
				worksheet.write(x,y,u'Var',head_style)
				worksheet.write(x,y+1,u'Proy. Total',head_style)
				x+=1
				worksheet.write(x,y,u'%',subtitle_purple10)
				worksheet.write(x,y+1,datetime.strptime(per.name, '%B-%Y').strftime('%b-%y'),subtitle_purple10)
				weeks = self.weeks_from_year(int(self.fiscal_year_id.name))[per.code[4:]]
				c = 0
				for week in weeks:
					worksheet.write(x-1,y+c+2,week['start'].strftime('%d %B'),subtitle_green10)
					worksheet.write(x,y+c+2,week['end'].strftime('%d %B'),subtitle_green10)
					c+=1
				worksheet.write(x,y+c+2,"%s Real"%datetime.strptime(per.name, '%B-%Y').strftime('%b-%y'),subtitle_green10)

				x+=2
				#SALDO INICIAL
				if per.code[4:] == '01':
					worksheet.write(x,y+1,self.get_saldo('am.date',False,self.fiscal_year_id.date_from,self.fiscal_year_id.date_from,False,opening_close="TRUE"),numbersiproy)
					cw = 0
					for week in weeks:
						if week_pos == 0:
							worksheet.write(x,y+cw+2,self.get_saldo('am.date',False,self.fiscal_year_id.date_from,self.fiscal_year_id.date_from,False,opening_close="TRUE"),numbersireal)
						else:
							worksheet.write_formula(x,y+cw+2, '=' + xl_rowcol_to_cell(pos_fin,week_pos), numbersireal)
						week_pos=y+cw+2
						cw+=1
					worksheet.write(x,y+c+2,self.get_saldo('am.date',False,self.fiscal_year_id.date_from,self.fiscal_year_id.date_from,False,opening_close="TRUE"),numbersireal)
				else:
					worksheet.write_formula(x,y+1, '=' + xl_rowcol_to_cell(pos_fin,y-3-len(self.weeks_from_year(int(self.fiscal_year_id.name))[str(int(per.code[4:])-1).zfill(2)])), numbersiproy)
					####
					cw = 0
					for week in weeks:
						worksheet.write_formula(x,y+cw+2, '=' + xl_rowcol_to_cell(pos_fin,week_pos), numbersireal)
						week_pos=y+cw+2
						cw+=1
					####
					worksheet.write_formula(x,y+c+2, '=' + xl_rowcol_to_cell(pos_fin,y-2), numbersireal)

				x+=3
				#INGRESOS
				fc = self.env['account.cash.flow'].search([('grupo','=','2')])
				for cash in fc:
					worksheet.write_formula(x,y,'=IF(' + xl_rowcol_to_cell(x,y+1) + '<>0,' + xl_rowcol_to_cell(x,y+c+2) + '/' + xl_rowcol_to_cell(x,y+1) + ',0)',numberpercent)
					worksheet.write_number(x,y+1,self.get_saldo_proy('aml.date_maturity',(per.date_start),(per.date_end),cta_cte_origen='TRUE',flujo_id=cash.id),numberproy)
					cw = 0
					for week in weeks:
						worksheet.write_number(x,y+cw+2,self.get_saldo('aml.date',True,(week['start']),(week['end']),True,opening_close="FALSE",flujo_id=cash.id),numberreal)
						cw+=1
					worksheet.write_number(x,y+c+2,self.get_saldo('aml.date',True,(per.date_start),(per.date_end),True,opening_close="FALSE",flujo_id=cash.id),numberreal)
					x+=1
				x+=1
				worksheet.write_formula(x,y+1, '=sum(' + xl_rowcol_to_cell(pos_ini_1,y+1) +':' +xl_rowcol_to_cell(pos_fin_1,y+1) + ')', subnumberproy)
				cw = 0
				for week in weeks:
					worksheet.write_formula(x,y+cw+2, '=sum(' + xl_rowcol_to_cell(pos_ini_1,y+cw+2) +':' +xl_rowcol_to_cell(pos_fin_1,y+cw+2) + ')', subnumberreal)
					cw+=1
				worksheet.write_formula(x,y+c+2, '=sum(' + xl_rowcol_to_cell(pos_ini_1,y+c+2) +':' +xl_rowcol_to_cell(pos_fin_1,y+c+2) + ')', subnumberreal)

				x+=4
				#EGRESOS
				fc = self.env['account.cash.flow'].search([('grupo','=','3')])
				for cash in fc:
					worksheet.write_formula(x,y,'=IF(' + xl_rowcol_to_cell(x,y+1) + '<>0,' + xl_rowcol_to_cell(x,y+c+2) + '/' + xl_rowcol_to_cell(x,y+1) + ',0)',numberpercent)
					worksheet.write_number(x,y+1,self.get_saldo_proy('aml.date_maturity',(per.date_start),(per.date_end),cta_cte_origen='TRUE',flujo_id=cash.id)*-1,numberproy)
					cw = 0
					for week in weeks:
						worksheet.write_number(x,y+cw+2,self.get_saldo('aml.date',True,(week['start']),(week['end']),True,opening_close="FALSE",flujo_id=cash.id)*-1,numberreal)
						cw+=1
					worksheet.write_number(x,y+c+2,self.get_saldo('aml.date',True,(per.date_start),(per.date_end),True,opening_close="FALSE",flujo_id=cash.id)*-1,numberreal)
					x+=1
				x+=1
				worksheet.write_formula(x,y+1, '=sum(' + xl_rowcol_to_cell(pos_ini_4,y+1) +':' +xl_rowcol_to_cell(pos_fin_4,y+1) + ')', subnumberproy)
				cw = 0
				for week in weeks:
					worksheet.write_formula(x,y+cw+2, '=sum(' + xl_rowcol_to_cell(pos_ini_4,y+cw+2) +':' +xl_rowcol_to_cell(pos_fin_4,y+cw+2) + ')', subnumberreal)
					cw+=1
				worksheet.write_formula(x,y+c+2, '=sum(' + xl_rowcol_to_cell(pos_ini_4,y+c+2) +':' +xl_rowcol_to_cell(pos_fin_4,y+c+2) + ')', subnumberreal)
				x+=2

				#FLUJO OPERATIVO
				worksheet.write_formula(x,y+1, '='+ xl_rowcol_to_cell(pos_ingresos_op,y+1) + '-' + xl_rowcol_to_cell(pos_egresos_op,y+1), totalnumberproy)
				cw = 0
				for week in weeks:
					worksheet.write_formula(x,y+cw+2, '='+ xl_rowcol_to_cell(pos_ingresos_op,y+cw+2) + '-' + xl_rowcol_to_cell(pos_egresos_op,y+cw+2), totalnumberreal)
					cw+=1
				worksheet.write_formula(x,y+c+2, '='+ xl_rowcol_to_cell(pos_ingresos_op,y+c+2) + '-' + xl_rowcol_to_cell(pos_egresos_op,y+c+2), totalnumberreal)

				x+=4
				#FINANCIAMIENTO
				fc = self.env['account.cash.flow'].search([('grupo','=','4')])
				for cash in fc:
					worksheet.write_formula(x,y,'=IF(' + xl_rowcol_to_cell(x,y+1) + '<>0,' + xl_rowcol_to_cell(x,y+c+2) + '/' + xl_rowcol_to_cell(x,y+1) + ',0)',numberpercent)
					worksheet.write_number(x,y+1,self.get_saldo_proy('aml.date_maturity',(per.date_start),(per.date_end),cta_cte_origen='TRUE',flujo_id=cash.id),numberproy)
					cw = 0
					for week in weeks:
						worksheet.write_number(x,y+cw+2,self.get_saldo('aml.date',True,(week['start']),(week['end']),True,opening_close="FALSE",flujo_id=cash.id),numberreal)
						cw+=1
					worksheet.write_number(x,y+c+2,self.get_saldo('aml.date',True,(per.date_start),(per.date_end),True,opening_close="FALSE",flujo_id=cash.id),numberreal)
					x+=1
				x+=1
				worksheet.write_formula(x,y+1, '=sum(' + xl_rowcol_to_cell(pos_ini_7,y+1) +':' +xl_rowcol_to_cell(pos_fin_7,y+1) + ')', subnumberproy)
				cw = 0
				for week in weeks:
					worksheet.write_formula(x,y+cw+2, '=sum(' + xl_rowcol_to_cell(pos_ini_7,y+cw+2) +':' +xl_rowcol_to_cell(pos_fin_7,y+cw+2) + ')', subnumberreal)
					cw+=1
				worksheet.write_formula(x,y+c+2, '=sum(' + xl_rowcol_to_cell(pos_ini_7,y+c+2) +':' +xl_rowcol_to_cell(pos_fin_7,y+c+2) + ')', subnumberreal)
				x+=3

				#FLUJO OPERATIVO Y FINANCIERO
				worksheet.write_formula(x,y+1, '='+ xl_rowcol_to_cell(pos_flujo_op,y+1) + '+' + xl_rowcol_to_cell(pos_ing_fin,y+1), totalnumberproy)
				cw = 0
				for week in weeks:
					worksheet.write_formula(x,y+cw+2, '='+ xl_rowcol_to_cell(pos_flujo_op,y+cw+2) + '+' + xl_rowcol_to_cell(pos_ing_fin,y+cw+2), totalnumberreal)
					cw+=1
				worksheet.write_formula(x,y+c+2, '='+ xl_rowcol_to_cell(pos_flujo_op,y+c+2) + '+' + xl_rowcol_to_cell(pos_ing_fin,y+c+2), totalnumberreal)

				x+=3
				#SALDO FINAL DE CAJA
				worksheet.write_formula(x,y+1, '='+ xl_rowcol_to_cell(8,y+1) + '+' + xl_rowcol_to_cell(x-3,y+1), totaltotalnumberproy)
				cw = 0
				for week in weeks:
					worksheet.write_formula(x,y+cw+2, '='+ xl_rowcol_to_cell(8,y+cw+2) + '+' + xl_rowcol_to_cell(x-3,y+cw+2), totaltotalnumberreal)
					cw+=1
				worksheet.write_formula(x,y+c+2, '='+ xl_rowcol_to_cell(8,y+c+2) + '+' + xl_rowcol_to_cell(x-3,y+c+2), totaltotalnumberreal)
				widths.append(1)
				widths.append(9)
				widths.append(12)
				for week in weeks:
					widths.append(12)
				widths.append(12)
				y+=(c+4)

			##################################################ANUAL##################################################
			x = 5
			worksheet.write(x,y,u'Var',head_style)
			worksheet.write(x,y+1,u'Proy. Total',head_style)
			x+=1
			worksheet.write(x,y,u'%',subtitle_purple10)
			worksheet.write(x,y+1,'Anual-%s'%self.fiscal_year_id.name,subtitle_purple10)
			worksheet.write(x,y+2,'Anual-%s Real'%self.fiscal_year_id.name,subtitle_green10)

			x+=2
			worksheet.write(x,y+1,self.get_saldo('am.date',False,self.fiscal_year_id.date_from,self.fiscal_year_id.date_from,False,opening_close="TRUE"),numbersiproy)
			worksheet.write(x,y+2,self.get_saldo('am.date',False,self.fiscal_year_id.date_from,self.fiscal_year_id.date_from,False,opening_close="TRUE"),numbersireal)

			x+=3
			#INGRESOS
			fc = self.env['account.cash.flow'].search([('grupo','=','2')])
			for cash in fc:
				worksheet.write_formula(x,y,'=IF(' + xl_rowcol_to_cell(x,y+1) + '<>0,' + xl_rowcol_to_cell(x,y+2) + '/' + xl_rowcol_to_cell(x,y+1) + ',0)',numberpercent)
				worksheet.write_number(x,y+1,self.get_saldo_proy('aml.date_maturity',(self.fiscal_year_id.date_from),(self.fiscal_year_id.date_to),cta_cte_origen='TRUE',flujo_id=cash.id),numberproy)
				worksheet.write_number(x,y+2,self.get_saldo('aml.date',True,(self.fiscal_year_id.date_from),(self.fiscal_year_id.date_to),True,opening_close="FALSE",flujo_id=cash.id),numberreal)
				x+=1
			x+=1
			worksheet.write_formula(x,y+1, '=sum(' + xl_rowcol_to_cell(pos_ini_1,y+1) +':' +xl_rowcol_to_cell(pos_fin_1,y+1) + ')', subnumberproy)
			worksheet.write_formula(x,y+2, '=sum(' + xl_rowcol_to_cell(pos_ini_1,y+2) +':' +xl_rowcol_to_cell(pos_fin_1,y+2) + ')', subnumberreal)

			x+=4
			#EGRESOS
			fc = self.env['account.cash.flow'].search([('grupo','=','3')])
			for cash in fc:
				worksheet.write_formula(x,y,'=IF(' + xl_rowcol_to_cell(x,y+1) + '<>0,' + xl_rowcol_to_cell(x,y+2) + '/' + xl_rowcol_to_cell(x,y+1) + ',0)',numberpercent)
				worksheet.write_number(x,y+1,self.get_saldo_proy('aml.date_maturity',(self.fiscal_year_id.date_from),(self.fiscal_year_id.date_to),cta_cte_origen='TRUE',flujo_id=cash.id)*-1,numberproy)
				worksheet.write_number(x,y+2,self.get_saldo('aml.date',True,(self.fiscal_year_id.date_from),(self.fiscal_year_id.date_to),True,opening_close="FALSE",flujo_id=cash.id)*-1,numberreal)
				x+=1
			x+=1
			worksheet.write_formula(x,y+1, '=sum(' + xl_rowcol_to_cell(pos_ini_4,y+1) +':' +xl_rowcol_to_cell(pos_fin_4,y+1) + ')', subnumberproy)
			worksheet.write_formula(x,y+2, '=sum(' + xl_rowcol_to_cell(pos_ini_4,y+2) +':' +xl_rowcol_to_cell(pos_fin_4,y+2) + ')', subnumberreal)
			x+=2

			#FLUJO OPERATIVO
			worksheet.write_formula(x,y+1, '='+ xl_rowcol_to_cell(pos_ingresos_op,y+1) + '-' + xl_rowcol_to_cell(pos_egresos_op,y+1), totalnumberproy)
			worksheet.write_formula(x,y+2, '='+ xl_rowcol_to_cell(pos_ingresos_op,y+2) + '-' + xl_rowcol_to_cell(pos_egresos_op,y+2), totalnumberreal)

			x+=4
			#FINANCIAMIENTO
			fc = self.env['account.cash.flow'].search([('grupo','=','4')])
			for cash in fc:
				worksheet.write_formula(x,y,'=IF(' + xl_rowcol_to_cell(x,y+1) + '<>0,' + xl_rowcol_to_cell(x,y+2) + '/' + xl_rowcol_to_cell(x,y+1) + ',0)',numberpercent)
				worksheet.write_number(x,y+1,self.get_saldo_proy('aml.date_maturity',(self.fiscal_year_id.date_from),(self.fiscal_year_id.date_to),cta_cte_origen='TRUE',flujo_id=cash.id),numberproy)
				worksheet.write_number(x,y+2,self.get_saldo('aml.date',True,(self.fiscal_year_id.date_from),(self.fiscal_year_id.date_to),True,opening_close="FALSE",flujo_id=cash.id),numberreal)
				x+=1
			x+=1
			worksheet.write_formula(x,y+1, '=sum(' + xl_rowcol_to_cell(pos_ini_7,y+1) +':' +xl_rowcol_to_cell(pos_fin_7,y+1) + ')', subnumberproy)
			worksheet.write_formula(x,y+2, '=sum(' + xl_rowcol_to_cell(pos_ini_7,y+2) +':' +xl_rowcol_to_cell(pos_fin_7,y+2) + ')', subnumberreal)
			x+=3

			#FLUJO OPERATIVO Y FINANCIERO
			worksheet.write_formula(x,y+1, '='+ xl_rowcol_to_cell(pos_flujo_op,y+1) + '+' + xl_rowcol_to_cell(pos_ing_fin,y+1), totalnumberproy)
			worksheet.write_formula(x,y+2, '='+ xl_rowcol_to_cell(pos_flujo_op,y+2) + '+' + xl_rowcol_to_cell(pos_ing_fin,y+2), totalnumberreal)

			x+=3
			#SALDO FINAL DE CAJA
			worksheet.write_formula(x,y+1, '='+ xl_rowcol_to_cell(8,y+1) + '+' + xl_rowcol_to_cell(x-3,y+1), totaltotalnumberproy)
			worksheet.write_formula(x,y+2, '='+ xl_rowcol_to_cell(8,y+2) + '+' + xl_rowcol_to_cell(x-3,y+2), totaltotalnumberreal)
			widths.append(1)
			widths.append(9)
			widths.append(20)
			widths.append(20)
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Flujo_Caja.xlsx', 'rb')
		return self.env['popup.it'].get_file('Flujo de Caja de %s al %s.xlsx'%((str(self.fiscal_year_id.date_from)),(str(self.fiscal_year_id.date_to))),base64.encodebytes(b''.join(f.readlines())))

	def get_saldo(self,type_date,use_counterpart_cash_flow,date_start,date_end,filtro,opening_close=None,cta_cte_origen=None,flujo_id=None,sign=None):
		if date_end < date_start:
			return 0
		if not use_counterpart_cash_flow:
			sql = """select sum(coalesce(aml.debit) - coalesce(aml.credit)) as amount from account_move_line aml
					left join account_move am on am.id = aml.move_id
					left join account_account aa on aa.id = aml.account_id
					where (%s between '%s' and '%s') and left(aa.code,2) = '10' and am.company_id = %d AND am.state = 'posted'
					%s
					%s
					%s
					%s"""%(type_date,
					date_start.strftime('%Y/%m/%d'),
					date_end.strftime('%Y/%m/%d'),
					self.company_id.id, 
					"AND am.is_opening_close = %s"%(opening_close) if opening_close else "",
					"AND aml.cta_cte_origen = %s"%(cta_cte_origen) if cta_cte_origen else "",
					("and coalesce(aml.debit) - coalesce(aml.credit) %s 0"%(sign) if filtro and not flujo_id else ""),
					(" and aml.cash_flow_id = %d"%(flujo_id) if flujo_id else " and aml.cash_flow_id is null") if filtro else "")
		else:
			sql = """SELECT 
					sum(coalesce(aml.debit) - coalesce(aml.credit))*-1 as amount
					FROM account_move_line aml
					LEFT JOIN account_account aa ON aa.id = aml.account_id
					LEFT JOIN account_move am ON am.id = aml.move_id
					WHERE left(aa.code,2) <> '10' AND aml.move_id in (
					SELECT
					DISTINCT ON (aml.move_id) move_id
					FROM account_move_line aml
					LEFT JOIN account_account aa ON aa.id = aml.account_id
					LEFT JOIN account_move am ON am.id = aml.move_id
					WHERE am.state = 'posted'
					AND (%s BETWEEN '%s' AND '%s') AND am.company_id = %d
					AND left(aa.code,2) = '10')
					%s
					%s
					%s
					%s"""%(type_date,
					date_start.strftime('%Y/%m/%d'),
					date_end.strftime('%Y/%m/%d'),
					self.company_id.id, 
					"AND am.is_opening_close = %s"%(opening_close) if opening_close else "",
					"AND aml.cta_cte_origen = %s"%(cta_cte_origen) if cta_cte_origen else "",
					("and (coalesce(aml.debit) - coalesce(aml.credit))*-1 %s 0"%(sign) if filtro and not flujo_id else ""),
					(" and aa.account_cash_flow_id = %d"%(flujo_id) if flujo_id else " and aa.account_cash_flow_id is null") if filtro else "")
		self.env.cr.execute(sql)
		res =self.env.cr.fetchone()
		return (res[0] or 0) if res else 0
	
	
	def get_saldo_proy(self,type_date,date_start,date_end,opening_close=None,cta_cte_origen=None,flujo_id=None):
		if date_end < date_start:
			return 0
		sql = """select sum(coalesce(aml.debit) - coalesce(aml.credit)) as amount from account_move_line aml
				left join account_move am on am.id = aml.move_id
				left join account_account aa on aa.id = aml.account_id
				where (%s between '%s' and '%s') and aa.account_type in ('asset_receivable','liability_payable') and am.company_id = %d AND am.state = 'posted'
				%s
				%s
				%s"""%(type_date,
				date_start.strftime('%Y/%m/%d'),
				date_end.strftime('%Y/%m/%d'),
				self.company_id.id, 
				"AND am.is_opening_close = %s"%(opening_close) if opening_close else "",
				"AND aml.cta_cte_origen = %s"%(cta_cte_origen) if cta_cte_origen else "",
				(" and aa.account_cash_flow_id = %d"%(flujo_id) if flujo_id else " and aa.account_cash_flow_id is null"))
		self.env.cr.execute(sql)
		res =self.env.cr.fetchone()
		return (res[0] or 0) if res else 0
	
	def format_date(self,date_str):
		date_obj = datetime.strptime(date_str, "%B-%Y")
		formatted_date = date_obj.strftime("%b-%y").capitalize()
		return formatted_date
	
	def weeks_from_year(self,year):
		month_weeks = {}

		for month in range(1, 13):
			month_key = f"{month:02d}"

			first_day = date(year, month, 1)
			last_day_num = calendar.monthrange(year, month)[1]
			last_day = date(year, month, last_day_num)

			weeks = []

			first_weekday = first_day.weekday()

			days_until_sunday = 6 - first_weekday
			first_sunday = first_day + timedelta(days=days_until_sunday)

			if first_sunday > last_day:
				first_sunday = last_day

			weeks.append({
				'start': first_day,
				'end': first_sunday
			})

			current_start = first_sunday + timedelta(days=1)

			while current_start <= last_day:
				current_end = current_start + timedelta(days=6)
				if current_end > last_day:
					current_end = last_day
				weeks.append({
					'start': current_start,
					'end': current_end
				})
				current_start = current_end + timedelta(days=1)

			month_weeks[month_key] = weeks

		return month_weeks
