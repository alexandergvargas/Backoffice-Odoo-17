# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from datetime import datetime, timedelta

class AccountCashFlowRepAdvance(models.TransientModel):
	_name = 'account.cash.flow.rep.advance'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio Fiscal',required=True)
	show_by = fields.Selection([('date','Dias'),('period','Meses')],string='Clasificar por',default='date')
	period_from_id = fields.Many2one('account.period',string='Periodo Inicial')
	period_to_id = fields.Many2one('account.period',string='Periodo Final')
	date_from = fields.Date(string='Fecha Inicial')
	date_to = fields.Date(string='Fecha Final')
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True, default='pantalla')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def get_report(self):
		self.validate_dates()
		if self.type_show == 'pantalla':
			self.env.cr.execute("""DELETE FROM account_cash_flow_book_advance WHERE user_id = %d"""%(self.env.uid))
		
			self.env.cr.execute("""
				INSERT INTO account_cash_flow_book_advance (journal_id,voucher,fecha,glosa,account_id,amount,grupo,concepto,user_id) 
				("""+self._get_sql()+""")""")
			
			return {
					'name': 'Reporte de Flujo de Caja',
					'type': 'ir.actions.act_window',
					'res_model': 'account.cash.flow.book.advance',
					'view_mode': 'tree,pivot,graph',
					'view_type': 'form',
				}
		else:
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

			especial1_simple = workbook.add_format()
			especial1_simple.set_align('justify')
			especial1_simple.set_align('vcenter')
			especial1_simple.set_text_wrap()
			especial1_simple.set_font_size(10)
			especial1_simple.set_font_name('Times New Roman')

			numberdos_simple = workbook.add_format({'num_format':'0.00'})
			numberdos_simple.set_align('right')
			numberdos_simple.set_align('vcenter')
			numberdos_simple.set_font_size(10)
			numberdos_simple.set_font_name('Times New Roman')
			
			format_flujo_operativo = workbook.add_format({'bold': True})
			format_flujo_operativo.set_align('justify')
			format_flujo_operativo.set_align('vcenter')
			format_flujo_operativo.set_text_wrap()
			format_flujo_operativo.set_font_size(11)
			format_flujo_operativo.set_font_name('Times New Roman')
			format_flujo_operativo.set_bottom(6)
			format_flujo_operativo.set_top(1)

			formats['especial2'].set_underline()

			numberdosflujo_operativo = workbook.add_format({'num_format':'0.00','bold': True})
			numberdosflujo_operativo.set_align('right')
			numberdosflujo_operativo.set_align('vcenter')
			numberdosflujo_operativo.set_font_size(11)
			numberdosflujo_operativo.set_font_name('Times New Roman')
			numberdosflujo_operativo.set_bottom(6)
			numberdosflujo_operativo.set_top(1)

			import importlib
			import sys
			importlib.reload(sys)

			worksheet = workbook.add_worksheet("FLUJO CAJA")
			worksheet.set_tab_color('blue')

			HEADERS = ['CONCEPTO']
			if self.show_by == "date":
				day_arr = []
				dayi = self.date_from
				while dayi <= self.date_to:
					day_arr.append(dayi)
					dayi = dayi + timedelta(days=1)
				for i in day_arr:
					HEADERS.append(str(i))
			else:
				perr_arr = []
				perri = self.period_from_id
				while int(perri.code) <= int(self.period_to_id.code):
					perr_arr.append(perri)
					perri = self.env['account.period'].search([('code','=',str(int(perri.code)+1))], limit=1)
				for i in perr_arr:
					HEADERS.append(i.code)

			worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
			x = 2

			worksheet.write(x,0,'SALDO INICIAL',especial1_simple)

			x += 2

			worksheet.write(x,0,'INGRESOS',formats['especial2'])
			x += 1
			pos_ini_ingresos = x
			for ingresos in self.env['account.cash.flow'].search([('grupo','=','2')]):
				worksheet.write(x,0,ingresos.name,especial1_simple)
				x+= 1
			worksheet.write(x,0,'INGRESOS NO DEFINIDOS',especial1_simple)
			x+= 1
			pos_fin_ingresos = x-1
			worksheet.write(x,0,'TOTAL INGRESOS',formats['especial2'])
			x+= 2

			worksheet.write(x,0,'EGRESOS',formats['especial2'])
			x += 1
			pos_ini_egresos = x
			for egresos in self.env['account.cash.flow'].search([('grupo','=','3')]):
				worksheet.write(x,0,egresos.name,especial1_simple)
				x+= 1
			worksheet.write(x,0,'EGRESOS NO DEFINIDOS',especial1_simple)
			x+= 1
			pos_fin_egresos = x-1
			worksheet.write(x,0,'TOTAL EGRESOS',formats['especial2'])
			x+= 2

			worksheet.write(x,0,'FINANCIAMIENTO',formats['especial2'])
			#pos_flujo_op = x
			x += 1

			pos_ini_finan = x
			for finan in self.env['account.cash.flow'].search([('grupo','=','4')]):
				worksheet.write(x,0,finan.name,especial1_simple)
				x+= 1
			pos_fin_finan = x-1
			
			worksheet.write(x,0,'TOTAL FINANCIAMIENTO',formats['especial2'])
			x += 2

			worksheet.write(x,0,'SALDO FINAL',format_flujo_operativo)

			pos_saldo_final = x

			y = 1

			for iterator in (day_arr if self.show_by == 'date' else perr_arr): 
				x = 2
				if iterator == (self.date_from if self.show_by == 'date' else self.period_from_id):
					worksheet.write(x,y,self.get_saldo(False,datetime.strptime('%s/01/01'%(self.fiscal_year_id.name), '%Y/%m/%d').date(),(self.date_from if self.show_by == 'date' else self.period_from_id.date_start) - timedelta(days=1),False),numberdos_simple)
				else:
					worksheet.write_formula(x,y, '=' + xl_rowcol_to_cell(pos_saldo_final,y-1), numberdos_simple)
				x += 3

				for ingresos in self.env['account.cash.flow'].search([('grupo','=','2')]):
					worksheet.write(x,y,self.get_saldo(parameters.use_counterpart_cash_flow,(iterator if self.show_by == 'date' else iterator.date_start),(iterator if self.show_by == 'date' else iterator.date_end),True,ingresos.id),numberdos_simple)
					x+= 1
				worksheet.write(x,y,self.get_saldo(parameters.use_counterpart_cash_flow,(iterator if self.show_by == 'date' else iterator.date_start),(iterator if self.show_by == 'date' else iterator.date_end),True,sign='>'),numberdos_simple)
				x+=1
				worksheet.write_formula(x,y, '=sum(' + xl_rowcol_to_cell(pos_ini_ingresos,y) +':' +xl_rowcol_to_cell(pos_fin_ingresos,y) + ')', numberdosflujo_operativo)
				x += 3

				for egresos in self.env['account.cash.flow'].search([('grupo','=','3')]):
					worksheet.write(x,y,self.get_saldo(parameters.use_counterpart_cash_flow,(iterator if self.show_by == 'date' else iterator.date_start),(iterator if self.show_by == 'date' else iterator.date_end),True,egresos.id),numberdos_simple)
					x+= 1
				worksheet.write(x,y,self.get_saldo(parameters.use_counterpart_cash_flow,(iterator if self.show_by == 'date' else iterator.date_start),(iterator if self.show_by == 'date' else iterator.date_end),True,sign='<'),numberdos_simple)
				x+=1
				worksheet.write_formula(x,y, '=sum(' + xl_rowcol_to_cell(pos_ini_egresos,y) +':' +xl_rowcol_to_cell(pos_fin_egresos,y) + ')', numberdosflujo_operativo)
				x += 3

				for finan in self.env['account.cash.flow'].search([('grupo','=','4')]):
					worksheet.write(x,y,self.get_saldo(parameters.use_counterpart_cash_flow,(iterator if self.show_by == 'date' else iterator.date_start),(iterator if self.show_by == 'date' else iterator.date_end),True,finan.id),numberdos_simple)
					x+= 1
				if pos_ini_finan <= pos_fin_finan:
					worksheet.write_formula(x,y, '=sum(' + xl_rowcol_to_cell(pos_ini_finan,y) +':' +xl_rowcol_to_cell(pos_fin_finan,y) + ')', numberdosflujo_operativo)
				else:
					worksheet.write(x,y, 0, numberdosflujo_operativo)

				x+=2
				worksheet.write_formula(x,y, '='+ xl_rowcol_to_cell(2,y) + '+' + xl_rowcol_to_cell(pos_fin_ingresos+1,y) + '+' + xl_rowcol_to_cell(pos_fin_egresos+1,y) + '+' + xl_rowcol_to_cell(pos_fin_finan+1,y), numberdosflujo_operativo)
				y+=1
			
			widths = [40]
			for iterator in (day_arr if self.show_by == 'date' else perr_arr):
				widths.append(11)
			try:
				worksheet = ReportBase.resize_cells(worksheet,widths)
			except IndexError:
				raise UserError(u'El rango entre las fechas debe ser menor')
			workbook.close()

			f = open(direccion +'Flujo_Caja.xlsx', 'rb')
			return self.env['popup.it'].get_file('Flujo de Caja de %s al %s.xlsx'%((str(self.date_from) if self.show_by == 'date' else self.period_from_id.name),(str(self.date_to) if self.show_by == 'date' else self.period_to_id.name)),base64.encodebytes(b''.join(f.readlines())))

	def get_saldo(self,use_counterpart_cash_flow,date_start,date_end,filtro,flujo_id=None,sign=None):
		if date_end < date_start:
			return 0
		if not use_counterpart_cash_flow:
			sql = """select sum(coalesce(aml.debit) - coalesce(aml.credit)) as amount from account_move_line aml
					left join account_move am on am.id = aml.move_id
					left join account_account aa on aa.id = aml.account_id
					where (am.date between '%s' and '%s') and left(aa.code,2) = '10' and am.company_id = %d AND am.state = 'posted'
					%s
					%s"""%(date_start.strftime('%Y/%m/%d'),
					date_end.strftime('%Y/%m/%d'),
					self.company_id.id, 
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
					WHERE am.state = 'posted' AND  am.is_opening_close <> TRUE 
					AND (am.date BETWEEN '%s' AND '%s') AND am.company_id = %d
					AND left(aa.code,2) = '10')
					%s
					%s"""%(date_start.strftime('%Y/%m/%d'),
					date_end.strftime('%Y/%m/%d'),
					self.company_id.id, 
					("and (coalesce(aml.debit) - coalesce(aml.credit))*-1 %s 0"%(sign) if filtro and not flujo_id else ""),
					(" and aa.account_cash_flow_id = %d"%(flujo_id) if flujo_id else " and aa.account_cash_flow_id is null") if filtro else "")
		self.env.cr.execute(sql)
		res =self.env.cr.fetchone()
		return (res[0] or 0) if res else 0


	def _get_sql(self):
		parameters = self.env['account.main.parameter'].search([('company_id', '=', self.company_id.id)], limit=1)

		if not parameters:
			raise UserError('Faltan configurar los Parametros Principales para esta Compañía')
		if not parameters.use_counterpart_cash_flow:
			sql = """SELECT 
					T.journal_id,
					T.voucher,
					T.fecha,
					T.glosa,
					T.account_id,
					T.amount,
					CASE WHEN T.grupo = '1' THEN '1-SALDO INICIAL'
					WHEN T.grupo = '2' THEN '2-INGRESO'
					WHEN T.grupo = '3' THEN '3-EGRESO'
					WHEN T.grupo = '4' THEN '4-FINANCIAMIENTO' END AS grupo,
					T.concepto,
					{user_id} as user_id
					FROM (
					
					(SELECT 
					null as journal_id,
					null as voucher,
					'{date_from}' as fecha,
					'SALDO INICIAL' as glosa,
					aml.account_id,
					sum(coalesce(aml.debit) - coalesce(aml.credit)) as amount,
					'1' as grupo,
					'000' as code,
					'000-SALDO INICIAL' as concepto
					FROM account_move_line aml
					LEFT JOIN account_account aa ON aa.id = aml.account_id
					LEFT JOIN account_move am ON am.id = aml.move_id
					WHERE left(aa.code,2) = '10' AND am.state = 'posted' AND
					am.company_id = {company_id}
					AND (am.date BETWEEN '{date_start_year}' AND '{last_day}')
					group by aml.account_id)

					UNION ALL

					(SELECT 
					am.journal_id,
					am.vou_number as voucher,
					am.date as fecha,
					am.glosa,
					aml.account_id,
					coalesce(aml.debit) - coalesce(aml.credit) as amount,
					case when aml.cash_flow_id IS NOT NULL then acf.grupo
					when aml.cash_flow_id IS NULL AND coalesce(aml.debit) - coalesce(aml.credit) > 0 then '2'
					when aml.cash_flow_id IS NULL AND coalesce(aml.debit) - coalesce(aml.credit) < 0 then '3'
					end as grupo,
					case when aml.cash_flow_id IS NOT NULL then acf.code
					when aml.cash_flow_id IS NULL AND coalesce(aml.debit) - coalesce(aml.credit) > 0 then '998'
					when aml.cash_flow_id IS NULL AND coalesce(aml.debit) - coalesce(aml.credit) < 0 then '999'
					end as code,
					case when aml.cash_flow_id IS NOT NULL then acf.code||'-'||acf.name
					when aml.cash_flow_id IS NULL AND coalesce(aml.debit) - coalesce(aml.credit) > 0 then '998-INGRESOS NO DEFINIDOS'
					when aml.cash_flow_id IS NULL AND coalesce(aml.debit) - coalesce(aml.credit) < 0 then '999-EGRESOS NO DEFINIDOS'
					end as concepto
					FROM account_move_line aml
					LEFT JOIN account_account aa ON aa.id = aml.account_id
					LEFT JOIN account_cash_flow acf ON acf.id = aml.cash_flow_id
					LEFT JOIN account_move am ON am.id = aml.move_id
					WHERE left(aa.code,2) = '10' AND am.state = 'posted' AND
					am.company_id = {company_id} AND  am.is_opening_close <> TRUE
					AND (am.date BETWEEN '{date_from}' AND '{date_to}') )
					
					)T
					ORDER BY T.grupo,T.code
			""".format(user_id = self.env.uid,
				date_start_year = self.fiscal_year_id.date_from.strftime('%Y/%m/%d') if self.show_by == "date" else self.period_from_id.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				last_day = (self.date_from - timedelta(days=1)).strftime('%Y/%m/%d') if self.show_by == "date" else (self.period_from_id.date_start - timedelta(days=1)).strftime('%Y/%m/%d'),
				company_id = self.company_id.id,
				date_from = self.date_from.strftime('%Y/%m/%d') if self.show_by == "date" else self.period_from_id.date_start.strftime('%Y/%m/%d'),
				date_to = self.date_to.strftime('%Y/%m/%d') if self.show_by == "date" else self.period_to_id.date_end.strftime('%Y/%m/%d'))

		else:
			sql = """
				SELECT 
				T.journal_id,
				T.voucher,
				T.fecha,
				T.glosa,
				T.account_id,
				T.amount,
				CASE WHEN T.grupo = '1' THEN '1-SALDO INICIAL'
				WHEN T.grupo = '2' THEN '2-INGRESO'
				WHEN T.grupo = '3' THEN '3-EGRESO'
				WHEN T.grupo = '4' THEN '4-FINANCIAMIENTO' END AS grupo,
				T.concepto,
				{user_id} as user_id FROM
				(

				(SELECT 
				null as journal_id,
				null as voucher,
				'{date_from}' as fecha,
				'SALDO INICIAL' as glosa,
				aml.account_id,
				sum(coalesce(aml.debit) - coalesce(aml.credit)) as amount,
				'1' as grupo,
				'000' as code,
				'000-SALDO INICIAL' as concepto
				FROM account_move_line aml
				LEFT JOIN account_account aa ON aa.id = aml.account_id
				LEFT JOIN account_move am ON am.id = aml.move_id
				WHERE left(aa.code,2) = '10' AND am.state = 'posted' AND
				am.company_id = {company_id}
				AND (am.date BETWEEN '{date_start_year}' AND '{last_day}')
				group by aml.account_id)
				
				UNION ALL 

				(SELECT 
				am.journal_id,
				am.vou_number as voucher,
				am.date as fecha,
				am.glosa,
				aml.account_id,
				(coalesce(aml.debit) - coalesce(aml.credit))*-1 as amount,

				case when aa.account_cash_flow_id IS NOT NULL then acf.grupo
				when aa.account_cash_flow_id IS NULL AND (coalesce(aml.debit) - coalesce(aml.credit))*-1 > 0 then '2'
				when aa.account_cash_flow_id IS NULL AND (coalesce(aml.debit) - coalesce(aml.credit))*-1 < 0 then '3'
				end as grupo,
				case when aa.account_cash_flow_id IS NOT NULL then acf.code
				when aa.account_cash_flow_id IS NULL AND (coalesce(aml.debit) - coalesce(aml.credit))*-1 > 0 then '998'
				when aa.account_cash_flow_id IS NULL AND (coalesce(aml.debit) - coalesce(aml.credit))*-1 < 0 then '999'
				end as code,
				case when aa.account_cash_flow_id IS NOT NULL then acf.code||'-'||acf.name
				when aa.account_cash_flow_id IS NULL AND (coalesce(aml.debit) - coalesce(aml.credit))*-1 > 0 then '998-INGRESOS NO DEFINIDOS'
				when aa.account_cash_flow_id IS NULL AND (coalesce(aml.debit) - coalesce(aml.credit))*-1 < 0 then '999-EGRESOS NO DEFINIDOS'
				end as concepto
				FROM account_move_line aml
				LEFT JOIN account_account aa ON aa.id = aml.account_id
				LEFT JOIN account_cash_flow acf ON acf.id = aa.account_cash_flow_id
				LEFT JOIN account_move am ON am.id = aml.move_id
				WHERE left(aa.code,2) <> '10' AND aa.account_cash_flow_id IS NOT NULL AND aml.move_id in (
				SELECT
				DISTINCT ON (aml.move_id) move_id
				FROM account_move_line aml
				LEFT JOIN account_account aa ON aa.id = aml.account_id
				LEFT JOIN account_move am ON am.id = aml.move_id
				WHERE am.state = 'posted' AND am.company_id = {company_id} AND  am.is_opening_close <> TRUE 
				AND (am.date BETWEEN '{date_from}' AND '{date_to}')
				AND left(aa.code,2) = '10'))
				
				)T
				ORDER BY T.grupo,T.code
			""".format(user_id = self.env.uid,
				date_start_year = self.fiscal_year_id.date_from.strftime('%Y/%m/%d') if self.show_by == "date" else self.period_from_id.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				last_day = (self.date_from - timedelta(days=1)).strftime('%Y/%m/%d') if self.show_by == "date" else (self.period_from_id.date_start - timedelta(days=1)).strftime('%Y/%m/%d'),
				company_id = self.company_id.id,
				date_from = self.date_from.strftime('%Y/%m/%d') if self.show_by == "date" else self.period_from_id.date_start.strftime('%Y/%m/%d'),
				date_to = self.date_to.strftime('%Y/%m/%d') if self.show_by == "date" else self.period_to_id.date_end.strftime('%Y/%m/%d'))
		
		return sql

	def validate_dates(self):
		if self.show_by == "date":
			# Check if both dates are in the same year
			if self.date_from.year != int(self.fiscal_year_id.name) or self.date_to.year != int(self.fiscal_year_id.name):
				raise UserError(u"Las fechas no pertenecen al ejercicio escogido.")
			# Check if start date is not after end date
			if self.date_from and self.date_to:
				
				if self.date_to < self.date_from:
					raise UserError(u"La fecha final no puede ser menor a la fecha inicial.")
				#raise UserError(u'entra3')
				# Check if the difference between dates is at most 31 days
				if (self.date_to - self.date_from).days > 31:
					raise UserError(u"La diferencia entre ambas fechas no puede exceder los 31 días.")




