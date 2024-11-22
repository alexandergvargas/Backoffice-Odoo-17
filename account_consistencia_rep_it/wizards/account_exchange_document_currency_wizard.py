# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountExchangeDocumentCurrencyWizard(models.TransientModel):
	_name = 'account.exchange.document.currency.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

	def get_fiscal_year(self):
		today = fields.Date.context_today(self)
		fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
		if not fiscal_year:
			raise UserError(u'No existe un año fiscal con el año actual.')
		else:
			return fiscal_year.id

	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',default=lambda self:self.get_fiscal_year(),required=True)
	period = fields.Many2one('account.period',string=u'Periodo',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en',default='pantalla')

	def get_report(self):
		self.env.cr.execute("""
			DROP VIEW IF EXISTS account_exchange_document_currency_view CASCADE;
			CREATE OR REPLACE view account_exchange_document_currency_view as ("""+self._get_sql_report(self.fiscal_year_id.name,self.period,self.company_id.id)+""")""")
			
		if self.type_show == 'pantalla':
			return {
				'name': 'Diferencia Documentos Pagados',
				'type': 'ir.actions.act_window',
				'res_model': 'account.exchange.document.currency.view',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Diferencia_ME_Documento.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########DIFERENCIA ME DOCUMENTO############
		worksheet = workbook.add_worksheet("DIFERENCIA DOCUMENTOS PAGADOS")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','CUENTA','PARTNER','TD','NRO COMP.','DEBE','HABER','SALDO MN','SALDO ME','TC','SALDO ACT','DIFERENCIA','CTA DIFERENCIA']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.exchange.document.currency.view'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,2,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,3,line.td_sunat if line.td_sunat else '',formats['especial1'])
			worksheet.write(x,4,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
			worksheet.write(x,5,line.debe if line.debe else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.haber if line.haber else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.saldomn if line.saldomn else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.saldome if line.saldome else '0.00',formats['numberdos'])
			worksheet.write(x,9,line.tc if line.tc else '0.0000',formats['numbercuatro'])
			worksheet.write(x,10,line.saldo_act if line.saldo_act else '0.00',formats['numberdos'])
			worksheet.write(x,11,line.diferencia if line.diferencia else '0.00',formats['numberdos'])
			worksheet.write(x,12,line.cuenta_diferencia if line.cuenta_diferencia else '',formats['especial1'])
			x += 1

		widths = [10,12,40,6,15,12,12,15,15,5,15,15,20]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Diferencia_ME_Documento.xlsx', 'rb')
		return self.env['popup.it'].get_file('Diferencia Documentos Pagados.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def _get_sql_report(self,fiscal_year,period,company_id):
		sql_partner_adjustment = ""
		partner_adjustment_id = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).partner_adjustment_id
		
		if partner_adjustment_id:
			sql_partner_adjustment = "AND vst.partner_id <> %d"%(partner_adjustment_id.id)

		sql = """SELECT 
				row_number() OVER () AS id,
				'%s' as periodo,
				aa.code as cuenta,
				rp.name as partner,
				vst.td_sunat,
				vst.nro_comprobante,
				vst.debe,
				vst.haber,
				vst.saldomn,
				vst.saldome,
				vst.tc,
				vst.saldo_act,
				vst.diferencia,
				aa2.code as cuenta_diferencia,
				vst.account_id,
				aa.currency_id,
				vst.partner_id,
				%d as period_id
				FROM get_saldos_me_documento_final('%s','%s',%d) vst
				LEFT JOIN account_account aa ON aa.id = vst.account_id
				LEFT JOIN account_account aa2 ON aa2.id = vst.difference_account_id
				LEFT JOIN res_partner rp ON rp.id = vst.partner_id
				WHERE vst.saldome = 0 
				%s
			""" % (period.code,
				period.id,
				fiscal_year,
				period.code,
				company_id,
				sql_partner_adjustment)

		return sql