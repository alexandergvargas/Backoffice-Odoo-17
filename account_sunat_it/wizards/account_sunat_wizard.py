# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from io import BytesIO
import re
import uuid

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4,letter
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import simpleSplit
import decimal


from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError

import codecs
import pprint

from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
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


from lxml import etree
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT

class AccountSunatWizard(models.TransientModel):
	_name = 'account.sunat.wizard'
	_description = 'Account Sunat Wizard'

	name = fields.Char()

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio')
	period_id = fields.Many2one('account.period',string='Periodo')
	number = fields.Char(string=u'Número')
	sire = fields.Boolean(default=False,string='En el periodo se uso SIRE')
	type_date =  fields.Selection([('date','Fecha Contable'),('invoice_date_due','Fecha de Vencimiento'),('payment_date','Fecha de Pago')],string=u'Mostrar en base a',default='payment_date')
	
	check_close_book= fields.Boolean('Cerrar Libro')
	#SOLO SIRVE PARA LOS ANEXOS DE INVENTARIOS Y BALANCES
	#_______________________________________________________________________________________________________________________________________________________________
	type_show_inventory_balance  =  fields.Selection([('excel','Excel'),('pdf','PDF')],default='pdf',string=u'Mostrar en', required=True) #|
	#_______________________________________________________________________________________________________________________________________________________________

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def get_txt_81(self):
		return self._get_ple(1)

	def get_txt_82(self):
		return self._get_ple(2)

	def get_txt_141(self):
		return self._get_ple(3)

	def get_txt_diario(self):
		return self._get_ple(4)

	def get_txt_plan_c(self):
		return self._get_ple(6)

	def get_txt_mayor(self):
		return self._get_ple(5)

	def get_txt_caja(self):
		return self._get_ple(8)

	def get_txt_banco(self):
		return self._get_ple(9)
	
	def _get_ple(self,type):
		ruc = self.company_id.partner_id.vat
		mond = self.company_id.currency_id.name

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		if not mond:
			raise UserError('No configuro la moneda de su Compañia.')

		#LE + RUC + AÑO(YYYY) + MES(MM) + DIA(00) 
		name_doc = "LE"+ruc+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month))+"00"
		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(type,self.period_id,self.company_id.id,x_sire=self.sire)
		ReportBase = self.env['report.base']
		res = ReportBase.get_file_sql_export(sql_ple,'|')
		
		# IDENTIFICADOR DEL LIBRO

		name_doc += nomenclatura

		# CODIGO DE OPORTUNIDAD DE PRESENTACION DEL EEFF (00) +
		# INDICADOR DE OPERACIONES (1) +
		# INDICADOR DE CONTENIDO Con informacion(1), Sin informacion(0) +
		# INDICADOR DE MONEDA UTILIZADA Nuevos Soles(1), US Dolares(2) +
		# INDICADOR DE LIBRO ELECTRONICO GENERADO POR EL PLE (1)
		if self.check_close_book:
			if type in [1,2,3]:			
				name_doc += "00"+"2"+("1" if len(res) > 0 else "0") + ("1" if mond == 'PEN' else "2") + "1.txt"
			else:
				name_doc += "00"+"1"+("1" if len(res) > 0 else "0") + ("1" if mond == 'PEN' else "2") + "1.txt"
		else:
			name_doc += "00"+"1"+("1" if len(res) > 0 else "0") + ("1" if mond == 'PEN' else "2") + "1.txt"
		if res:
			return self.env['popup.it'].get_file(name_doc,res)
		else:
			attachment = self.env['ir.attachment'].sudo().create({
				'name': str(name_doc),
				'type': 'binary',
				'datas': res,
				'store_fname': str(name_doc),
				'res_model': self._name,
				'res_id': self.id,
			})

			return {
				'type': 'ir.actions.act_url',
				'url': '/web/content/%s/%s?download=true' % (attachment.id, str(name_doc)),
				'target': 'new',
			}
	
		

	def get_txt_balance(self):
		ruc = self.company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#LE + RUC + AÑO(YYYY) + MES(MM) + DIA(00) 
		name_doc = self.number+str(ruc)+".txt"

		sql_ple = self.env['account.base.sunat'].sql_txt_balance(self.fiscal_year_id,self.company_id.id)
		ReportBase = self.env['report.base']
		res = ReportBase.get_file_sql_export(sql_ple,'|')
		if res:
			return self.env['popup.it'].get_file(name_doc,res)
		else:
			attachment = self.env['ir.attachment'].sudo().create({
				'name': str(name_doc),
				'type': 'binary',
				'datas': res,
				'store_fname': str(name_doc),
				'res_model': self._name,
				'res_id': self.id,
			})

			return {
				'type': 'ir.actions.act_url',
				'url': '/web/content/%s/%s?download=true' % (attachment.id, str(name_doc)),
				'target': 'new',
			}

	def get_txt_servidores(self):
		return self.get_plame(1)
	
	def get_txt_recibos(self):	
		return self.get_plame(2)
	
	def get_plame(self,type):

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		ruc = self.company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		name_doc = "0601"+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_end.month))+str(ruc)

		ctxt = ""
		separator = "|"

		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(7,self.period_id,self.company_id.id,honorary_type_date=self.type_date)

		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()
		
		if type == 1:
			name_doc += ".ps4"
			for recibo in dicc:
				ctxt += str(recibo['tdp']) + separator
				ctxt += str(recibo['docp']) + separator
				ctxt += str(recibo['apellido_p']) + separator
				ctxt += str(recibo['apellido_m']) + separator
				ctxt += str(recibo['namep']) + separator
				ctxt += str(recibo['is_not_home']) + separator
				ctxt += str(recibo['c_d_imp']) if recibo['c_d_imp'] else '0'
				ctxt += separator
				ctxt = ctxt + """\r\n"""
		else:
			name_doc += ".4ta"
			for recibo in dicc:
				ctxt += str(recibo['tdp']) + separator
				ctxt += str(recibo['docp']) + separator
				ctxt += str(recibo['honorary_type']) + separator
				ctxt += str(recibo['serie']) if recibo['serie'] else ''
				ctxt += separator
				ctxt += str(recibo['numero']) if recibo['numero'] else ''
				ctxt += separator
				ctxt += str(recibo['renta']) if recibo['renta'] else '0'
				ctxt += separator
				ctxt += str(recibo['fecha_e'].strftime('%d/%m/%Y')) + separator
				ctxt += str(recibo['fecha_p'].strftime('%d/%m/%Y')) if recibo['fecha_p'] else ''
				ctxt += separator
				ctxt += '0' if recibo['retencion'] == 0 else '1'
				ctxt += separator
				ctxt += '' + separator + '' + separator
				ctxt = ctxt + """\r\n"""

		import importlib
		import sys
		importlib.reload(sys)

		return self.env['popup.it'].get_file(name_doc,base64.encodebytes(b''+ctxt.encode("utf-8")))

	def get_pdt_pi(self):
		return self.get_txt_pdt(1,self.company_id,self.period_id.date_start,self.period_id.date_end)

	def get_pdt_p(self):
		return self.get_txt_pdt(0,self.company_id,self.period_id.date_start,self.period_id.date_end)
	
	def get_txt_pdt(self,type,company_id,date_start,date_end):
		type_doc = self.env['account.main.parameter'].search([('company_id','=',company_id.id)],limit=1).dt_perception

		if not type_doc:
			raise UserError(u'No existe un Tipo de Documento para Percepciones configurado en Parametros Principales de Contabilidad para su Compañía')

		ruc = company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#0621 + RUC + AÑO(YYYY) + MES(MM) + PI o P
		name_doc = "0621"+str(ruc)+str(date_start.year)+str('{:02d}'.format(date_start.month))

		if type == 1:
			name_doc += "PI.txt"
		if type == 0:
			name_doc += "P.txt"

		sql_query = self.env['account.base.sunat']._get_sql_txt_percepciones(type,date_start,date_end,company_id.id,type_doc.code)
		ReportBase = self.env['report.base']
		res = ReportBase.get_file_sql_export(sql_query,'|')

		return self.env['popup.it'].get_file(name_doc,res)

	def get_daot_purchase(self):
		return self.get_daot(self.get_sql_daot_purchase(),"Costos")

	def get_daot_sale(self):
		return self.get_daot(self.get_sql_daot_sale(),"Ingresos")

	def get_sql_daot_purchase(self):
		uit_value = self.env['account.fiscal.year.uit'].search([('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1).uit
		if not uit_value:
			raise UserError (u"No esta configurado el UIT en la Tabla UIT de Contabilidad")
		sql = """
			SELECT 
			ROW_NUMBER() OVER() AS field1,
			litc.l10n_pe_vat_code AS field2,
			rpc.vat AS field3,
			'%s' AS field4,
			CASE
				WHEN rp.is_company = TRUE THEN '02'
				ELSE '01'
			END AS field5,
			lit.l10n_pe_vat_code AS field6,
			rp.vat AS field7,
			T1.montoc AS field8,
			CASE
				WHEN rp.is_company <> TRUE THEN rp.last_name
			END AS field9,
			CASE
				WHEN rp.is_company <> TRUE THEN rp.m_last_name
			END AS field10,
			CASE
				WHEN rp.is_company <> TRUE THEN split_part(rp.name_p, ' ', 1)
			END AS field11,
			CASE
				WHEN rp.is_company <> TRUE AND split_part(rp.name_p, ' ', 2) <> '' THEN split_part(rp.name_p, ' ', 2)
			END AS field12,
			CASE
				WHEN rp.is_company = TRUE THEN rp.name
			END AS field13,
			NULL AS field14
			FROM (select a1.partner_id,round(sum(a1.base1+a1.base2+a1.base3+a1.cng),0) as montoc, a1.company from vst_compras_1_1 a1
			left join res_partner a2 on a2.id=a1.partner_id
			where a2.is_not_home<>TRUE and a1.td<>'02' and a1.company = %s and left(a1.periodo,4) = '%s'
			group by a1.partner_id, a1.company
			having round(sum(a1.base1+a1.base2+a1.base3+a1.cng),0) >= %s)T1
			LEFT JOIN res_partner rp ON rp.id = T1.partner_id
			LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
			LEFT JOIN res_company rc ON rc.id = T1.company
			LEFT JOIN res_partner rpc ON rpc.id = rc.partner_id
			LEFT JOIN l10n_latam_identification_type litc ON litc.id = rpc.l10n_latam_identification_type_id
		""" % (self.exercise.name,
				str(self.company_id.id),
				self.exercise.name,
				str(uit_value*2))

		return sql

	def get_sql_daot_sale(self):
		param = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		uit_value = self.env['account.fiscal.year.uit'].search([('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1).uit
		if not uit_value:
			raise UserError (u"No esta configurado el UIT en la Tabla UIT de Contabilidad")
		if not param.sale_ticket_partner:
			raise UserError(u'No existe Partner para Boleta de Ventas configurado en Parametros Principales de Contabilidad para esta Compañía')

		sql = """
			SELECT 
			ROW_NUMBER() OVER() AS field1,
			litc.l10n_pe_vat_code AS field2,
			rpc.vat AS field3,
			'%s' AS field4,
			CASE
				WHEN rp.is_company = TRUE THEN '02'
				ELSE '01'
			END AS field5,
			lit.l10n_pe_vat_code AS field6,
			rp.vat AS field7,
			T1.montoc AS field8,
			CASE
				WHEN rp.is_company <> TRUE THEN rp.last_name
			END AS field9,
			CASE
				WHEN rp.is_company <> TRUE THEN rp.m_last_name
			END AS field10,
			CASE
				WHEN rp.is_company <> TRUE THEN split_part(rp.name_p, ' ', 1)
			END AS field11,
			CASE
				WHEN rp.is_company <> TRUE AND split_part(rp.name_p, ' ', 2) <> '' THEN split_part(rp.name_p, ' ', 2)
			END AS field12,
			CASE
				WHEN rp.is_company = TRUE THEN rp.name
			END AS field13,
			NULL AS field14
			FROM (select am.partner_id,round(sum(a1.venta_g+a1.inaf+a1.exo),0) as montoc,a1.company from vst_ventas_1_1 a1
			LEFT JOIN account_move am ON am.id = a1.am_id
			LEFT JOIN res_partner a2 on a2.id=am.partner_id
			where a2.is_not_home<>TRUE and a1.td<>'02' and a1.company = %s and left(a1.periodo,4) = '%s' and am.partner_id <> %s
			group by am.partner_id,a1.company
			having round(sum(a1.venta_g+a1.inaf+a1.exo),0) >= %s)T1
			LEFT JOIN res_partner rp ON rp.id = T1.partner_id
			LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
			LEFT JOIN res_company rc ON rc.id = T1.company
			LEFT JOIN res_partner rpc ON rpc.id = rc.partner_id
			LEFT JOIN l10n_latam_identification_type litc ON litc.id = rpc.l10n_latam_identification_type_id
		""" % (self.exercise.name,
				str(self.company_id.id),
				self.exercise.name,
				str(param.sale_ticket_partner.id),
				str(uit_value*2))

		return sql

	def get_daot(self,sql,nomenclatura):
		name_doc = nomenclatura+".txt"
		self.env.cr.execute(sql)
		sql = "COPY (%s) TO STDOUT WITH %s" % (sql, "CSV DELIMITER '|'")
		rollback_name = self._create_savepoint()

		try:
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
		finally:
			self._rollback_savepoint(rollback_name)
		#res = res.encode('utf-8')
		if res:
			return self.env['popup.it'].get_file(name_doc,res)
		else:
			attachment = self.env['ir.attachment'].sudo().create({
				'name': str(name_doc),
				'type': 'binary',
				'datas': res,
				'store_fname': str(name_doc),
				'res_model': self._name,
				'res_id': self.id,
			})

			return {
				'type': 'ir.actions.act_url',
				'url': '/web/content/%s/%s?download=true' % (attachment.id, str(name_doc)),
				'target': 'new',
			}

	def get_pdb_currency_rate(self):
		ruc = self.company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#RUC + .tc
		name_doc = str(ruc)+".tc"
		sql = self.env['account.base.sunat'].get_sql_pdb_currency_rate(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		
		dicc = self.env.cr.dictfetchall()
		ctxt = ""
		separator = "|"
		
		for elem in dicc:
			for i in range(1,4):
				ctxt += str(elem['field%s'%(i)]) if elem['field%s'%(i)] else ''
				ctxt += separator
			ctxt = ctxt + """\r\n"""

		import importlib
		import sys
		importlib.reload(sys)

		return self.env['popup.it'].get_file(name_doc,base64.encodebytes(b''+ctxt.encode("utf-8")))

	def get_pdb_purchase(self):
		ruc = self.company_id.partner_id.vat
		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#C + RUC + AÑO(YYYY) + MES(MM) + .txt
		name_doc = "C"+str(ruc)+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month))+".txt"
		sql = self.env['account.base.sunat'].get_sql_pdb_purchase(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)

		dicc = self.env.cr.dictfetchall()
		ctxt = ""
		separator = "|"
		
		for elem in dicc:
			for i in range(1,31):
				ctxt += str(elem['field%s'%(i)]) if elem['field%s'%(i)] else ''
				ctxt += separator
			ctxt = ctxt + """\r\n"""

		import importlib
		import sys
		importlib.reload(sys)

		return self.env['popup.it'].get_file(name_doc,base64.encodebytes(b''+ctxt.encode("utf-8")))

	def get_pdb_sale(self):
		ruc = self.company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#V + RUC + AÑO(YYYY) + MES(MM) + .txt
		name_doc = "V"+str(ruc)+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month))+".txt"
		sql = self.env['account.base.sunat'].get_sql_pdb_sale(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		
		dicc = self.env.cr.dictfetchall()
		ctxt = ""
		separator = "|"
		
		for elem in dicc:
			for i in range(1,31):
				ctxt += str(elem['field%s'%(i)]) if elem['field%s'%(i)] else ''
				ctxt += separator
			ctxt = ctxt + """\r\n"""

		import importlib
		import sys
		importlib.reload(sys)

		return self.env['popup.it'].get_file(name_doc,base64.encodebytes(b''+ctxt.encode("utf-8")))

	def get_pdb_payment(self):
		ruc = self.company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#F + RUC + AÑO(YYYY) + MES(MM) + .txt
		name_doc = "F"+str(ruc)+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month))+".txt"
		sql = self.env['account.base.sunat'].get_sql_pdb_payment(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		
		dicc = self.env.cr.dictfetchall()
		ctxt = ""
		separator = "|"
		
		for elem in dicc:
			for i in range(1,13):
				ctxt += str(elem['field%s'%(i)]) if elem['field%s'%(i)] else ''
				ctxt += separator
			ctxt = ctxt + """\r\n"""

		import importlib
		import sys
		importlib.reload(sys)

		return self.env['popup.it'].get_file(name_doc,base64.encodebytes(b''+ctxt.encode("utf-8")))

	def get_excel_81(self):
		ReportBase = self.env['report.base']
		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(1,self.period_id,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9',
					'CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21','CAMPO 22','CAMPO 23',
					'CAMPO 24','CAMPO 25','CAMPO 26','CAMPO 27','CAMPO 28','CAMPO 29','CAMPO 30','CAMPO 31','CAMPO 32','CAMPO 33','CAMPO 34',
					'CAMPO 35','CAMPO 36','CAMPO 37','CAMPO 38','CAMPO 39','CAMPO 40','CAMPO 41','CAMPO 42'])
		return self.env['popup.it'].get_file('Registro de Compras 81.xlsx',workbook)
			
	def get_excel_82(self):
		ReportBase = self.env['report.base']
		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(2,self.period_id,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8',
					'CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21','CAMPO 22','CAMPO 23',
					'CAMPO 24','CAMPO 25','CAMPO 26','CAMPO 27','CAMPO 28','CAMPO 29','CAMPO 30','CAMPO 31','CAMPO 32','CAMPO 33','CAMPO 34',
					'CAMPO 35','CAMPO 36'])
		return self.env['popup.it'].get_file('Registro de Compras 82.xlsx',workbook)
	
	def get_excel_141(self):
		ReportBase = self.env['report.base']
		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(3,self.period_id,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8',
					'CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21','CAMPO 22','CAMPO 23',
					'CAMPO 24','CAMPO 25','CAMPO 26','CAMPO 27','CAMPO 28','CAMPO 29','CAMPO 30','CAMPO 31','CAMPO 32','CAMPO 33','CAMPO 34','CAMPO 35'])
		return self.env['popup.it'].get_file('Registro de Ventas 141.xlsx',workbook)

	def get_excel_diario(self):
		ReportBase = self.env['report.base']
		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(4,self.period_id,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9',
		'CAMPO 10','CAMPO 11','CAMPO 12','CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21','CAMPO 22',
		'CAMPO 23','CAMPO 24','CAMPO 25','CAMPO 26'])
		return self.env['popup.it'].get_file('Ple Libro Diario.xlsx',workbook)

	def get_excel_plan_c(self):
		ReportBase = self.env['report.base']
		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(6,self.period_id,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8'])
		return self.env['popup.it'].get_file('Ple Plan Contable.xlsx',workbook)

	def get_excel_mayor(self):
		ReportBase = self.env['report.base']
		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(5,self.period_id,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9',
		'CAMPO 10','CAMPO 11','CAMPO 12','CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21','CAMPO 22',
		'CAMPO 23','CAMPO 24','CAMPO 25','CAMPO 26'])
		return self.env['popup.it'].get_file('Ple Mayor.xlsx',workbook)
		
	def get_excel_servidores(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Servidores.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(7,self.period_id,self.company_id.id,honorary_type_date=self.type_date)

		worksheet = workbook.add_worksheet("Servidores")
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['tdp'] if line['tdp'] else '',formats['especial1'])
			worksheet.write(x,1,line['docp'] if line['docp'] else '',formats['especial1'])
			worksheet.write(x,2,line['apellido_p'] if line['apellido_p'] else '',formats['especial1'])
			worksheet.write(x,3,line['apellido_m'] if line['apellido_m'] else '',formats['especial1'])
			worksheet.write(x,4,line['namep'] if line['namep'] else '',formats['especial1'])
			worksheet.write(x,5,line['is_not_home'] if line['is_not_home'] else '',formats['especial1'])
			worksheet.write(x,6,line['c_d_imp'] if line['c_d_imp'] else '0',formats['especial1'])
			x+=1

		widths = [9,12,26,26,52,10,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Servidores.xlsx', 'rb')
		return self.env['popup.it'].get_file('Servidores.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def get_excel_recibos(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Recibos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		date_new_format = workbook.add_format({'num_format':'dd-mm-yyyy'})
		date_new_format.set_align('justify')
		date_new_format.set_align('vcenter')
		date_new_format.set_font_size(10)
		date_new_format.set_font_name('Times New Roman')
		formats['date_new_format'] = date_new_format

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(7,self.period_id,self.company_id.id,honorary_type_date=self.type_date)

		worksheet = workbook.add_worksheet("Recibos")
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['tdp'] if line['tdp'] else '',formats['especial1'])
			worksheet.write(x,1,line['docp'] if line['docp'] else '',formats['especial1'])
			worksheet.write(x,2,line['honorary_type'] if line['honorary_type'] else '',formats['especial1'])
			worksheet.write(x,3,line['serie'] if line['serie'] else '',formats['especial1'])
			worksheet.write(x,4,line['numero'] if line['numero'] else '',formats['especial1'])
			worksheet.write(x,5,line['renta'] if line['renta'] else '0.00',formats['numberdos'])
			worksheet.write(x,6,line['fecha_e'] if line['fecha_e'] else '',formats['date_new_format'])
			worksheet.write(x,7,line['fecha_p'] if line['fecha_p'] else '',formats['date_new_format'])
			worksheet.write(x,8,'0' if line['retencion'] == 0 else '1',formats['especial1'])
			worksheet.write(x,9,'',formats['especial1'])
			worksheet.write(x,10,'',formats['especial1'])
			x+=1

		widths = [9,12,12,12,12,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Recibos.xlsx', 'rb')
		return self.env['popup.it'].get_file('Recibos.xlsx',base64.encodebytes(b''.join(f.readlines())))
	
	def get_pdf_libro_diario(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal-12, "*** LIBRO DIARIO DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-10,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-20, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-30, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=6><b>N° CORREL. ASNTO COD. UNI. DE OPER.</b></font>",style), 
				Paragraph("<font size=6><b>FECHA DE LA OPERACION</b></font>",style), 
				Paragraph("<font size=6><b>GLOSA O DESCRIPCION DE LA OPERACION</b></font>",style), 
				Paragraph("<font size=6><b>CUENTA CONTABLE ASOCIADA A LA OPERACION</b></font>",style), 
				'', 
				Paragraph("<font size=6><b>MOVIMIENTO</b></font>",style), 
				''],
				['','','',Paragraph("<font size=6><b>CODIGO</b></font>",style),
				Paragraph("<font size=6><b>DENOMINACION</b></font>",style),
				Paragraph("<font size=6><b>DEBE</b></font>",style),
				Paragraph("<font size=6><b>HABER</b></font>",style)]]
			t=Table(data,colWidths=size_widths, rowHeights=(20))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,1)),
				('SPAN',(1,0),(1,1)),
				('SPAN',(2,0),(2,1)),
				('SPAN',(3,0),(4,0)),
				('SPAN',(5,0),(6,0)),
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-85)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-95
			else:
				return pagina,posactual-valor

		width ,height  = A4  # 595 , 842
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "libro_diario_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= A4 )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [60,45,130,40,140,60,60]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-43

		c.setFont("Helvetica", 8)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_diariog(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		libro = ''
		voucher = ''
		sum_debe = 0
		sum_haber = 0

		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica-Bold", 8)
			if cont == 0:
				libro = i['libro']
				voucher = i['voucher']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,libro)
				pos_inicial -= 15

			
			if libro != i['libro']:
				c.line(440,pos_inicial+3,565,pos_inicial+3)
				c.drawString( 350 ,pos_inicial-10,'TOTAL:')
				c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
				c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
				sum_debe = 0
				sum_haber = 0
				pos_inicial -= 25

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				
				libro = i['libro']
				voucher = i['voucher']
				c.drawString( first_pos+2 ,pos_inicial,libro)
				pos_inicial -= 15

			if voucher != i['voucher']:
				c.line(440,pos_inicial+3,565,pos_inicial+3)
				c.drawString( 350 ,pos_inicial-10,'TOTAL:')
				c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
				c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
				sum_debe = 0
				sum_haber = 0
				pos_inicial -= 15

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

				voucher = i['voucher']
				pos_inicial -= 10


			c.setFont("Helvetica", 6)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['voucher'] if i['voucher'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha'] if i['fecha'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['glosa'] if i['glosa'] else '',130) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['cuenta'] if i['cuenta'] else '',50) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['des'] if i['des'] else '',150) )
			first_pos += size_widths[4]

			c.drawRightString( first_pos+60 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])) )
			sum_debe += i['debe']
			first_pos += size_widths[5]

			c.drawRightString( first_pos+60 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])))
			sum_haber += i['haber']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 8)
		c.line(440,pos_inicial+3,565,pos_inicial+3)
		c.drawString( 350 ,pos_inicial-10,'TOTAL:')
		c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
		c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DIARIO '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_libro_mayor(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal-12, "*** LIBRO MAYOR DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-10,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-20, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-30, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=6><b>LIBRO</b></font>",style), 
				Paragraph("<font size=6><b>TD</b></font>",style), 
				Paragraph("<font size=6><b>NUMERO</b></font>",style), 
				Paragraph("<font size=6><b>NRO CORRELATIVO</b></font>",style), 
				Paragraph("<font size=6><b>FECHA</b></font>",style), 
				Paragraph("<font size=6><b>DESCRIPCION O GLOSA</b></font>",style),
				Paragraph("<font size=6><b>SALDOS Y MOVIMIENTOS</b></font>",style), 
				''],
				['','','','','','',
				Paragraph("<font size=6><b>DEUDOR</b></font>",style),
				Paragraph("<font size=6><b>ACREEDOR</b></font>",style)]]
			t=Table(data,colWidths=size_widths, rowHeights=(20))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,1)),
				('SPAN',(1,0),(1,1)),
				('SPAN',(2,0),(2,1)),
				('SPAN',(3,0),(3,1)),
				('SPAN',(4,0),(4,1)),
				('SPAN',(5,0),(5,1)),
				('SPAN',(6,0),(7,0)),
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-85)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-95
			else:
				return pagina,posactual-valor

		width ,height  = A4  # 595 , 842
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "libro_mayor_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= A4 )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [60,35,60,70,50,140,60,60]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-43

		c.setFont("Helvetica", 8)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_mayor(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		cuenta = ''
		sum_debe = 0
		sum_haber = 0
		saldo_debe = 0
		saldo_haber = 0

		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica-Bold", 8)
			if cont == 0:
				cuenta = i['cuenta']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cod. Cuenta: ' + cuenta + '' + i['name_cuenta'])
				pos_inicial -= 15

			if cuenta != i['cuenta']:
				c.line(440,pos_inicial+3,565,pos_inicial+3)
				c.drawString( 350 ,pos_inicial-10,'TOTAL CUENTA:')
				c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
				c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
				pos_inicial -= 10

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 8)

				c.line(440,pos_inicial+3,565,pos_inicial+3)
				c.drawString( 350 ,pos_inicial-10,'SALDO FINAL:')
				saldo_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
				saldo_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)

				c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_debe)) )
				c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_haber)))
				pos_inicial -= 20

				c.line(440,pos_inicial+3,565,pos_inicial+3)

				sum_debe = 0
				sum_haber = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 8)

				cuenta = i['cuenta']
				c.drawString( first_pos+2 ,pos_inicial,'Cod. Cuenta: ' + cuenta if cuenta else "" + '' + i['name_cuenta'] if i['name_cuenta'] else "")
				pos_inicial -= 15


			c.setFont("Helvetica", 6)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['libro'] if i['libro'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',50) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['voucher'] if i['voucher'] else '',50) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha'] if i['fecha'] else '',50) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['glosa'] if i['glosa'] else '',150) )
			first_pos += size_widths[5]

			c.drawRightString( first_pos+60 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])) )
			sum_debe += i['debe']
			first_pos += size_widths[6]

			c.drawRightString( first_pos+60 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])))
			sum_haber += i['haber']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 8)
		c.line(440,pos_inicial+3,565,pos_inicial+3)
		c.drawString( 350 ,pos_inicial-10,'TOTAL CUENTA:')
		c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
		c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 8)

		c.line(440,pos_inicial+3,565,pos_inicial+3)
		c.drawString( 350 ,pos_inicial-10,'SALDO FINAL:')
		saldo_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
		saldo_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)

		c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_debe)) )
		c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_haber)))
		pos_inicial -= 20

		c.line(440,pos_inicial+3,565,pos_inicial+3)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO MAYOR '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_compras(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal-12, "*** REGISTRO DE COMPRAS DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-10,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-20, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-30, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 4
			style.alignment= 1

			data= [[Paragraph("<font size=4.5><b>N° Vou.</b></font>",style), 
				Paragraph("<font size=4.5><b>F. Emision</b></font>",style), 
				Paragraph("<font size=4.5><b>F. Venc</b></font>",style), 
				Paragraph("<font size=4.5><b>Comprobante de pago</b></font>",style), 
				'', 
				'',
				Paragraph("<font size=4.5><b>Nº Comprobante Pago</b></font>",style), 
				Paragraph("<font size=4.5><b>Informacion del Proveedor</b></font>",style),
				'','',
				Paragraph("<font size=4.5><b>Adq. Grav. dest. a Oper. Grav. y/o Exp.</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Adq. Grav. dest. a Oper. Grav. y/o Exp. y a Oper.</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Adq. Grav. dest. a Oper. No Gravadas</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Valor de Adq no Gravadas</b></font>",style),
				Paragraph("<font size=4.5><b>I.S.C.</b></font>",style),
				Paragraph("<font size=4.5><b>ICBPER</b></font>",style),
				Paragraph("<font size=4.5><b>Otros Tributos</b></font>",style),
				Paragraph("<font size=4.5><b>Importe Total</b></font>",style),
				Paragraph("<font size=4.5><b>Nº Comp. de pago emitido por sujeto no domiciliado </b></font>",style),
				Paragraph("<font size=4.5><b>Constancia de Deposito de Detracción</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>T.C.</b></font>",style),
				Paragraph("<font size=4.5><b>Referencia del Documento</b></font>",style),
				'','',''],
				['','','',
				Paragraph("<font size=4.5><b>T/D</b></font>",style),
				Paragraph("<font size=4.5><b>Serie</b></font>",style),
				Paragraph("<font size=4.5><b>Año de Emision DUA o DSI</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Doc. de Identidad</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Apellidos y nombres o Razon Social</b></font>",style),
				'','','','','','','','','','','','','','','',
				Paragraph("<font size=4.5><b>Fecha</b></font>",style),
				Paragraph("<font size=4.5><b>T/D</b></font>",style),
				Paragraph("<font size=4.5><b>Serie</b></font>",style),
				Paragraph("<font size=4.5><b>Numero Comprobante Doc Numero de pago</b></font>",style)],
				['','','','','','','',
				Paragraph("<font size=4.5><b>Doc</b></font>",style),
				Paragraph("<font size=4.5><b>Numero</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Base Imp.</b></font>",style),
				Paragraph("<font size=4.5><b>I.G.V.</b></font>",style),
				Paragraph("<font size=4.5><b>Base Imp.</b></font>",style),
				Paragraph("<font size=4.5><b>I.G.V.</b></font>",style),
				Paragraph("<font size=4.5><b>Base Imp.</b></font>",style),
				Paragraph("<font size=4.5><b>I.G.V.</b></font>",style),
				'','','','','','',
				Paragraph("<font size=4.5><b>Numero</b></font>",style),
				Paragraph("<font size=4.5><b>Fecha Emi.</b></font>",style),
				'','','','',''
				]]
			t=Table(data,colWidths=size_widths, rowHeights=(14))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,2)),
				('SPAN',(1,0),(1,2)),
				('SPAN',(2,0),(2,2)),
				('SPAN',(3,0),(5,0)),
				('SPAN',(3,1),(3,2)),
				('SPAN',(4,1),(4,2)),
				('SPAN',(5,1),(5,2)),
				('SPAN',(6,0),(6,2)),
				('SPAN',(7,0),(9,0)),
				('SPAN',(7,1),(8,1)),
				('SPAN',(9,1),(9,2)),
				('SPAN',(10,0),(11,1)),
				('SPAN',(12,0),(13,1)),
				('SPAN',(14,0),(15,1)),
				('SPAN',(16,0),(16,2)),
				('SPAN',(17,0),(17,2)),
				('SPAN',(18,0),(18,2)),
				('SPAN',(19,0),(19,2)),
				('SPAN',(20,0),(20,2)),
				('SPAN',(21,0),(21,2)),
				('SPAN',(22,0),(23,1)),
				('SPAN',(24,0),(24,2)),
				('SPAN',(25,0),(28,0)),
				('SPAN',(25,1),(25,2)),
				('SPAN',(26,1),(26,2)),
				('SPAN',(27,1),(27,2)),
				('SPAN',(28,1),(28,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-112
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "compra_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [30,28,28,14,16,25,32,15,30,67,29,29,27,25,25,26,24,23,24,24,34,38,29,30,20,25,14,18,45]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-60

		c.setFont("Helvetica", 4)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat']._get_sql_vst_compras(self.period_id.date_start,self.period_id.date_end,self.company_id.id)

		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		td = ''
		base1, base2, base3, igv1, igv2, igv3, cng, isc, otros, icbper, total = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
		total_base1, total_base2, total_base3, total_igv1, total_igv2, total_igv3, total_cng, total_isc, total_icbper, total_otros, total_total = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica-Bold", 4)
			if cont == 0:
				td = i['td']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Tipo Doc.: ' + (td or '') )
				pos_inicial -= 10

			if td != i['td']:
				c.line(314,pos_inicial+3,598,pos_inicial+3)
				c.drawString( 270 ,pos_inicial-5,'TOTALES:')
				c.drawRightString( 342,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base1)) )
				c.drawRightString( 371 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv1)))
				c.drawRightString( 400 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base2)))
				c.drawRightString( 427 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv2)))
				c.drawRightString( 452 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base3)))
				c.drawRightString( 477 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv3)))
				c.drawRightString( 503 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % cng)))
				c.drawRightString( 527 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % isc)))
				c.drawRightString( 550 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % icbper)))
				c.drawRightString( 574 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % otros)))
				c.drawRightString( 598 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)))

				base1, base2, base3, igv1, igv2, igv3, cng, isc, otros, icbper, total = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 4)

				td = i['td']
				c.drawString( first_pos+2 ,pos_inicial,'Tipo Doc.: ' + (td or '') )
				pos_inicial -= 10


			c.setFont("Helvetica", 4)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['voucher'] if i['voucher'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_e'] if i['fecha_e'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_v'] if i['fecha_v'] else '',50) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td'] if i['td'] else '',50) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['serie'] if i['serie'] else '',50) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['anio'] if i['anio'] else '',50) )
			first_pos += size_widths[5]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['numero'] if i['numero'] else '',50) )
			first_pos += size_widths[6]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['tdp'] if i['tdp'] else '',50) )
			first_pos += size_widths[7]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['docp'] if i['docp'] else '',50) )
			first_pos += size_widths[8]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['namep'] if i['namep'] else '',130) )
			first_pos += size_widths[9]

			c.drawRightString( 342 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['base1'])) )
			base1 += i['base1']
			total_base1 += i['base1']
			first_pos += size_widths[10]

			c.drawRightString( 371 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['igv1'])) )
			igv1 += i['igv1']
			total_igv1 += i['igv1']
			first_pos += size_widths[11]

			c.drawRightString( 400 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['base2'])) )
			base2 += i['base2']
			total_base2 += i['base2']
			first_pos += size_widths[12]

			c.drawRightString( 427 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['igv2'])) )
			igv2 += i['igv2']
			total_igv2 += i['igv2']
			first_pos += size_widths[13]

			c.drawRightString( 452 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['base3'])) )
			base3 += i['base3']
			total_base3 += i['base3']
			first_pos += size_widths[14]

			c.drawRightString( 477 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['igv3'])) )
			igv3 += i['igv3']
			total_igv3 += i['igv3']
			first_pos += size_widths[15]

			c.drawRightString( 503 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['cng'])) )
			cng += i['cng']
			total_cng += i['cng']
			first_pos += size_widths[16]

			c.drawRightString( 527 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['isc'])) )
			isc += i['isc']
			total_isc += i['isc']
			first_pos += size_widths[17]

			c.drawRightString( 550 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['icbper'])) )
			icbper += i['icbper']
			total_icbper += i['icbper']
			first_pos += size_widths[18]

			c.drawRightString( 574 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['otros'])) )
			otros += i['otros']
			total_otros += i['otros']
			first_pos += size_widths[19]

			c.drawRightString( 598 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['total'])) )
			total += i['total']
			total_total += i['total']
			first_pos += size_widths[20]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_no_dom'] if i['nro_no_dom'] else '',50) )
			first_pos += size_widths[21]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['comp_det'] if i['comp_det'] else '',50) )
			first_pos += size_widths[22]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_det'] if i['fecha_det'] else '',50) )
			first_pos += size_widths[23]

			c.drawRightString( first_pos+18 ,pos_inicial,'{:,.4f}'.format(decimal.Decimal ("%0.4f" % i['currency_rate'])) )
			first_pos += size_widths[24]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['f_doc_m'] if i['f_doc_m'] else '',50) )
			first_pos += size_widths[25]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_doc_m'] if i['td_doc_m'] else '',50) )
			first_pos += size_widths[26]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['serie_m'] if i['serie_m'] else '',50) )
			first_pos += size_widths[27]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['numero_m'] if i['numero_m'] else '',50) )

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 4)
		c.line(314,pos_inicial+3,598,pos_inicial+3)
		c.drawString( 270 ,pos_inicial-5,'TOTALES:')
		c.drawRightString( 342 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base1)) )
		c.drawRightString( 371 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv1)))
		c.drawRightString( 400 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base2)))
		c.drawRightString( 427 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv2)))
		c.drawRightString( 452 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base3)))
		c.drawRightString( 477 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv3)))
		c.drawRightString( 503 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % cng)))
		c.drawRightString( 527 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % isc)))
		c.drawRightString( 550 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % icbper)))
		c.drawRightString( 574 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % otros)))
		c.drawRightString( 598 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)))
		
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 4)

		c.line(314,pos_inicial+3,598,pos_inicial+3)

		c.drawString( 270 ,pos_inicial-5,'TOTAL GENERAL:')
		c.drawRightString( 342 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_base1)) )
		c.drawRightString( 371 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_igv1)))
		c.drawRightString( 400 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_base2)))
		c.drawRightString( 427 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_igv2)))
		c.drawRightString( 452 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_base3)))
		c.drawRightString( 477 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_igv3)))
		c.drawRightString( 503 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_cng)))
		c.drawRightString( 527 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_isc)))
		c.drawRightString( 550 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_icbper)))
		c.drawRightString( 574 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_otros)))
		c.drawRightString( 598 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_total)))

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.line(314,pos_inicial+3,598,pos_inicial+3)	

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('REGISTRO DE COMPRAS '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_ventas(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal-12, "*** REGISTRO DE VENTAS E INGRESOS DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-10,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-20, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-30, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 4
			style.alignment= 1

			data= [[Paragraph("<font size=4.5><b>N° Vou.</b></font>",style), 
				Paragraph("<font size=4.5><b>F. Emision</b></font>",style), 
				Paragraph("<font size=4.5><b>F. Venc</b></font>",style), 
				Paragraph("<font size=4.5><b>Comprobante de pago</b></font>",style), 
				'', 
				'',
				Paragraph("<font size=4.5><b>Informacion del Cliente</b></font>",style),
				'','',
				Paragraph("<font size=4.5><b>Valor Facturado de la Exportacion</b></font>",style),
				Paragraph("<font size=4.5><b>Base Imp. de la Ope. Gravada</b></font>",style),
				Paragraph("<font size=4.5><b>Imp. Total de la Operacion</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>I.S.C.</b></font>",style),
				Paragraph("<font size=4.5><b>I.G.V. y/o IPM</b></font>",style),
				Paragraph("<font size=4.5><b>ICBPER</b></font>",style),
				Paragraph("<font size=4.5><b>Otros Tributos y cargos que no forman parte de la base imponible</b></font>",style),
				Paragraph("<font size=4.5><b>Importe Total</b></font>",style),
				Paragraph("<font size=4.5><b>T.C.</b></font>",style),
				Paragraph("<font size=4.5><b>Referencia del Comprobante</b></font>",style),
				'','',''],
				['','','',
				Paragraph("<font size=4.5><b>T/D</b></font>",style),
				Paragraph("<font size=4.5><b>Serie</b></font>",style),
				Paragraph("<font size=4.5><b>Numero</b></font>",style),
				Paragraph("<font size=4.5><b>Doc. de Identidad</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Apellidos y nombres o Razon Social</b></font>",style),
				'','',
				Paragraph("<font size=4.5><b>Exonerada</b></font>",style),
				Paragraph("<font size=4.5><b>Inafecta</b></font>",style),
				'','','','','','',
				Paragraph("<font size=4.5><b>Fecha</b></font>",style),
				Paragraph("<font size=4.5><b>T/D</b></font>",style),
				Paragraph("<font size=4.5><b>Serie</b></font>",style),
				Paragraph("<font size=4.5><b>Numero</b></font>",style)],
				['','','','','','',
				Paragraph("<font size=4.5><b>Doc</b></font>",style),
				Paragraph("<font size=4.5><b>Numero</b></font>",style),
				'','','','','','','','','','','','','','','']]
			t=Table(data,colWidths=size_widths, rowHeights=(14))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,2)),
				('SPAN',(1,0),(1,2)),
				('SPAN',(2,0),(2,2)),
				('SPAN',(3,0),(5,0)),
				('SPAN',(3,1),(3,2)),
				('SPAN',(4,1),(4,2)),
				('SPAN',(5,1),(5,2)),
				('SPAN',(6,0),(8,0)),
				('SPAN',(6,1),(7,1)),
				('SPAN',(8,1),(8,2)),
				('SPAN',(9,0),(9,2)),
				('SPAN',(10,0),(10,2)),
				('SPAN',(11,0),(12,0)),
				('SPAN',(11,1),(11,2)),
				('SPAN',(12,1),(12,2)),
				('SPAN',(13,0),(13,2)),
				('SPAN',(14,0),(14,2)),
				('SPAN',(15,0),(15,2)),
				('SPAN',(16,0),(16,2)),
				('SPAN',(17,0),(17,2)),
				('SPAN',(18,0),(18,2)),
				('SPAN',(19,0),(22,0)),
				('SPAN',(19,1),(19,2)),
				('SPAN',(20,1),(20,2)),
				('SPAN',(21,1),(21,2)),
				('SPAN',(22,1),(22,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-112
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "venta_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [32,28,28,14,18,32,15,33,100,40,40,30,30,40,40,40,40,40,20,28,14,18,45]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-60

		c.setFont("Helvetica", 4)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_ventas(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		td = ''
		exp, venta_g, exo, inaf, isc_v, igv_v, icbper, otros_v, total = 0, 0, 0, 0, 0, 0, 0, 0, 0
		total_exp, total_venta_g, total_exo, total_inaf, total_isc_v, total_igv_v, total_icbper, total_otros_v, total_total = 0, 0, 0, 0, 0, 0, 0, 0, 0

		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica-Bold", 4)
			if cont == 0:
				td = i['td']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Tipo Doc.: ' + (td or '') )
				pos_inicial -= 10

			if td != i['td']:
				c.line(330,pos_inicial+3,667,pos_inicial+3)
				c.drawString( 280 ,pos_inicial-5,'TOTALES:')
				c.drawRightString( 367 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % exp)) )
				c.drawRightString( 407 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % venta_g)))
				c.drawRightString( 437 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % exo)))
				c.drawRightString( 467 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % inaf)))
				c.drawRightString( 507 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % isc_v)))
				c.drawRightString( 547 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv_v)))
				c.drawRightString( 587 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % icbper)))
				c.drawRightString( 627 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % otros_v)))
				c.drawRightString( 667 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)))

				exp, venta_g, exo, inaf, isc_v, igv_v, icbper, otros_v, total = 0, 0, 0, 0, 0, 0, 0, 0, 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 4)

				td = i['td']
				c.drawString( first_pos+2 ,pos_inicial,'Tipo Doc.: ' + (td or '') )
				pos_inicial -= 10


			c.setFont("Helvetica", 4)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['voucher'] if i['voucher'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_e'] if i['fecha_e'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_v'] if i['fecha_v'] else '',50) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td'] if i['td'] else '',50) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['serie'] if i['serie'] else '',50) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['numero'] if i['numero'] else '',50) )
			first_pos += size_widths[5]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['tdp'] if i['tdp'] else '',50) )
			first_pos += size_widths[6]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['docp'] if i['docp'] else '',50) )
			first_pos += size_widths[7]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['namep'] if i['namep'] else '',190) )
			first_pos += size_widths[8]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['exp'])) )
			exp += i['exp']
			total_exp += i['exp']
			first_pos += size_widths[9]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['venta_g'])) )
			venta_g += i['venta_g']
			total_venta_g += i['venta_g']
			first_pos += size_widths[10]

			c.drawRightString( first_pos+27 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['exo'])) )
			exo += i['exo']
			total_exo += i['exo']
			first_pos += size_widths[11]

			c.drawRightString( first_pos+27 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['inaf'])) )
			inaf += i['inaf']
			total_inaf += i['inaf']
			first_pos += size_widths[12]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['isc_v'])) )
			isc_v += i['isc_v']
			total_isc_v += i['isc_v']
			first_pos += size_widths[13]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['igv_v'])) )
			igv_v += i['igv_v']
			total_igv_v += i['igv_v']
			first_pos += size_widths[14]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['icbper'])) )
			icbper += i['icbper']
			total_icbper += i['icbper']
			first_pos += size_widths[15]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['otros_v'])) )
			otros_v += i['otros_v']
			total_otros_v += i['otros_v']
			first_pos += size_widths[16]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['total'])) )
			total += i['total']
			total_total += i['total']
			first_pos += size_widths[17]

			c.drawRightString( first_pos+17 ,pos_inicial,'{:,.4f}'.format(decimal.Decimal ("%0.4f" % i['currency_rate'])) )
			first_pos += size_widths[18]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['f_doc_m'] if i['f_doc_m'] else '',50) )
			first_pos += size_widths[19]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_doc_m'] if i['td_doc_m'] else '',50) )
			first_pos += size_widths[20]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['serie_m'] if i['serie_m'] else '',50) )
			first_pos += size_widths[21]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['numero_m'] if i['numero_m'] else '',50) )

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 4)
		c.line(330,pos_inicial+3,667,pos_inicial+3)
		c.drawString( 280 ,pos_inicial-5,'TOTALES:')
		c.drawRightString( 367 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % exp)) )
		c.drawRightString( 407 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % venta_g)))
		c.drawRightString( 437 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % exo)))
		c.drawRightString( 467 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % inaf)))
		c.drawRightString( 507 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % isc_v)))
		c.drawRightString( 547 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv_v)))
		c.drawRightString( 587 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % icbper)))
		c.drawRightString( 627 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % otros_v)))
		c.drawRightString( 667 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)))
		
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 4)

		c.line(330,pos_inicial+3,667,pos_inicial+3)

		c.drawString( 280 ,pos_inicial-5,'TOTAL GENERAL:')
		c.drawRightString( 367 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_exp)) )
		c.drawRightString( 407 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_venta_g)))
		c.drawRightString( 437 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_exo)))
		c.drawRightString( 467 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_inaf)))
		c.drawRightString( 507 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_isc_v)))
		c.drawRightString( 547 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_igv_v)))
		c.drawRightString( 587 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_icbper)))
		c.drawRightString( 627 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_otros_v)))
		c.drawRightString( 667 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_total)))

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.line(330,pos_inicial+3,667,pos_inicial+3)	

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('REGISTRO DE VENTAS  '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_libro_caja(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 9)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO CAJA - MOVIMIENTOS DEL EFECTIVO DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-12, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-22,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-32, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-42, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>NUMERO DE VOUCHER</b></font>",style), 
				Paragraph("<font size=8><b>FECHA DE OPERACION</b></font>",style), 
				Paragraph("<font size=8><b>DESCRIPCION DE LA OPERACION</b></font>",style), 
				Paragraph("<font size=8><b>SALDOS Y MOVIMIENTOS</b></font>",style),
				''],
				['','','',
				Paragraph("<font size=8><b>DEUDOR</b></font>",style),
				Paragraph("<font size=8><b>ACREEDOR</b></font>",style)]]
			t=Table(data,colWidths=size_widths, rowHeights=(20))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,1)),
				('SPAN',(1,0),(1,1)),
				('SPAN',(2,0),(2,1)),
				('SPAN',(3,0),(4,0)),
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-117
			else:
				return pagina,posactual-valor

		width ,height  = A4  # 595 , 842
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "libro_caja.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= A4 )
		pos_inicial = hReal-50
		pagina = 1

		size_widths = [80,80,235,70,70]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-55

		c.setFont("Helvetica", 8)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_caja(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		cuenta = ''
		sum_debe = 0
		sum_haber = 0
		saldo_debe = 0
		saldo_haber = 0

		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica-Bold", 10)
			if cont == 0:
				cuenta = i['cuenta']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cuenta: ' + cuenta + ' ' + i['name_cuenta'])
				pos_inicial -= 15

			if cuenta != i['cuenta']:
				c.setFont("Helvetica-Bold", 9)
				c.line(425,pos_inicial+3,565,pos_inicial+3)
				c.drawString( 350 ,pos_inicial-10,'TOTALES:')
				c.drawRightString( 495,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
				c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
				pos_inicial -= 10

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				c.line(425,pos_inicial+3,565,pos_inicial+3)
				c.drawString( 350 ,pos_inicial-10,'SALDO FINAL:')
				saldo_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
				saldo_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)

				c.drawRightString( 495,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_debe)) )
				c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_haber)))
				pos_inicial -= 20

				c.line(425,pos_inicial+3,565,pos_inicial+3)

				sum_debe = 0
				sum_haber = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 10)

				cuenta = i['cuenta']
				c.drawString( first_pos+2 ,pos_inicial,'Cuenta: ' + cuenta + ' ' + i['name_cuenta'])
				pos_inicial -= 15


			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['voucher'] if i['voucher'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha'] if i['fecha'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['glosa'] if i['glosa'] else '',150) )
			first_pos += size_widths[2]

			c.drawRightString( first_pos+70 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])) )
			sum_debe += i['debe']
			first_pos += size_widths[3]

			c.drawRightString( first_pos+70 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])))
			sum_haber += i['haber']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 9)
		c.line(425,pos_inicial+3,565,pos_inicial+3)
		c.drawString( 350 ,pos_inicial-10,'TOTALES:')
		c.drawRightString( 495,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
		c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(425,pos_inicial+3,565,pos_inicial+3)
		c.drawString( 350 ,pos_inicial-10,'SALDO FINAL:')
		saldo_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
		saldo_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)

		c.drawRightString( 495,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_debe)) )
		c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_haber)))
		pos_inicial -= 20

		c.line(425,pos_inicial+3,565,pos_inicial+3)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO CAJA '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_libro_banco(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO BANCOS - MOVIMIENTOS DE LA CUENTA CORRIENTE DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=7.5><b>N° VOU.</b></font>",style), 
				Paragraph("<font size=7.5><b>N° CORRELATIVO DEL LIBRO DIARIO</b></font>",style), 
				Paragraph("<font size=7.5><b>FECHA OPERACION</b></font>",style), 
				Paragraph("<font size=8><b>OPERACIONES BANCARIAS</b></font>",style),
				'', 
				'',
				'',
				Paragraph("<font size=8><b>SALDOS Y MOVIMIENTOS</b></font>",style),
				''],
				['','','',
				Paragraph("<font size=7.5>MEDIO DE PAGO</font>",style),
				Paragraph("<font size=7.5>DESC. OPERACION</font>",style),
				Paragraph("<font size=7.5>APELLIDOS Y NOMBRES, DENOMINACION O RAZON SOCIAL</font>",style),
				Paragraph("<font size=7>N. TRANSACCIÓN BANCARIA DE DOCUMENTOS O DE CONTROL INTERNO DE LA OPERACIÓN</font>",style),
				Paragraph("<font size=7.5><b>DEUDOR</b></font>",style),
				Paragraph("<font size=7.5><b>ACREEDOR</b></font>",style)]]
			t=Table(data,colWidths=size_widths, rowHeights=[18,30])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,1)),
				('SPAN',(1,0),(1,1)),
				('SPAN',(2,0),(2,1)),
				('SPAN',(3,0),(6,0)),
				('SPAN',(7,0),(8,0)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-112
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "banco_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [45,55,55,55,150,140,120,85,85]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-60

		c.setFont("Helvetica", 7)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_banco(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		
		cont = 0
		cuenta = ''
		debe, haber, sum_debe, sum_haber, final_debe, final_haber = 0, 0, 0, 0, 0, 0

		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica-Bold", 7)
			if cont == 0:
				cuenta = i['cuenta']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,i['cuenta'])
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+30 ,pos_inicial,particionar_text(i['nombre_cuenta'],110))
				c.setFont("Helvetica-Bold", 6)
				c.drawString( first_pos+140 ,pos_inicial,'Cod. Ent. Financiera:')
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+200 ,pos_inicial,i['code_bank'] if i['code_bank'] else '')
				c.setFont("Helvetica-Bold", 6)
				c.drawString( first_pos+400 ,pos_inicial,'Número de cuenta:')
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+470 ,pos_inicial,i['account_number'] if i['account_number'] else '')
				pos_inicial -= 15

			if cuenta != i['cuenta']:
				c.line(655,pos_inicial+3,815,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'SUB TOTAL:')
				c.drawRightString( 730,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)) )
				c.drawRightString( 815 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)))

				debe, haber = 0, 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 7)

				cuenta = i['cuenta']
				c.drawString( first_pos+2 ,pos_inicial,i['cuenta'])
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+30 ,pos_inicial,particionar_text(i['nombre_cuenta'],110))
				c.setFont("Helvetica-Bold", 7)
				c.drawString( first_pos+140 ,pos_inicial,'Cod. Ent. Financiera:')
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+200 ,pos_inicial,i['code_bank'] if i['code_bank'] else '')
				c.setFont("Helvetica-Bold", 7)
				c.drawString( first_pos+400 ,pos_inicial,'Número de cuenta:')
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+470 ,pos_inicial,i['account_number'] if i['account_number'] else '')
				pos_inicial -= 10


			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['libro'] if i['libro'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['voucher'] if i['voucher'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha'] if i['fecha'] else '',50) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['medio_pago'] if i['medio_pago'] else '',50) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['glosa'] if i['glosa'] else '',150) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',120) )
			first_pos += size_widths[5]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',50) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+82 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])) )
			debe += i['debe']
			sum_debe += i['debe']
			first_pos += size_widths[7]

			c.drawRightString( first_pos+82 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])) )
			haber += i['haber']
			sum_haber += i['haber']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 7)
		c.line(655,pos_inicial+3,815,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SUB TOTAL:')
		c.drawRightString( 730,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)) )
		c.drawRightString( 815 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)))
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 7)

		c.line(655,pos_inicial+3,815,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'TOTALES:')
		c.drawRightString( 730,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
		c.drawRightString( 815 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 7)

		c.line(655,pos_inicial+3,815,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		final_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
		final_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)

		c.drawRightString( 730,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_debe)) )
		c.drawRightString( 815 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_haber)))
		pos_inicial -= 20

		c.line(655,pos_inicial+3,815,pos_inicial+3)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO BANCOS '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_inventario_balance(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO INVENTARIO Y BALANCE - BALANCE DE COMPROBACION DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=9><b>CUENTA Y SUBCUENTA CONTABLE</b></font>",style),'',
				Paragraph("<font size=9><b>SALDOS INICIALES</b></font>",style),'',
				Paragraph("<font size=9><b>MOVIMIENTOS</b></font>",style),'',
				Paragraph("<font size=9><b>SALDOS FINALES</b></font>",style),'',
				Paragraph("<font size=9><b>SALDOS FINALES DEL BALANCE GENERAL</b></font>",style),'',
				Paragraph("<font size=9><b>PERDIDAS FINALES EST. DE PERDIDAS Y GANAN. POR FUNCION</b></font>",style),''],
				[Paragraph("<font size=9><b>CUENTA</b></font>",style),
				Paragraph("<font size=8.5><b>DENOMINACION</b></font>",style),
				Paragraph("<font size=8.5><b>DEUDOR</b></font>",style),
				Paragraph("<font size=8.5><b>ACREEDOR</b></font>",style),
				Paragraph("<font size=8.5><b>DEBE</b></font>",style),
				Paragraph("<font size=8.5><b>HABER</b></font>",style),
				Paragraph("<font size=8.5><b>DEUDOR</b></font>",style),
				Paragraph("<font size=8.5><b>ACREEDOR</b></font>",style),
				Paragraph("<font size=8.5><b>ACTIVO</b></font>",style),
				Paragraph("<font size=8.5><b>PASIVO</b></font>",style),
				Paragraph("<font size=8.5><b>PERDIDA</b></font>",style),
				Paragraph("<font size=8.5><b>GANANCIA</b></font>",style)]]
			t=Table(data,colWidths=size_widths, rowHeights=[30,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,0)),
				('SPAN',(2,0),(3,0)),
				('SPAN',(4,0),(5,0)),
				('SPAN',(6,0),(7,0)),
				('SPAN',(8,0),(9,0)),
				('SPAN',(10,0),(11,0)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-112
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "inv_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [48,185,55,55,55,55,55,55,55,55,55,55]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-60

		c.setFont("Helvetica", 7)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_inventario(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		debe_inicial, haber_inicial, debe, haber, saldo_deudor, saldo_acreedor, activo, pasivo, perdifun, gananfun = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['cuenta'] if i['cuenta'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nomenclatura'] if i['nomenclatura'] else '',200) )
			first_pos += size_widths[1]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe_inicial'])) )
			debe_inicial += i['debe_inicial']
			first_pos += size_widths[2]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber_inicial'])) )
			haber_inicial += i['haber_inicial']
			first_pos += size_widths[3]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])) )
			debe += i['debe']
			first_pos += size_widths[4]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])) )
			haber += i['haber']
			first_pos += size_widths[5]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_deudor'])) )
			saldo_deudor += i['saldo_deudor']
			first_pos += size_widths[6]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_acreedor'])) )
			saldo_acreedor += i['saldo_acreedor']
			first_pos += size_widths[7]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['activo'])) )
			activo += i['activo']
			first_pos += size_widths[8]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['pasivo'])) )
			pasivo += i['pasivo']
			first_pos += size_widths[9]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['perdifun'])) )
			perdifun += i['perdifun']
			first_pos += size_widths[10]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['gananfun'])) )
			gananfun += i['gananfun']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 7)
		c.line(80,pos_inicial+3,815,pos_inicial+3)
		c.drawString( 80 ,pos_inicial-10,'TOTALES:')
		c.drawRightString( 316,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe_inicial)) )
		c.drawRightString( 371,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber_inicial)) )
		c.drawRightString( 426,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)) )
		c.drawRightString( 481 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)))
		c.drawRightString( 536 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_deudor)))
		c.drawRightString( 591 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_acreedor)))
		c.drawRightString( 646 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % activo)))
		c.drawRightString( 701 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % pasivo)))
		c.drawRightString( 756 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % perdifun)))
		c.drawRightString( 811 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % gananfun)))
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 7)

		c.line(80,pos_inicial+3,815,pos_inicial+3)
		c.drawString( 80 ,pos_inicial-10,'GANANCIA DEL EJERCICIO:')
		final_activo = abs(activo - pasivo) if (activo - pasivo) < 0 else 0
		final_pasivo = (activo - pasivo) if (activo - pasivo) > 0 else 0
		c.drawRightString( 646,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_activo)) )
		c.drawRightString( 701 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_pasivo)))
		final_perdifun = abs(perdifun - gananfun) if (perdifun - gananfun) < 0 else 0
		final_gananfun = (perdifun - gananfun) if (perdifun - gananfun) > 0 else 0
		c.drawRightString( 756 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_perdifun)))
		c.drawRightString( 811 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_gananfun)))
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 7)

		c.line(80,pos_inicial+3,815,pos_inicial+3)
		c.drawString( 80 ,pos_inicial-10,'SUMAS IGUALES:')

		c.drawRightString( 646,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_activo + activo))) )
		c.drawRightString( 701,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_pasivo + pasivo))) )
		c.drawRightString( 756,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_perdifun + perdifun))) )
		c.drawRightString( 811,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_gananfun + gananfun))) )
		pos_inicial -= 20

		c.line(80,pos_inicial+3,815,pos_inicial+3)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO INVENTARIO Y BALANCE '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))


	def get_pdf_10_caja_bancos(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 10 - CAJA Y BANCOS DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1 

			data= [[Paragraph("<font size=9><b>CUENTA CONTABLE DIVISIONARIA</b></font>",style),'',
				Paragraph("<font size=9><b>REFERENCIA DE LA CUENTA</b></font>",style),'','',
				Paragraph("<font size=9><b>SALDO CONTABLE FINAL</b></font>",style),''],
				[Paragraph("<font size=9><b>CODIGO</b></font>",style),
				Paragraph("<font size=9><b>DENOMINACION</b></font>",style),
				Paragraph("<font size=9><b>ENT. FINANCIERA</b></font>",style),
				Paragraph("<font size=9><b>NUMERO DE CTA</b></font>",style),
				Paragraph("<font size=9><b>MONEDA</b></font>",style),
				Paragraph("<font size=9><b>DEUDOR</b></font>",style),
				Paragraph("<font size=9><b>ACREEDOR</b></font>",style)]]
			t=Table(data,colWidths=size_widths, rowHeights=[30,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,0)),
				('SPAN',(2,0),(4,0)),
				('SPAN',(5,0),(6,0)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "caja_10.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,200,100,150,50,100,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica", 7)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_10_caja_bancos(self.period_id.code,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		debe, haber = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica", 9)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['cuenta'] if i['cuenta'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nomenclatura'] if i['nomenclatura'] else '',215) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['code_bank'] if i['code_bank'] else '',50) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['account_number'] if i['account_number'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,str(i['moneda']) if i['moneda'] else '')
			first_pos += size_widths[4]

			c.drawRightString( first_pos+100 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])) )
			debe += i['debe']
			first_pos += size_widths[5]

			c.drawRightString( first_pos+100 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])) )
			haber += i['haber']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(585,pos_inicial+3,780,pos_inicial+3)
		c.drawString( 500 ,pos_inicial-10,'TOTALES:')
		c.drawRightString( 680 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)))
		c.drawRightString( 780 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)))

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 10  '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_12_cliente(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 12 - CLIENTES DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL CLIENTE</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO (TABLA2)</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "caja_12.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_12_cliente(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 12 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_13_cobrar_relacionadas(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 13 - RELACIONADAS DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL CLIENTE</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO (TABLA2)</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "caja_13.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_13_cobrar_relacionadas(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 13 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_14_cobrar_acc_personal(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 14 - CTAS x COB. A ACCIONISTAS Y PERSONAL DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACIÓN DEL ACCIONISTA, SOCIO O PERSONAL</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE INICIO DE LA OPERACION</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "caja_14.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_14_cobrar_acc_personal(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 14 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_16_cobrar_diversas(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 11)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 16 - CTAS x COB. DIVERSAS DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DE TERCEROS</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION COMP.DE PAGO O F. INICIO OPERACION</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "caja_16.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_16_cobrar_diversas(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 16 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_19_cobrar_dudosa(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 19 - PROVISION PARA CTAS DE COBRANZA DUDOSA DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DE DEUDORES</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION COMP.DE PAGO O F. INICIO OPERACION</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "caja_19.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_19_cobrar_dudosa(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 19 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_cuenta_40(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 8)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 40 - TRIBUTOS POR PAGAR DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-12, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-22,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-32, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-42, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=9><b>CUENTA Y SUB CUENTA TRIBUTOS POR PAGAR</b></font>",style),'', 
				Paragraph("<font size=8><b>SALDO FINAL</b></font>",style)],
				[Paragraph("<font size=8><b>CODIGO</b></font>",style),
				Paragraph("<font size=8><b>DENOMINACION</b></font>",style),'']]
			t=Table(data,colWidths=size_widths, rowHeights=(20))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,0)),
				('SPAN',(2,0),(2,1)),
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,70,500) 
			t.drawOn(c,70,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-117
			else:
				return pagina,posactual-valor

		width ,height  = A4  # 595 , 842
		wReal = width - 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_40.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= A4 )
		pos_inicial = hReal-50
		pagina = 1

		size_widths = [80,300,80]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-55

		c.setFont("Helvetica", 8)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_40(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		saldo = 0

		for i in res:
			first_pos = 70

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['cuenta'] if i['cuenta'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nomenclatura'] if i['nomenclatura'] else '',250) )
			first_pos += size_widths[1]

			c.drawRightString( first_pos+80 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo'])))
			saldo += i['saldo']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 9)
		c.line(450,pos_inicial+3,530,pos_inicial+3)
		c.drawString( 390 ,pos_inicial-10,'TOTAL:')
		c.drawRightString( 530,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo)) )
		pos_inicial -= 20

		c.line(450,pos_inicial+3,530,pos_inicial+3)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 40 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))


	def get_pdf_cuenta_41(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 8)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 41 - REMUNERACIONES POR PAGAR DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-12, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-22,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-32, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-42, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=9><b>CUENTA Y SUBCUENTA REMUNERACIONES POR PAGAR</b></font>",style),'', 
				Paragraph("<font size=8><b>TRABAJADOR</b></font>",style),'','','',
				Paragraph("<font size=8><b>SALDO FINAL</b></font>",style)],
				['','',
				Paragraph("<font size=8><b>CODIGO</b></font>",style),
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES</b></font>",style),
				Paragraph("<font size=8><b>DOC DE IDENT.</b></font>",style),'',''],
				[Paragraph("<font size=7.5><b>CODIGO</b></font>",style),
				Paragraph("<font size=8><b>DENOMINACION</b></font>",style),'','',
				Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),'']]
			t=Table(data,colWidths=size_widths, rowHeights=(16))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,1)),
				('SPAN',(2,0),(5,0)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,1),(3,2)),
				('SPAN',(4,1),(5,1)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-117
			else:
				return pagina,posactual-valor

		width ,height  = A4  # 595 , 842
		wReal = width - 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_40.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= A4 )
		pos_inicial = hReal-50
		pagina = 1

		size_widths = [44,160,50,150,31,50,50]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-55

		c.setFont("Helvetica", 8)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_41(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		saldo = 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['cuenta'] if i['cuenta'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nomenclatura'] if i['nomenclatura'] else '',180) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['ref'] if i['ref'] else '',50) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',150) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[5]

			c.drawRightString( first_pos+50 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo'])))
			saldo += i['saldo']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 9)
		c.line(515,pos_inicial+3,565,pos_inicial+3)
		c.drawString( 470 ,pos_inicial-10,'TOTAL:')
		c.drawRightString( 565,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo)) )
		pos_inicial -= 20

		c.line(515,pos_inicial+3,565,pos_inicial+3)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 41 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_cuenta_42(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 42 - CTAS POR PAGAR COMERCIALES TERCEROS DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_42.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_42(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 42 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_cuenta_43(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 43 - CTAS POR PAGAR COMERCIALES RELACIONADAS DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_43.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_43(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 43 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_cuenta_44(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 44 - CTAS POR PAGAR ACCIONISTAS Y DIRECTORES DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_44.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_44(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 44 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_cuenta_45(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 45 - OBLIGACIONES FINANCIERAS DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_45.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_45(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 45 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_cuenta_46(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 46 - CTAS POR PAGAR DIVERSAS TERCEROS DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_46.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_46(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 46 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_cuenta_47(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 47 - CTAS POR PAGAR DIVERSAS RELACIONADAS DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_47.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_47(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 47 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_cuenta_48(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 48 - PROVISIONES DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_48.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_48(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 48 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_cuenta_49(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 49 - PASIVO DIFERIDO DEL MES DE %s ***"%(self.period_id.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-122
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_49.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_49(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 49 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))
	
	#_________________INCORPORACION DE EXCEL________________#
	def get_report_3_1(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_1()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_financial_situation()	
	
	def get_excel_3_1(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Formato_3_1.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.1 Balance General")
		worksheet.set_tab_color('blue')
		decimal_rounding = '%0.2f'
		period_ini = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		finan_sit = self.env['financial.situation.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_from':period_ini.id,'period_to':self.period_id.id})
		finan_sit._get_financial_situation_sql()
		currents_B1 = self.env['financial.situation'].search([('group_balance','=','B1')])
		currents_B2 = self.env['financial.situation'].search([('group_balance','=','B2')])
		currents_B3 = self.env['financial.situation'].search([('group_balance','=','B3')])
		currents_B4 = self.env['financial.situation'].search([('group_balance','=','B4')])
		currents_B5 = self.env['financial.situation'].search([('group_balance','=','B5')])
		worksheet.merge_range(2,0,2,8, "LIBRO DE INVENTARIOS Y BALANCES - BALANCE GENERAL", formats['especial5'] )
		
		worksheet.write(4,1,"EJERCICIO",formats['especial2'])
		worksheet.write(4,2,self.period_id.fiscal_year_id.name,formats['especial2'])
		worksheet.write(5,1,"RUC:",formats['especial2'])
		worksheet.write(5,2,self.company_id.partner_id.vat,formats['especial2'])
		worksheet.merge_range(6,1,6,6,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + self.company_id.partner_id.name ,formats['especial2'])

		x=8
		worksheet.write(x,2,"ACTIVO",formats['especial2'])
		worksheet.write(x,5,"PASIVO Y PATRIMONIO",formats['especial2'])
		x+=2
		worksheet.write(x,2,"ACTIVO CORRIENTE",formats['especial2'])
		worksheet.write(x,5,"PASIVO CORRIENTE",formats['especial2'])
		x+=1
		total_B1 = 0
		aux=x
		
		for current in currents_B1:
			worksheet.merge_range(x,2,x,3,current.name,formats['especial1'])
			worksheet.write(x,4,str(decimal_rounding % current.total),formats['numberdos'])
			total_B1 += current.total
			x+=1
		worksheet.merge_range(x,2,x,3,"TOTAL ACTIVO CORRIENTE",formats['especial2'])
		worksheet.write(x,4,str(decimal_rounding % total_B1),formats['numbertotal'])
		pos_total = x
		total_B3 = 0
		for current in currents_B3:
			worksheet.merge_range(aux,5,aux,6,current.name,formats['especial1'])
			worksheet.write(aux,7,str(decimal_rounding % current.total),formats['numberdos'])
			total_B3 += current.total
			aux+=1
		worksheet.merge_range(pos_total,5,pos_total,6,"TOTAL ACTIVO CORRIENTE",formats['especial2'])
		worksheet.write(pos_total,7,str(decimal_rounding % total_B3),formats['numbertotal'])
		if aux > x:
			x=aux
		else:
			aux=x
		x+=3
		worksheet.write(x,2,"ACTIVO NO CORRIENTE",formats['especial2'])
		worksheet.write(x,5,"PASIVO NO CORRIENTE",formats['especial2'])
		x+=1
		aux=x
		total_B2 = 0		
		for current in currents_B2:
			worksheet.merge_range(x,2,x,3,current.name,formats['especial1'])
			worksheet.write(x,4,str(decimal_rounding % current.total),formats['numberdos'])
			total_B2 += current.total
			x+=1
		worksheet.merge_range(x,2,x,3,"TOTAL ACTIVO NO CORRIENTE",formats['especial2'])
		worksheet.write(x,4,str(decimal_rounding % total_B2),formats['numbertotal'])
		pos_total = x
		total_B4 = 0
		for current in currents_B4:
			worksheet.merge_range(aux,5,aux,6,current.name,formats['especial1'])
			worksheet.write(aux,4,str(decimal_rounding % current.total),formats['numberdos'])
			total_B4 += current.total
			aux+=1
		worksheet.merge_range(pos_total,5,pos_total,6,"TOTAL PASIVO NO CORRIENTE",formats['especial2'])
		worksheet.write(pos_total,7,str(decimal_rounding % total_B4),formats['numbertotal'])
		if aux > x:
			x=aux
		else:
			aux=x

		x+=3
		worksheet.write(x,5,"PATRIMONIO",formats['especial2'])
		x+=1
		
		total_B5 = 0
		for current in currents_B5:
			worksheet.merge_range(x,5,x,6,current.name,formats['especial1'])
			worksheet.write(x,7,str(decimal_rounding % current.total),formats['numberdos'])
			total_B5 += current.total
			x+=1
		worksheet.merge_range(x,5,x,6,"TOTAL PATRIMONIO",formats['especial2'])
		worksheet.write(x,7,str(decimal_rounding % total_B5),formats['numbertotal'])
		x+=2
		period_result = (total_B1 + total_B2) - (total_B3 + total_B4 + total_B5)
		worksheet.merge_range(x,5,x,6,"RESULTADO DEL PERIODO",formats['especial2'])
		worksheet.write(x,7,str(decimal_rounding % period_result),formats['numbertotal'])
		x+=1
		worksheet.merge_range(x,2,x,3,"TOTAL ACTIVO ",formats['especial2'])
		worksheet.merge_range(x,5,x,6,"TOTAL PASIVO Y PATRIMONIO",formats['especial2'])
		worksheet.write(x,4,str(decimal_rounding % (total_B1 + total_B2)),formats['numbertotal'])
		worksheet.write(x,7,str(decimal_rounding % (total_B3 + total_B4 + total_B5 + period_result)),formats['numbertotal'])
		
		widths = [8,9,27,17,10,27,17,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Formato_3_1.xlsx', 'rb')
		return self.env['popup.it'].get_file('Situacion Financiera.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_financial_situation(self):
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		doc = SimpleDocTemplate(direccion + 'Formato_3_1.pdf',pagesize=landscape(letter))
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		decimal_rounding = '%0.2f'
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		top_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
					 ('VALIGN', (0, 0), (-1, -1), 'TOP')]
		internal_width = [7.5*cm,2.5*cm]
		internal_height = [0.5*cm]
		external_width = [10*cm,10*cm]
		spacer = Spacer(10, 20)
		period_ini = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)

		finan_sit = self.env['financial.situation.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_from':period_ini.id,'period_to':self.period_id.id})
		finan_sit._get_financial_situation_sql()
		currents_B1 = self.env['financial.situation'].search([('group_balance','=','B1')])
		currents_B2 = self.env['financial.situation'].search([('group_balance','=','B2')])
		currents_B3 = self.env['financial.situation'].search([('group_balance','=','B3')])
		currents_B4 = self.env['financial.situation'].search([('group_balance','=','B4')])
		currents_B5 = self.env['financial.situation'].search([('group_balance','=','B5')])

		elements.append(Paragraph('<strong>FORMATO 3.1 : "LIBRO DE INVENTARIOS Y BALANCES - BALANCE GENERAL"</strong>', style_title))
		elements.append(Spacer(20, 10))
		elements.append(Paragraph('<strong>           EJERCICIO: %s</strong>'%(self.period_id.fiscal_year_id.name), style_left))
		elements.append(Spacer(10, 5))
		elements.append(Paragraph('<strong>RUC: %s</strong>'%(self.company_id.partner_id.vat), style_left))
		elements.append(Spacer(10, 5))
		elements.append(Paragraph(u'<strong>APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s</strong>'%(self.company_id.partner_id.name), style_left))
		elements.append(Spacer(10, 10))
		period_c = self.period_id.code
		data = [
			 ['',Paragraph('<strong>%s</strong>'%(period_c[4:]+'-'+period_c[:4]),style_right),'',
			  Paragraph('<strong>%s</strong>'%(period_c[4:]+'-'+period_c[:4]),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		data = [
			 [Paragraph('<strong>ACTIVO</strong>',style_left),'',
			  Paragraph('<strong>PASIVO Y PATRIMONIO</strong>',style_left),'']
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		data = [
				[Paragraph('<strong>ACTIVO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B1 = 0
		for current in currents_B1:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B1 += current.total
		t1 = Table(data,internal_width,y*internal_height)
		t1.setStyle(TableStyle(simple_style))
		data = [
				[Paragraph('<strong>PASIVO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B3 = 0
		for current in currents_B3:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B3 += current.total
		t2 = Table(data,internal_width,y*internal_height)
		t2.setStyle(TableStyle(simple_style))
		t3 = Table([[t1,t2]],external_width)
		t3.setStyle(TableStyle(top_style))
		elements.append(t3)

		data = [
			[Paragraph('<strong>TOTAL ACTIVO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B1),style_right),
			 Paragraph('<strong>TOTAL PASIVO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B3),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)
		
		data = [
				[Paragraph('<strong>ACTIVO NO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B2 = 0
		for current in currents_B2:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B2 += current.total
		t1 = Table(data,internal_width,y*[0.8*cm])
		t1.setStyle(TableStyle(simple_style))
		data = [
				[Paragraph('<strong>PASIVO NO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B4 = 0
		for current in currents_B4:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B4 += current.total
		t2 = Table(data,internal_width,y*internal_height)
		t2.setStyle(TableStyle(simple_style))
		t3 = Table([[t1,t2]],external_width)
		t3.setStyle(TableStyle(top_style))
		elements.append(t3)

		data = [
			[Paragraph('<strong>TOTAL ACTIVO NO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B2),style_right),
			 Paragraph('<strong>TOTAL PASIVO NO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B4),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		data = [
				[Paragraph('<strong>PATRIMONIO</strong>',style_left),'']
			   ]
		y = 1
		total_B5 = 0
		for current in currents_B5:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B5 += current.total
		t2 = Table(data,internal_width,y*internal_height)
		t2.setStyle(TableStyle(simple_style))
		t3 = Table([['',t2]],external_width)
		t3.setStyle(TableStyle(top_style))
		elements.append(t3)

		data = [
			['','',
			 Paragraph('<strong>TOTAL PATRIMONIO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B5),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		period_result = (total_B1 + total_B2) - (total_B3 + total_B4 + total_B5)
		data = [
			['','',
			 Paragraph('<strong>RESULTADO DEL PERIODO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % period_result),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)
		data = [
			[Paragraph('<strong>TOTAL ACTIVO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % (total_B1 + total_B2)),style_right),
			 Paragraph('<strong>TOTAL PASIVO Y PATRIMONIO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % (total_B3 + total_B4 + total_B5 + period_result)),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		doc.build(elements)

		f = open(direccion +'Formato_3_1.pdf', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIOS Y BALANCES - BALANCE GENERAL.pdf',base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_2(self):
			if self.type_show_inventory_balance == 'excel':
				return self.get_excel_3_2()
			if self.type_show_inventory_balance == "pdf":
				return self.get_pdf_10_caja_bancos()

	def get_excel_3_2(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'caja_10.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.2 CAJA Y BANCOS")
		worksheet.set_tab_color('blue')
		
		x=2
		worksheet.merge_range(x,0,x,8,'LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 10 '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,2,"CUENTA CONTABLE DIVISIONARIA",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x,5,"REFERENCIA DE LA CUENTA ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x,7,"SALDO CONTABLE FINAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"CODIGO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"DENOMINACION",formats_custom['especial_2_custom'])
		worksheet.write(x,3,"ENT. FINANCIERA",formats_custom['especial_2_custom'])
		worksheet.write(x,4,"NUMERO DE CTA",formats_custom['especial_2_custom'])
		worksheet.write(x,5,"MONEDA",formats_custom['especial_2_custom'])
		worksheet.write(x,6,"DEUDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,7,"ACREEDOR",formats_custom['especial_2_custom'])
		
		sql = self.env['account.base.sunat'].pdf_get_sql_vst_10_caja_bancos(self.period_id.code,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		#self.env.cr.execute(_get_sql_vst_10_caja_bancos(self))
		#res = self.env.cr.dictfetchall()
		x+=1
		debe, haber = 0, 0
		for i in res:
			worksheet.write(x,1,i['cuenta'] if i['cuenta'] else '',formats['especial1'])
			worksheet.write(x,2,i['nomenclatura'] if i['nomenclatura'] else '',formats['especial1'])
			worksheet.write(x,3,i['code_bank'] if i['code_bank'] else '',formats['especial1'])
			worksheet.write(x,4,i['account_number'] if i['account_number'] else '',formats['especial1'])
			worksheet.write(x,5,i['moneda'] if i['moneda'] else '',formats['especial1'])
			worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])),formats['numberdos'])
			debe += i['debe']
			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])),formats['numberdos'])
			haber += i['haber']
			x+=1
		worksheet.write(x,5,"TOTALES",formats['especial2'])
		worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)),formats['numbertotal'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)),formats['numbertotal'])
		widths = [8,9,42,18,17,11,15,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'caja_10.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 10  '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_3(self):
			if self.type_show_inventory_balance == 'excel':
				return self.get_excel_3_3()
			if self.type_show_inventory_balance == "pdf":
				return self.get_pdf_12_cliente()

	def get_excel_3_3(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'caja_12.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.3 CLIENTES")
		worksheet.set_tab_color('blue')
		
		x=2
		worksheet.merge_range(x,0,x,7,'LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 12 '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DEL CLIENTE",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO (TABLA2) ",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])
		
		sql = self.env['account.base.sunat'].pdf_get_sql_vst_12_cliente(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: '+ i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1
		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'caja_12.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 12 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))
	
	def get_report_3_4(self):
			if self.type_show_inventory_balance == 'excel':
				return self.get_excel_3_4()
			if self.type_show_inventory_balance == "pdf":
				return self.get_pdf_14_cobrar_acc_personal()

	def get_excel_3_4(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'caja_14.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.4 Accionistas")
		worksheet.set_tab_color('blue')
		

		x=2
		worksheet.merge_range(x,0,x,7,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 14 - CTAS x COB. A ACCIONISTAS Y PERSONAL DEL MES DE %s'%(self.period_id.name), formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACIÓN DEL ACCIONISTA, SOCIO O PERSONAL",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])
		
		sql = self.env['account.base.sunat'].pdf_get_sql_vst_14_cobrar_acc_personal(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: '+ i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1
		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'caja_14.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - CUENTA 14 - CTAS x COB. A ACCIONISTAS Y PERSONAL DEL MES DE %s'%(self.period_id.name),base64.encodebytes(b''.join(f.readlines())))
		
	def get_report_3_5(self):
			if self.type_show_inventory_balance == 'excel':
				return self.get_excel_3_5()
			if self.type_show_inventory_balance == "pdf":
				return self.get_pdf_16_cobrar_diversas()

	def get_excel_3_5(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'caja_16.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.5 Cuentas por cobrar")
		worksheet.set_tab_color('blue')
		
		
		x=2
		worksheet.merge_range(x,0,x,7,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 16 - CTAS x COB. DIVERSAS DEL MES DE %s'%(self.period_id.name), formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DE TERCEROS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])
		
		sql = self.env['account.base.sunat'].pdf_get_sql_vst_16_cobrar_diversas(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: '+ i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1
		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'caja_16.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - CUENTA 16 - CTAS x COB. DIVERSAS DEL MES DE %s'%(self.period_id.name),base64.encodebytes(b''.join(f.readlines())))
	
	def get_report_3_6(self):
			if self.type_show_inventory_balance == 'excel':
				return self.get_excel_3_6()
			if self.type_show_inventory_balance == "pdf":
				return self.get_pdf_19_cobrar_dudosa()

	def get_excel_3_6(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'caja_19.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.6 Provision")
		worksheet.set_tab_color('blue')
		
		
		x=2
		worksheet.merge_range(x,0,x,7,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 19 - PROVISION PARA CTAS DE COBRANZA DUDOSA DEL MES DE %s'%(self.period_id.name), formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DE DEUDORES",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])
		
		sql = self.env['account.base.sunat'].pdf_get_sql_vst_19_cobrar_dudosa(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: '+ i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1

		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'caja_19.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - CUENTA 19 - PROVISION PARA CTAS DE COBRANZA DUDOSA DEL MES DE %s'%(self.period_id.name),base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_7(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_7()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_libro_37()	
	
	def get_excel_3_7(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'libro_37.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.7 Mercaderias")
		worksheet.set_tab_color('blue')
		decimal_rounding = '%0.2f'
		worksheet.merge_range(2,0,2,8, 'FORMATO 3.7: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA "', formats['especial5'] )
		worksheet.merge_range(3,0,3,8, 'CUENTA 20 - MERCADERIAS Y LA CUENTA 21 - PRODUCTOS TERMINADOS"', formats['especial5'] )


		worksheet.write(4,1,"Periodos",formats['especial2'])
		worksheet.write(4,2,self.period_id.fiscal_year_id.name,formats['especial2'])
		worksheet.write(5,1,"RUC:",formats['especial2'])
		worksheet.write(5,2,self.company_id.partner_id.vat,formats['especial2'])
		worksheet.merge_range(6,1,6,6,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + self.company_id.partner_id.name ,formats['especial2'])
		worksheet.merge_range(7,1,7,6,u"MÉTODO DE EVALUACIÓN APLICADO: ",formats['especial2'])
		#worksheet.write(7,7,self.company_id.partner_id.name,formats['especial2'])
		
		worksheet.write(8,1,"CODIGO DE LA EXISTENCIA",formats['especial2'])
		worksheet.write(8,2,"TIPO DE EXISTENCIA (TABLA 5)",formats['especial2'])
		worksheet.write(8,3,"DESCRIPCIÓN",formats['especial2'])
		worksheet.write(8,4,u"CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6)",formats['especial2'])
		worksheet.write(8,5,"CANTIDAD",formats['especial2'])
		worksheet.write(8,6,"COSTO UNITARIO",formats['especial2'])
		worksheet.write(8,7,"COSTO TOTAL",formats['especial2'])
		
		worksheet.write(9,5,"COSTO TOTAL GENERAL",formats['especial2'])
		widths = [10,33,25,68,27,30,21,19]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'libro_37.xlsx', 'rb')
		return self.env['popup.it'].get_file('Cuenta 20 - Mercaderias',base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_8(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_8()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_38()	
	
	def get_excel_3_8(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'libro_38.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.8 Valores")
		worksheet.set_tab_color('blue')
		decimal_rounding = '%0.2f'
		worksheet.merge_range(2,0,2,8, 'FORMATO 3.8: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA LA CUENTA 31 - VALORES"', formats['especial5'] )


		worksheet.write(4,1,"Periodos",formats['especial2'])
		worksheet.write(4,2,self.period_id.fiscal_year_id.name,formats['especial2'])
		worksheet.write(5,1,"RUC:",formats['especial2'])
		worksheet.write(5,2,self.company_id.partner_id.vat,formats['especial2'])
		worksheet.merge_range(6,1,6,3,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + self.company_id.partner_id.name ,formats['especial2'])
	
		#CABECERAS DEL REPORTE
		formats_custom={}
		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom
		x=8
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL DEL ACCIONISTA O SOCIO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,"TITULO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x,9,"VALOR EN LIBROS",formats_custom['especial_2_custom'])

		x+=1
		worksheet.write(x,1,"TIPO (TABLA 2)",formats_custom['especial_2_custom'])
		worksheet.write(x,2,u"NÚMERO",formats_custom['especial_2_custom'])
		
		worksheet.write(x,4,u"DENOMINACIÓN",formats_custom['especial_2_custom'])
		worksheet.write(x,5,u"VALOR NOMINAL UNITARIO",formats_custom['especial_2_custom'])
		worksheet.write(x,6,u"CANTIDAD",formats_custom['especial_2_custom'])

		worksheet.write(x,7,u"COSTO TOTAL",formats_custom['especial_2_custom'])
		worksheet.write(x,8,u"PROVISIÓN TOTAL",formats_custom['especial_2_custom'])
		worksheet.write(x,9,u"TOTAL NETO",formats_custom['especial_2_custom'])
		detail = self.env['sunat.table.data.38'].search([('company_id', '=', self.company_id.id),('date', '>=', self.fiscal_year_id.date_from),('date', '<=', self.period_id.date_end)])
		prov_total, total = 0, 0
		x+=1
		for i in detail:
		

			worksheet.write(x,1 (i.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''),formats['especial1'])

			worksheet.write(x,2 (i.partner_id.vat or ''),formats['especial1']) 
			

			worksheet.write(x,3 (i.partner_id.name or ''),formats['especial1']) 
			

			worksheet.write(x,4(i.name or ''),formats['especial1'])
			

			worksheet.write(x,5,'{:,.2f}'.format((i.amount or 0)),formats['numberdos'])
			

			worksheet.write(x,6,'{:,.2f}'.format((i.qty or 0)),formats['numberdos'])
		
			
			worksheet.write(x,7,'{:,.2f}'.format((i.total_cost or 0)),formats['numberdos'])
			
			
			worksheet.write(x,8,'{:,.2f}'.format((i.prov_total or 0)),formats['numberdos'])
		
			prov_total+=(i.prov_total or 0)
			
			worksheet.write(x,9,'{:,.2f}'.format((i.total or 0)),formats['numberdos'])
						
			total+=(i.total or 0)
			x+=1
		worksheet.write(x,7,"TOTALES",formats['especial2'])
		worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % prov_total)),formats['numbertotal'])
		worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)),formats['numbertotal'])
		widths = [8,10,20,54,26,16,17,13,13,16]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'libro_38.xlsx', 'rb')
		return self.env['popup.it'].get_file('Formato 3.8: Valores',base64.encodebytes(b''.join(f.readlines())))
	
	def get_report_3_9(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_9()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_libro_39()	
	
	def get_excel_3_9(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'libro_39.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.9 INTANGIBLES")
		worksheet.set_tab_color('blue')
		decimal_rounding = '%0.2f'
		worksheet.merge_range(2,0,2,8, 'FORMATO 3.9: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA CUENTA 34 - INTANGIBLES""', formats['especial5'] )


		worksheet.write(4,1,"Periodos",formats['especial2'])
		worksheet.write(4,2,self.period_id.fiscal_year_id.name,formats['especial2'])
		worksheet.write(5,1,"RUC:",formats['especial2'])
		worksheet.write(5,2,self.company_id.partner_id.vat,formats['especial2'])
		worksheet.merge_range(6,1,6,6,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + self.company_id.partner_id.name ,formats['especial2'])
		#CABECERAS DEL REPORTE
		formats_custom={}
		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		date_new_format = workbook.add_format({'num_format':'dd-mm-yyyy'})
		date_new_format.set_align('justify')
		date_new_format.set_align('vcenter')
		date_new_format.set_font_size(10)
		date_new_format.set_font_name('Times New Roman')
		formats['date_new_format'] = date_new_format

		x=8
		
		worksheet.write(x,1,"FECHA DE INICIO DE LA OPERACIÓN ",formats_custom['especial_2_custom'])
		worksheet.write(x,2,u"DESCRIPCIÓN DEL INTANGIBLE",formats_custom['especial_2_custom'])
		
		worksheet.write(x,3,u"TIPO DE INTANGIBLE (TABLA 7)",formats_custom['especial_2_custom'])
		worksheet.write(x,4,u"VALOR CONTABLE DEL INTANGIBLE",formats_custom['especial_2_custom'])
		worksheet.write(x,5,u"AMORTIZACIÓN CONTABLE ACUMULADA",formats_custom['especial_2_custom'])

		worksheet.write(x,6,u"VALOR NETO CONTABLE DEL INTANGIBLE",formats_custom['especial_2_custom'])
		detail = self.env['sunat.table.data.39'].search([('company_id', '=', self.company_id.id),('date', '>=', self.fiscal_year_id.date_from),('date', '<=', self.period_id.date_end)])

		amount = amort_acum = total = 0
		x+=1
		for i in detail:
		

			worksheet.write(x,1 (i.date.strftime('%Y/%m/%d') or ''),formats['date_new_format'])

			worksheet.write(x,2 (i.name or ''),formats['especial1']) 
			

			worksheet.write(x,3 (i.type or ''),formats['especial1']) 
			

			worksheet.write(x,4,'{:,.2f}'.format((i.amount or 0)),formats['numberdos'])
			amount += (i.amount or 0)

			worksheet.write(x,5,'{:,.2f}'.format((i.amort_acum or 0)),formats['numberdos'])
			amort_acum += (i.amort_acum or 0)
			
			worksheet.write(x,6,'{:,.2f}'.format((i.total or 0)),formats['numberdos'])
			total += (i.total or 0)
			
			x+=1
		worksheet.write(x,3,"TOTALES",formats['especial2'])
		worksheet.write(x,4,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % amount)),formats['numbertotal'])
		worksheet.write(x,5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % amort_acum)),formats['numbertotal'])
		worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)),formats['numbertotal'])
		
		widths = [8,30,53,17,20,24,17]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'libro_39.xlsx', 'rb')
		return self.env['popup.it'].get_file('Cuenta 34 - Intangibles',base64.encodebytes(b''.join(f.readlines())))
	
	def get_report_3_10(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_10()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cuenta_40()	
	
	def get_excel_3_10(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_40.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.10 Tributos por pagar")
		worksheet.set_tab_color('blue')
		def _get_sql_vst_40(self):
			sql = """
				SELECT
				cuenta,
				nomenclatura,
				debe-haber AS saldo
				FROM get_f1_register('%s','%s',%s,'pen')
				WHERE left(cuenta,2) = '40'
			
			""" % (self.period_id.code[:4]+'00',
				self.period_id.code,
				str(self.company_id.id))

			return sql

		x=2
		worksheet.merge_range(x,0,x,4,'FORMATO 3.10: "LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 40 - TRIBUTOS POR PAGAR"', formats['especial5'])

		x+=2
		
		worksheet.write(x,0,"EJERCICIO",formats['especial2'])
		worksheet.write(x,1,self.period_id.fiscal_year_id.name,formats['especial2'])
		x+=1
		worksheet.write(x,0,"RUC:",formats['especial2'])
		worksheet.write(x,1,self.company_id.partner_id.vat,formats['especial2'])
		x+=1
		worksheet.merge_range(x,0,x,5,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + self.company_id.partner_id.name ,formats['especial2'])

		x+=2
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,0,x,1,"CUENTA Y SUB CUENTA TRIBUTOS POR PAGAR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,2,x+1,2,"SALDO FINAL",formats_custom['especial_2_custom'])		
		x+=1
		worksheet.write(x,0,"CODIGO",formats_custom['especial_2_custom'])
		worksheet.write(x,1,"DENOMINACION",formats_custom['especial_2_custom'])

		self.env.cr.execute(self.env['account.base.sunat'].pdf_get_sql_vst_40(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id))
		res = self.env.cr.dictfetchall()

		x+=1
		saldo = 0

		for i in res:
		
			worksheet.write(x,0,  i['cuenta'] if i['cuenta'] else '',formats['especial1']) 
			

			worksheet.write(x,1, i['nomenclatura'] if i['nomenclatura'] else '',formats['especial1']) 
			

			worksheet.write(x,2,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo'])),formats['numberdos'])
			saldo += i['saldo']
			x+=1
		worksheet.write(x,1,"TOTAL",formats['especial2'])
		worksheet.write(x,2,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo)),formats['numbertotal'])
	
		widths = [22,77,19]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_40.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 40 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))
	
	def get_report_3_11(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_11()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cuenta_41()	
	
	def get_excel_3_11(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_41.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.11 Remuneraciones")
		worksheet.set_tab_color('blue')
		def _get_sql_vst_41(self):
			sql = """
				SELECT
				gs.cuenta,
				aa.name->>'es_PE' AS nomenclatura,
				rp.ref,
				partner,
				td_partner,
				gs.doc_partner,
				SUM(saldo_mn) AS saldo
				FROM get_saldos_sin_cierre('%s','%s',%s) gs
				LEFT JOIN account_account aa ON aa.id = gs.account_id
				LEFT JOIN res_partner rp ON rp.id = gs.partner_id
				WHERE LEFT(gs.cuenta,2) = '41' and gs.saldo_mn <> 0
				GROUP BY gs.cuenta,aa.name->>'es_PE',rp.ref,partner,td_partner,gs.doc_partner
			
			""" % (self.period_id.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period_id.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		x=2
		worksheet.merge_range(x,0,x,4,'LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 41 - REMUNERACIONES POR PAGAR DEL MES DE '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x+1,2,"CUENTA Y SUBCUENTA REMUNERACIONES POR PAGAR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x,6,"TRABAJADOR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"SALDO FINAL",formats_custom['especial_2_custom'])			
		x+=1
		worksheet.merge_range(x,3,x+1,3,"CODIGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+1,4,"APELLIDOS Y NOMBRES",formats_custom['especial_2_custom'])	
		worksheet.merge_range(x,5,x,6,"DOC DE IDENT",formats_custom['especial_2_custom'])			
		x+=1
		worksheet.write(x,1,"CODIGO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"DENOMINACION",formats_custom['especial_2_custom'])
		worksheet.write(x,5,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,6,"NUMERO",formats_custom['especial_2_custom'])

		self.env.cr.execute(_get_sql_vst_41(self))
		res = self.env.cr.dictfetchall()
		x+=1
		saldo = 0

		for i in res:
		
			worksheet.write(x,1,  i['cuenta'] if i['cuenta'] else '',formats['especial1']) 			

			worksheet.write(x,2, i['nomenclatura'] if i['nomenclatura'] else '',formats['especial1']) 

			worksheet.write(x,3, i['ref'] if i['ref'] else '',formats['especial1'])

			worksheet.write(x,4, i['partner'] if i['partner'] else '',formats['especial1']) 

			worksheet.write(x,5, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 

			worksheet.write(x,6, i['doc_partner'] if i['doc_partner'] else '',formats['especial1'])  
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo'])),formats['numberdos'])
			saldo += i['saldo']
			x+=1
		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo)),formats['numbertotal'])
	
		widths = [10,10,30,10,34,8,12,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_41.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 41 - REMUNERACIONES POR PAGAR DEL MES DE '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_12(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_12()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cuenta_42()	
	
	def get_excel_3_12(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_42.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.12 Proveedores")
		worksheet.set_tab_color('blue')
		def _get_sql_vst_42(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos_sin_cierre('%s','%s',%s)
				WHERE LEFT(cuenta,2) = '42' and saldo_mn <> 0
			
			""" % (self.period_id.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period_id.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		x=2
		worksheet.merge_range(x,0,x,4,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 42 - CTAS POR PAGAR COMERCIALES TERCEROS DEL MES DE '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DEL PROVEEDOR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])

		self.env.cr.execute(_get_sql_vst_42(self))
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0
		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: '+ i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1

		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_42.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 42 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_13(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_13()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cuenta_46()	
	
	def get_excel_3_13(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_46.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.13 Cuentas por pagar")
		worksheet.set_tab_color('blue')
		def _get_sql_vst_46(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos_sin_cierre('%s','%s',%s)
				WHERE LEFT(cuenta,2) = '46' and saldo_mn <> 0
			
			""" % (self.period_id.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period_id.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		x=2
		worksheet.merge_range(x,0,x,4,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 46 - CTAS POR PAGAR DIVERSAS TERCEROS DEL MES DE '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DEL PROVEEDOR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])

		self.env.cr.execute(_get_sql_vst_46(self))
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0
		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1

		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_46.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 46 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_14(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_14()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cuenta_47()	
	
	def get_excel_3_14(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_47.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.14 Beneficios")
		worksheet.set_tab_color('blue')
		def _get_sql_vst_47(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos_sin_cierre('%s','%s',%s)
				WHERE LEFT(cuenta,2) = '47' and saldo_mn <> 0
			
			""" % (self.period_id.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period_id.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		x=2
		worksheet.merge_range(x,0,x,4,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 47 - CTAS POR PAGAR DIVERSAS RELACIONADAS DEL MES DE '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DEL PROVEEDOR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])

		self.env.cr.execute(_get_sql_vst_47(self))
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0
		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1

		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_47.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 47 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_15(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_15()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cuenta_49()	
	
	def get_excel_3_15(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_49.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.15 Ganancias")
		worksheet.set_tab_color('blue')
		def _get_sql_vst_49(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos_sin_cierre('%s','%s',%s)
				WHERE LEFT(cuenta,2) = '49' and saldo_mn <> 0 
			
			""" % (self.period_id.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period_id.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		x=2
		worksheet.merge_range(x,0,x,4,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 49 - PASIVO DIFERIDO DEL MES DE '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DEL PROVEEDOR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])

		self.env.cr.execute(_get_sql_vst_49(self))
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0
		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1

		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_49.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 49 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_16(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_16()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cta_50()	
	
	def get_excel_3_16(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta50.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.16 Cuenta 50")
		worksheet.set_tab_color('blue')
		decimal_rounding = '%0.2f'
		capital = self.env['sunat.table.data.031601'].search([('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1)
		
		worksheet.merge_range(2,0,2,8, 'FORMATO 3.16: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA CUENTA 50 - CAPITAL"', formats['especial5'] )
		
		worksheet.write(4,1,"EJERCICIO",formats['especial2'])
		worksheet.write(4,2,self.period_id.fiscal_year_id.name,formats['especial2'])
		worksheet.write(5,1,"RUC:",formats['especial2'])
		worksheet.write(5,2,self.company_id.partner_id.vat,formats['especial2'])
		worksheet.merge_range(6,1,6,6,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + self.company_id.partner_id.name ,formats['especial2'])
		worksheet.merge_range(7,1,7,6,"DETALLE DE LA PARTICIPACIÓN ACCIONARIA O PARTICIPACIONES SOCIALES:",formats['especial2'])
		
		formats_custom = {}
		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom
		x=8

		worksheet.merge_range(x,1,x,3,"CAPITAL SOCIAL O PARTICIPACIONES SOCIALES AL 31.12",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,str(capital.importe_cap),formats_custom['especial_2_custom'])
		x+=1
		worksheet.merge_range(x,1,x,3,"VALOR NOMINAL POR ACCIÓN O PARTICIPACIÓN SOCIAL",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,str(capital.valor_nominal),formats_custom['especial_2_custom'])
		x+=1
		worksheet.merge_range(x,1,x,3,"NÚMERO DE ACCIONES O PARTICIPACIONES SOCIALES SUSCRITAS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,str(capital.nro_acc_sus),formats_custom['especial_2_custom'])
		x+=1
		worksheet.merge_range(x,1,x,3,"NÚMERO DE ACCIONES O PARTICIPACIONES SOCIALES PAGADAS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,str(capital.nro_acc_pag),formats_custom['especial_2_custom'])
		x+=1
		worksheet.merge_range(x,1,x,3,"NÚMERO DE ACCIONISTAS O SOCIOS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,str(len(capital.line_ids)),formats_custom['especial_2_custom'])
		x+=2

		worksheet.merge_range(x,1,x,2,u"DOCUMENTO DE IDENTIDAD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,4,u"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL DEL ACCIONISTA O SOCIO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+1,5,u"SOCIO TIPO DE ACCIONES",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+1,6,u"NÚMERO DE ACCIONES O DE PARTICIPACIONES SOCIALES",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+1,7,u"PORCENTAJE TOTAL DE PARTICIPACION",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO (TABLA 2)",formats_custom['especial_2_custom'])
		worksheet.write(x,2,u"NÚMERO",formats_custom['especial_2_custom'])
		x+1
		num_acciones, percentage = 0, 0
		for i in capital.line_ids:		
			worksheet.write(x,1,(i.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''),formats['especial1'])

			worksheet.write(x,2,(i.partner_id.vat or ''),formats['especial1'])

			worksheet.write(x,3,(i.partner_id.name or ''),formats['especial1'])

			worksheet.write(x,4, (i.tipo or ''),formats['especial1'])
			
			worksheet.write(x,5,(str(i.num_acciones) or ''),formats['especial1'])
			num_acciones += (i.num_acciones or 0)

			worksheet.write(x,6,(str(i.percentage) or ''),formats['especial1'])
			percentage += (i.percentage or 0)

			x+=1
		x+=1	
		worksheet.write(x,5,"TOTAL",formats['especial2'])	
		worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % num_acciones)),formats['numbertotal'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % percentage)),formats['numbertotal'])
		
		widths = [8,15,17,41,38,27,25,17]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta50.xlsx', 'rb')
		return self.env['popup.it'].get_file('Cuenta 50 - Capital',base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_17(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_17()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_inventario_balance()	
	
	def get_excel_3_17(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_3_17.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.17 Balance")
		worksheet.set_tab_color('blue')

		x=2
		worksheet.merge_range(x,0,x,4,'LIBRO INVENTARIO Y BALANCE - BALANCE DE COMPROBACION DEL MES DE '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=2
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,2,"CUENTA Y SUBCUENTA CONTABLE",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x,4,"SALDOS INICIALES",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x,6,"MOVIMIENTOS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x,8,"SALDOS FINALES",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,9,x,10,"SALDOS FINALES DEL BALANCE GENERAL",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,11,x,12,"PERDIDAS FINALES EST. DE PERDIDAS Y GANAN. POR FUNCION",formats_custom['especial_2_custom'])
		x+=1	
		worksheet.write(x,1,"CUENTA",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"DENOMINACION",formats_custom['especial_2_custom'])
		worksheet.write(x,3,"DEUDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,4,"ACREEDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,5,"DEBE",formats_custom['especial_2_custom'])
		worksheet.write(x,6,"HABER",formats_custom['especial_2_custom'])
		worksheet.write(x,7,"DEUDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,8,"ACREEDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,9,"ACTIVO",formats_custom['especial_2_custom'])
		worksheet.write(x,10,"PASIVO",formats_custom['especial_2_custom'])
		worksheet.write(x,11,"PERDIDA",formats_custom['especial_2_custom'])
		worksheet.write(x,12,"GANANCIA",formats_custom['especial_2_custom'])
		self.env.cr.execute(self.env['account.base.sunat'].pdf_get_sql_vst_inventario(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id))
		res = self.env.cr.dictfetchall()
		x+=1	
		debe_inicial, haber_inicial, debe, haber, saldo_deudor, saldo_acreedor, activo, pasivo, perdifun, gananfun = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
		for i in res:

		
			worksheet.write(x,1, i['cuenta'] if i['cuenta'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['nomenclatura'] if i['nomenclatura'] else '',formats['especial1']) 
			

			worksheet.write(x,3,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe_inicial'])),formats['numberdos'] )
			debe_inicial += i['debe_inicial']
			

			worksheet.write(x,4,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber_inicial'])),formats['numberdos'] )
			haber_inicial += i['haber_inicial']
			

			worksheet.write(x,5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])),formats['numberdos'] )
			debe += i['debe']
		

			worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])),formats['numberdos'] )
			haber += i['haber']
		

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_deudor'])),formats['numberdos'] )
			saldo_deudor += i['saldo_deudor']
			

			worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_acreedor'])),formats['numberdos'] )
			saldo_acreedor += i['saldo_acreedor']
		

			worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['activo'])) ,formats['numberdos'])
			activo += i['activo']
			

			worksheet.write(x,10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['pasivo'])) ,formats['numberdos'])
			pasivo += i['pasivo']
		

			worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['perdifun'])) ,formats['numberdos'])
			perdifun += i['perdifun']
			

			worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['gananfun'])) ,formats['numberdos'])
			gananfun += i['gananfun']
			x+=1

		worksheet.write(x,2,'TOTALES:',formats['especial2'])
		worksheet.write(x,3,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe_inicial)),formats['numbertotal'])
		worksheet.write(x,4,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber_inicial)) ,formats['numbertotal'])
		worksheet.write(x,5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)) ,formats['numbertotal'])
		worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)),formats['numbertotal'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_deudor)),formats['numbertotal'])
		worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_acreedor)),formats['numbertotal'])
		worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % activo)),formats['numbertotal'])
		worksheet.write(x,10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % pasivo)),formats['numbertotal'])
		worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % perdifun)),formats['numbertotal'])
		worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % gananfun)),formats['numbertotal'])
		x+=1

		worksheet.write(x,2,'GANANCIA DEL EJERCICIO:',formats['especial2'])
		final_activo = abs(activo - pasivo) if (activo - pasivo) < 0 else 0
		final_pasivo = (activo - pasivo) if (activo - pasivo) > 0 else 0
		worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_activo)) ,formats['numbertotal'])
		worksheet.write(x,10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_pasivo)),formats['numbertotal'])
		final_perdifun = abs(perdifun - gananfun) if (perdifun - gananfun) < 0 else 0
		final_gananfun = (perdifun - gananfun) if (perdifun - gananfun) > 0 else 0
		worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_perdifun)),formats['numbertotal'])
		worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_gananfun)),formats['numbertotal'])
		x+=1
	
		worksheet.write(x,2,'SUMAS IGUALES:',formats['especial2'])

		worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_activo + activo))) ,formats['numbertotal'])
		worksheet.write(x,10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_pasivo + pasivo))) ,formats['numbertotal'])
		worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_perdifun + perdifun))) ,formats['numbertotal'])
		worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_gananfun + gananfun))) ,formats['numbertotal'])
		widths = [10,27,10,10,10,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_3_17.xlsx', 'rb')
		return self.env['popup.it'].get_file(u'Formato 3.17 - Balance de Comprobación.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_18(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_18()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_efective_flow()	

	def get_excel_3_18(self):		
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Flujo_Efectivo.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)		

		####DELETING BORDERS####
		for i in ['especial2','especial1','numberdos','numbertotal']:
			formats[i].set_border(style = 0)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.18 Flujo")
		worksheet.set_tab_color('blue')
		
		x=2
		worksheet.merge_range(x,0,x,4,'FORMATO 3.18: "LIBRO DE INVENTARIOS Y BALANCES - ESTADO DE FLUJOS DE EFECTIVO', formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		formats_custom_1 = {}

		especial_2_custom_1 = workbook.add_format({'bold': True})
		especial_2_custom_1.set_align('center')
		especial_2_custom_1.set_align('vcenter')
		especial_2_custom_1.set_text_wrap()
		especial_2_custom_1.set_font_size(10.5)
		especial_2_custom_1.set_font_name('Times New Roman')
		formats_custom_1['especial_2_custom_1'] = especial_2_custom_1

		ENV_GROUPS = [
			{'name': 'ACTIVIDADES DE OPERACION' ,'code': ['E1','E2'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE OPERACION'},
			{'name': 'ACTIVIDADES DE INVERSION' ,'code': ['E3','E4'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE INVERSION'},
			{'name': 'ACTIVIDADES DE FINANCIAMIENTO' ,'code': ['E5','E6'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE FINANCIAMIENTO'}
		]

		period_aper = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		period_ini = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '01')],limit=1)
		wiz = self.env['efective.flow.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_ini':period_aper.id,'period_from':period_ini.id,'period_to':self.period_id.id})
		wiz._get_efective_flow_sql()
		
		worksheet.write(x,1,"ACTIVIDADES",formats_custom_1['especial_2_custom_1'])
		x+=1
		for group in ENV_GROUPS:
			currents_positive = self.env['efective.flow'].search([('efective_group','=',group['code'][0])])
			worksheet.write(x, 1, group['name'], formats['especial2'])
			total = 0
			x += 1
			for current in currents_positive:
				worksheet.write(x, 1, current.name if current.name else '', formats['especial1'])
				worksheet.write(x, 2, current.total if current.total else '0.00', formats['numberdos'])
				total += current.total
				x += 1
			currents_negative = self.env['efective.flow'].search([('efective_group','=',group['code'][1])])
			worksheet.write(x, 1, 'Menos:', formats['especial2'])
			x += 1
			for current in currents_negative:
				worksheet.write(x, 1, current.name if current.name else '', formats['especial1'])
				worksheet.write(x, 2, current.total if current.total else '0.00', formats['numberdos'])
				total += current.total
				x += 1
			worksheet.write(x, 1, group['total_name'], formats['especial2'])
			worksheet.write(x, 2, total, formats['numbertotal'])
			x += 2
		efective_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6'])]).mapped('total')
		worksheet.write(x, 1, 'AUMENTOS (DISM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO', formats['especial2'])
		worksheet.write(x, 2, sum(efective_equivalent), formats['numbertotal'])
		x += 1
		currents = self.env['efective.flow'].search([('efective_group','in',['E7','E8'])],order='efective_order')
		for current in currents:
			worksheet.write(x, 1, current.name if current.name else '',formats['especial2'])
			worksheet.write(x, 2, current.total if current.total else '0.00',formats['numbertotal'])
			x += 1
		final_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6','E7','E8'])]).mapped('total')
		worksheet.write(x, 1, 'SALDO AL FINALIZAR DE EFECTIVO Y EQUIVALENTE DE EFECTIVO AL FINALIZAR EL EJERCICIO', formats['especial2'])
		worksheet.write(x, 2, sum(final_equivalent), formats['numbertotal'])
		
		
		widths = [10,132,16]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Flujo_Efectivo.xlsx', 'rb')
		return self.env['popup.it'].get_file('Formato 3.18 - Estados de Flujo de Efectivo.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_19(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_19()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_patrimony_net()	

	def get_excel_3_19(self):		
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Patrimonio_Neto.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)		

		####DELETING BORDERS####
		for i in ['especial2','especial1','numberdos','numbertotal']:
			formats[i].set_border(style = 0)
		
		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"FORMATO 3.19 Patrimonio")
		worksheet.set_tab_color('blue')
		
		x=2
		worksheet.merge_range(x,0,x,4,'FORMATO 3.19 : "LIBRO DE INVENTARIOS Y BALANCES - ESTADO DE CAMBIOS EN EL PATRIMONIO NETO DEL 01.01 AL %s"'%(self.period_id.date_end.strftime('%d.%m')), formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=2

		period_aper = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		wiz = self.env['net.patrimony.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_from':period_aper.id,'period_to':self.period_id.id})
		self.env.cr.execute(wiz._get_net_patrimony_sql())
		data = self._cr.dictfetchall()
		HEADERS = ['CONCEPTOS','CAPITAL','ACCIONES DE INVERSION','CAPITAL ADICIONAL','RESULTADOS NO REALIZADOS',
		'EXCEDENTE DE REVALUACION','RESERVAS','RESULTADOS ACUMULADOS','TOTALES']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,x,1,especial_2_custom)

		x+=1

		capital, acciones, cap_add, res_no_real, exce_de_rev, reservas, res_ac, total = 0, 0, 0, 0, 0, 0, 0, 0

		for line in data:
			worksheet.write(x,1,line['glosa'] if line['glosa'] else '',formats['especial1'])
			worksheet.write(x,2,line['capital'] if line['capital']  else '0.00',formats['numberdos'])
			worksheet.write(x,3,line['acciones'] if line['acciones']  else '0.00',formats['numberdos'])
			worksheet.write(x,4,line['cap_add'] if line['cap_add'] else '0.00',formats['numberdos'])
			worksheet.write(x,5,line['res_no_real'] if line['res_no_real'] else '0.00',formats['numberdos'])
			worksheet.write(x,6,line['exce_de_rev'] if line['exce_de_rev'] else '0.00',formats['numberdos'])
			worksheet.write(x,7,line['reservas'] if line['reservas'] else '0.00',formats['numberdos'])
			worksheet.write(x,8,line['res_ac'] if line['res_ac'] else '0.00',formats['numberdos'])
			worksheet.write(x,9,line['total'] if line['total'] else '0.00',formats['numbertotal'])

			capital +=line['capital'] if line['capital'] else 0
			acciones +=line['acciones'] if line['acciones'] else 0
			cap_add +=line['cap_add'] if line['cap_add'] else 0
			res_no_real +=line['res_no_real'] if line['res_no_real'] else 0
			exce_de_rev +=line['exce_de_rev'] if line['exce_de_rev'] else 0
			reservas +=line['reservas'] if line['reservas'] else 0
			res_ac +=line['res_ac'] if line['res_ac'] else 0
			total +=line['total'] if line['total'] else 0

			x += 1

		worksheet.write(x,1,'TOTALES',especial_2_custom)
		worksheet.write(x,2,capital,formats['numbertotal'])
		worksheet.write(x,3,acciones,formats['numbertotal'])
		worksheet.write(x,4,cap_add,formats['numbertotal'])
		worksheet.write(x,5,res_no_real,formats['numbertotal'])
		worksheet.write(x,6,exce_de_rev,formats['numbertotal'])
		worksheet.write(x,7,reservas,formats['numbertotal'])
		worksheet.write(x,8,res_ac,formats['numbertotal'])
		worksheet.write(x,9,total,formats['numbertotal'])

		widths = [10,57,19,19,19,19,19,19,19,19]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Patrimonio_Neto.xlsx', 'rb')
		return self.env['popup.it'].get_file('Formato 3.19 - Estado de cambios en Patrimonio Neto.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def get_report_3_20(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_20()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_function_result()	
	
	def get_excel_3_20(self):		
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Resultado_por_Funcion.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)		

		####DELETING BORDERS####
		for i in ['especial2','especial1','numberdos','numbertotal']:
			formats[i].set_border(style = 0)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"FORMATO 3.20 FUNCIÓN")
		worksheet.set_tab_color('blue')
		
		x=2
		worksheet.merge_range(x,0,x,4,'FORMATO 3.20: "LIBRO DE INVENTARIOS Y BALANCES - ESTADO DE GANANCIAS Y PÉRDIDAS POR FUNCIÓN DEL 01.01 AL %s"'%(self.period_id.date_end.strftime('%d.%m')), formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=2
		
		ENV_GROUPS = [
			{'name': 'INGRESOS BRUTOS' ,'code': 'F1'},
			{'name': 'COSTOS OPERACIONALES' ,'code': 'F2'},
			{'name': 'UTILIDAD OPERATIVA' ,'code': 'F3'},
			{'name': 'RESULTADOS ANTES DE PARTICIPACIONES E IMPUESTOS' , 'code': 'F4'},
			{'name': 'UTILIDAD (PERDIDA) NETA ACT CONTINUAS', 'code': 'F5'},
			{'name': 'UTILIDAD (PERDIDA) NETA DEL EJERCICIO', 'code': 'F6'}
		]
		
		TOTALS = self.get_totals(ENV_GROUPS)
		GROUPS = self.get_function_totals(ENV_GROUPS,TOTALS)

		period_aper = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		wiz = self.env['function.result.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_from':period_aper.id,'period_to':self.period_id.id})
		self._cr.execute(wiz._get_function_result_sql())
		
		total_F1, total_F2 = 0, 0
		for group in GROUPS:
			total_F1 += group['total'] if group['code'] == 'F1' else 0
			total_F2 += group['total'] if group['code'] == 'F2' else 0
			currents = self.env['function.result'].search([('group_function','=',group['code'])])
			for current in currents:
				worksheet.write(x, 1, current.name if current.name else '', formats['especial1'])
				worksheet.write(x, 2, (-1.0 * current.total) if current.total else '0.00', formats['numberdos'])
				x += 1
			if group['code'] == 'F2':
				worksheet.write(x, 1, group['name'], formats['especial2'])
				worksheet.write(x, 2, group['total'], formats['numbertotal'])
				x += 2
				worksheet.write(x, 1, 'UTILIDAD BRUTA', formats['especial2'])
				worksheet.write(x, 2, total_F1 + total_F2, formats['numbertotal'])
				x += 2
			else:
				worksheet.write(x, 1, group['name'], formats['especial2'])
				worksheet.write(x, 2, group['total'], formats['numbertotal'])
				x += 2

		widths = [10,60,16]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Resultado_por_Funcion.xlsx', 'rb')
		return self.env['popup.it'].get_file('Formato 3.20 - Estado de Ganancias y Perdidas por Funcion.xlsx',base64.encodebytes(b''.join(f.readlines())))
	
	def get_totals(self,groups):
		TOTALS = []
		for group in groups:
			currents = self.env['function.result'].search([('group_function','=',group['code'])]).mapped('total')
			total = {'sum': -1.0 * sum(currents), 'code': group['code']}
			TOTALS.append(total)
		return TOTALS
		
	def get_function_totals(self,groups,totals):
		def get_sum_group(code):
			return next(filter(lambda t: t['code'] == code, totals))['sum']
		####Totals#####
		next(filter(lambda g: g['code'] == 'F1', groups))['total'] = get_sum_group('F1')
		next(filter(lambda g: g['code'] == 'F2', groups))['total'] = get_sum_group('F2')
		operative_utility = get_sum_group('F1') + get_sum_group('F2')
		next(filter(lambda g: g['code'] == 'F3', groups))['total'] = operative_utility + get_sum_group('F3')
		tax_result = operative_utility + get_sum_group('F3') + get_sum_group('F4')
		next(filter(lambda g: g['code'] == 'F4', groups))['total'] = tax_result
		continue_utility = tax_result + get_sum_group('F5')
		next(filter(lambda g: g['code'] == 'F5', groups))['total'] = continue_utility
		continue_excercise = continue_utility + get_sum_group('F6')
		next(filter(lambda g: g['code'] == 'F6', groups))['total'] = continue_excercise
		return groups
	
	def get_pdf_cta_50(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths,capital):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, 'FORMATO 3.16: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA CUENTA 50 - CAPITAL"')
			c.setFont("Helvetica-Bold", 10)
			c.drawString(50,hReal-20, 'EJERCICIO: %s'%self.fiscal_year_id.name)
			c.drawString(50,hReal-35, 'RUC: %s'%self.company_id.partner_id.vat)
			c.drawString(50,hReal-50, 'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s'%self.company_id.partner_id.name)

			c.setFont("Helvetica-Bold", 9)
			c.drawString(50,hReal-70, 'DETALLE DE LA PARTICIPACIÓN ACCIONARIA O PARTICIPACIONES SOCIALES:')

			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=9><b>CAPITAL SOCIAL O PARTICIPACIONES SOCIALES AL 31.12</b></font>",style), Paragraph("<font size=9><b>%s</b></font>"%str(capital.importe_cap),style)],
	  			[Paragraph("<font size=9><b>VALOR NOMINAL POR ACCIÓN O PARTICIPACIÓN SOCIAL</b></font>",style), Paragraph("<font size=9><b>%s</b></font>"%str(capital.valor_nominal),style)],
				[Paragraph("<font size=9><b>NÚMERO DE ACCIONES O PARTICIPACIONES SOCIALES SUSCRITAS  </b></font>",style), Paragraph("<font size=9><b>%s</b></font>"%str(capital.nro_acc_sus),style)],
				[Paragraph("<font size=9><b>NÚMERO DE ACCIONES O PARTICIPACIONES SOCIALES PAGADAS</b></font>",style), Paragraph("<font size=9><b>%s</b></font>"%str(capital.nro_acc_pag),style)],
				[Paragraph("<font size=9><b>NÚMERO DE ACCIONISTAS O SOCIOS</b></font>",style), Paragraph("<font size=9><b>%s</b></font>"%str(len(capital.line_ids)),style)]]
			
			t=Table(data,colWidths=[320,320], rowHeights=[18,18,18,18,18])
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,50,500) 
			t.drawOn(c,50,hReal-170)

			data= [[Paragraph("<font size=7.5><b>DOCUMENTO DE IDENTIDAD</b></font>",style), 
				'',
				Paragraph("<font size=7.5><b>APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL DEL ACCIONISTA O SOCIO</b></font>",style), 
				Paragraph("<font size=7.5><b>TIPO DE ACCIONES</b></font>",style),
				Paragraph("<font size=7.5><b>NÚMERO DE ACCIONES O DE PARTICIPACIONES SOCIALES</b></font>",style),
				Paragraph("<font size=7.5><b>PORCENTAJE TOTAL DE PARTICIPACION</b></font>",style)],
				[Paragraph("<font size=7.5><b>TIPO (TABLA 2)</b></font>",style),
				Paragraph("<font size=7.5><b>NÚMERO</b></font>",style),'','','','']]
			
			t=Table(data,colWidths=size_widths, rowHeights=[18,30])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,0)),
				('SPAN',(2,0),(2,1)),
				('SPAN',(3,0),(3,1)),
				('SPAN',(4,0),(4,1)),
				('SPAN',(5,0),(5,1)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,50,500) 
			t.drawOn(c,50,hReal-235)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths,capital):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths,capital)
				return pagina+1,hReal-245
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "banco_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-245
		pagina = 1

		size_widths = [60,110,300,80,100,80] #770
		capital = self.env['sunat.table.data.031601'].search([('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1)

		pdf_header(self,c,wReal,hReal,size_widths,capital)

		c.setFont("Helvetica", 7)

		num_acciones, percentage = 0, 0

		for i in capital.line_ids:
			first_pos = 50

			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''),50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.vat or ''),50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.name or ''),250) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.tipo or ''),50) )
			first_pos += size_widths[3]

			c.drawRightString( first_pos+size_widths[4] ,pos_inicial,particionar_text( (str(i.num_acciones) or ''),130) )
			first_pos += size_widths[4]
			num_acciones += (i.num_acciones or 0)

			c.drawRightString( first_pos+size_widths[5] ,pos_inicial,particionar_text( (str(i.percentage) or ''),120) )
			percentage += (i.percentage or 0)

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths,capital)
		
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,5,pagina,size_widths,capital)

		c.setFont("Helvetica-Bold", 7)
		c.line(600,pos_inicial,780,pos_inicial)
		c.drawString( 550 ,pos_inicial-10,'TOTALES:')
		c.drawRightString( 700,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % num_acciones)) )
		c.drawRightString( 780 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % percentage)))
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths,capital)
		c.setFont("Helvetica-Bold", 7)

		c.line(600,pos_inicial,780,pos_inicial)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('Cuenta 50 - Capital',base64.encodebytes(b''.join(f.readlines())))
	
	def get_pdf_efective_flow(self):
		period_aper = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		period_ini = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '01')],limit=1)
		wiz = self.env['efective.flow.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_ini':period_aper.id,'period_from':period_ini.id,'period_to':self.period_id.id})
		wiz._get_efective_flow_sql()
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		doc = SimpleDocTemplate(direccion + 'Flujo_Efectivo.pdf',pagesize=letter)
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		decimal_rounding = '%0.2f'
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		top_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
					 ('VALIGN', (0, 0), (-1, -1), 'TOP')]
		internal_width = [12*cm,2.5*cm]
		internal_height = [1*cm]
		spacer = Spacer(10, 20)

		elements.append(Paragraph('<strong>FORMATO 3.18: "LIBRO DE INVENTARIOS Y BALANCES - ESTADO DE FLUJOS DE EFECTIVO"</strong>', style_title))
		elements.append(Spacer(20, 10))
		elements.append(Paragraph('<strong>           EJERCICIO: %s</strong>'%(self.period_id.fiscal_year_id.name), style_left))
		elements.append(Spacer(10, 5))
		elements.append(Paragraph('<strong>RUC: %s</strong>'%(self.company_id.partner_id.vat), style_left))
		elements.append(Spacer(10, 5))
		elements.append(Paragraph(u'<strong>APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s</strong>'%(self.company_id.partner_id.name), style_left))
		elements.append(Spacer(10, 10))

		ENV_GROUPS = [
			{'name': 'ACTIVIDADES DE OPERACION' ,'code': ['E1','E2'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE OPERACION'},
			{'name': 'ACTIVIDADES DE INVERSION' ,'code': ['E3','E4'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE INVERSION'},
			{'name': 'ACTIVIDADES DE FINANCIAMIENTO' ,'code': ['E5','E6'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE FINANCIAMIENTO'}
		]

		period_c = self.period_id.code

		t = Table([
			[Paragraph('<strong>ACTIVIDADES</strong>', style_cell), 
			Paragraph('<strong>%s</strong>' % str(period_c[4:]+'-'+period_c[:4]), style_right)]
			], internal_width, internal_height)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)
		elements.append(Spacer(10, 10))
		
		for group in ENV_GROUPS:
			data, y, total = [], 0, 0
			currents_positive = self.env['efective.flow'].search([('efective_group','=',group['code'][0])])
			data.append([Paragraph('<strong>%s</strong>' % group['name'], style_left)])
			y += 1
			for current in currents_positive:
				data.append([Paragraph(current.name if current.name else '', style_left),
							 Paragraph(str(decimal_rounding % current.total) if current.total else '0.00', style_right)])
				total += current.total
				y += 1
			currents_negative = self.env['efective.flow'].search([('efective_group','=',group['code'][1])])
			data.append([Paragraph('<strong>Menos:</strong>', style_left),''])
			y += 1
			for current in currents_negative:
				data.append([Paragraph(current.name if current.name else '', style_left),
							 Paragraph(str(decimal_rounding % current.total) if current.total else '0.00', style_right)])
				total += current.total
				y += 1
			data.append([Paragraph('<strong>%s</strong>' % group['total_name'], style_left),
						 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total), style_right)])
			y += 1
			t = Table(data, internal_width, y*internal_height)
			t.setStyle(TableStyle(simple_style))
			elements.append(t)
			elements.append(spacer)
		efective_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6'])]).mapped('total')
		t = Table([
			[Paragraph('<strong>AUMENTOS (DISM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO</strong>', style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % sum(efective_equivalent)), style_right)]
		], internal_width, internal_height)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		currents = self.env['efective.flow'].search([('efective_group','in',['E7','E8'])],order='efective_order')
		
		data, y = [], 0
		for current in currents:
			data.append([Paragraph(current.name, style_left),
						 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % current.total), style_right)])
			y += 1
			
		if data:
			t = Table(data, internal_width, y*internal_height)
			t.setStyle(TableStyle(simple_style))
			elements.append(t)

		final_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6','E7','E8'])]).mapped('total')
		t = Table([
			[Paragraph('<strong>%s</strong>' % 'SALDO AL FINALIZAR DE EFECTIVO Y EQUIVALENTE DE EFECTIVO AL FINALIZAR EL EJERCICIO', style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % sum(final_equivalent)), style_right)]
			], internal_width, internal_height)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		doc.build(elements)

		f = open(direccion +'Flujo_Efectivo.pdf', 'rb')
		return self.env['popup.it'].get_file('Formato 3.18 - Estados de Flujo de Efectivo.pdf',base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_patrimony_net(self):
		#CREANDO ARCHIVO PDF
		period_aper = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		wiz = self.env['net.patrimony.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_from':period_aper.id,'period_to':self.period_id.id})

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		name_file = "Patrimonio_Neto.pdf"
	
		archivo_pdf = SimpleDocTemplate(str(direccion)+name_file, pagesize=(2200,1000), rightMargin=30,leftMargin=30, topMargin=30,bottomMargin=18)

		elements = []
		#Estilos 
		style_left_bold = ParagraphStyle(name = 'Right',alignment = TA_RIGHT, fontSize = 19, fontName="Helvetica-Bold" )
		style_form = ParagraphStyle(name='Justify', alignment=TA_CENTER , fontSize = 25, fontName="Helvetica-Bold" )
		style_left = ParagraphStyle(name = 'Left', alignment=TA_LEFT, fontSize=19, fontName="Helvetica")
		style_left_cell = ParagraphStyle(name = 'Left', alignment=TA_LEFT, fontSize=15, fontName="Helvetica")
		style_right = ParagraphStyle(name = 'Right', alignment=TA_RIGHT, fontSize=19, fontName="Helvetica")
		style_title_tab = ParagraphStyle(name = 'Center',alignment = TA_CENTER, leading = 25, fontSize = 20, fontName="Helvetica-Bold" )
		

		company = self.company_id
		elements.append(Paragraph('FORMATO 3.19 : "LIBRO DE INVENTARIOS Y BALANCES - ESTADO DE CAMBIOS EN EL PATRIMONIO NETO DEL 01.01 AL %s"'%(self.period_id.date_end.strftime('%d.%m')), style_form))
		elements.append(Spacer(20, 15))
		elements.append(Paragraph('<strong>EJERCICIO: %s</strong>'%(self.period_id.fiscal_year_id.name), style_left))
		elements.append(Spacer(10, 15))
		elements.append(Paragraph('<strong>RUC: %s</strong>'%(self.company_id.partner_id.vat), style_left))
		elements.append(Spacer(10, 15))
		elements.append(Paragraph(u'<strong>APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s</strong>'%(self.company_id.partner_id.name), style_left))
		elements.append(Spacer(10, 20))


	#Crear Tabla
		headers = ['CUENTAS PATRIMONIALES','CAPITAL','ACCIONES DE INVERSION','CAPITAL ADICIONAL','RESULTADOS NO REALIZADOS',
		'EXCEDENTE DE REVALUACION','RESERVAS','RESULTADOS ACUMULADOS','TOTAL']

		datos = []
		datos.append([])

		for i in headers:
			datos[0].append(Paragraph(i,style_title_tab))

		x = 1
		capital, acciones, cap_add, res_no_real, exce_de_rev, reservas, res_ac, total = 0, 0, 0, 0, 0, 0, 0, 0

		self._cr.execute(wiz._get_net_patrimony_sql())
		data = self._cr.dictfetchall()

		for fila in data:
			datos.append([])
			datos[x].append(Paragraph((fila['glosa']) if fila['glosa'] else '',style_left_cell))
			datos[x].append(Paragraph(str(fila['capital']) if fila['capital'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['acciones']) if fila['acciones'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['cap_add']) if fila['cap_add'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['res_no_real']) if fila['res_no_real'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['exce_de_rev']) if fila['exce_de_rev'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['reservas']) if fila['reservas'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['res_ac']) if fila['res_ac'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['total']) if fila['total'] else '0.00',style_left_bold))

			capital += fila['capital'] if fila['capital'] else 0
			acciones += fila['acciones'] if fila['acciones'] else 0
			cap_add += fila['cap_add'] if fila['cap_add'] else 0
			res_no_real += fila['res_no_real'] if fila['res_no_real'] else 0
			exce_de_rev += fila['exce_de_rev'] if fila['exce_de_rev'] else 0
			reservas += fila['reservas'] if fila['reservas'] else 0
			res_ac += fila['res_ac'] if fila['res_ac'] else 0
			total += fila['total'] if fila['total'] else 0

			x += 1
		
		datos.append([])
		datos[x].append(Paragraph('TOTALES',style_title_tab))
		datos[x].append(Paragraph(str(round(capital,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(acciones,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(cap_add,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(res_no_real,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(exce_de_rev,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(reservas,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(res_ac,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(total,2)),style_left_bold))

		table_datos = Table(datos, colWidths=[20*cm,7*cm,7*cm,7*cm,7*cm,7*cm,7*cm,7*cm,7*cm],rowHeights=[2.5*cm] + x * [2*cm])

		#color_cab = colors.Color(red=(220/255),green=(230/255),blue=(241/255))

		#Estilo de Tabla
		style_table = TableStyle([
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (0,0), (-1,-1), 0.25, colors.black), 
				('BOX', (0,0), (-1,-1), 0.25, colors.black),
			])
		table_datos.setStyle(style_table)

		elements.append(table_datos)

		#Build
		archivo_pdf.build(elements)

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)
		import os

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('Formato 3.19 - Estado de cambios en Patrimonio Neto.pdf',base64.encodebytes(b''.join(f.readlines())))
	
	def get_pdf_function_result(self):
		period_aper = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		wiz = self.env['function.result.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_from':period_aper.id,'period_to':self.period_id.id})
		self._cr.execute(wiz._get_function_result_sql())
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		doc = SimpleDocTemplate(direccion + 'Resultado_por_Funcion.pdf',pagesize=letter)
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		decimal_rounding = '%0.2f'
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		top_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
					 ('VALIGN', (0, 0), (-1, -1), 'TOP')]
		internal_width = [11*cm,2.5*cm]
		internal_height = [0.5*cm]
		spacer = Spacer(10, 20)

		elements.append(Paragraph('<strong>FORMATO 3.20: "LIBRO DE INVENTARIOS Y BALANCES - ESTADO DE GANANCIAS Y PÉRDIDAS POR FUNCIÓN DEL 01.01 AL 31.12</strong>', style_title))
		elements.append(Spacer(20, 10))
		elements.append(Paragraph('<strong>EJERCICIO: %s</strong>'%(self.period_id.fiscal_year_id.name), style_left))
		elements.append(Spacer(10, 5))
		elements.append(Paragraph('<strong>RUC: %s</strong>'%(self.company_id.partner_id.vat), style_left))
		elements.append(Spacer(10, 5))
		elements.append(Paragraph(u'<strong>APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s</strong>'%(self.company_id.partner_id.name), style_left))
		elements.append(Spacer(10, 10))

		ENV_GROUPS = [
			{'name': 'INGRESOS BRUTOS' ,'code': 'F1'},
			{'name': 'COSTOS OPERACIONALES' ,'code': 'F2'},
			{'name': 'UTILIDAD OPERATIVA' ,'code': 'F3'},
			{'name': 'RESULTADOS ANTES DE PARTICIPACIONES E IMPUESTOS' , 'code': 'F4'},
			{'name': 'UTILIDAD (PERDIDA) NETA ACT CONTINUAS', 'code': 'F5'},
			{'name': 'UTILIDAD (PERDIDA) NETA DEL EJERCICIO', 'code': 'F6'}
		]

		period_c = self.period_id.code

		t = Table([
			[Paragraph(u'<strong>DESCRIPCIÓN</strong>', style_cell), 
			Paragraph('<strong>%s</strong>' % str(period_c[4:]+'-'+period_c[:4]), style_right)]
			], internal_width, internal_height)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)
		elements.append(Spacer(10, 10))

		TOTALS = wiz.get_totals(ENV_GROUPS)
		GROUPS = wiz.get_function_totals(ENV_GROUPS,TOTALS)

		data, y = [], 0
		total_F1, total_F2 = 0, 0
		for group in GROUPS:
			total_F1 += group['total'] if group['code'] == 'F1' else 0
			total_F2 += group['total'] if group['code'] == 'F2' else 0
			currents = self.env['function.result'].search([('group_function','=',group['code'])])
			for current in currents:
				data.append([Paragraph(current.name if current.name else '', style_left),
							 Paragraph(str(decimal_rounding % (-1.0 * current.total)) if current.total else '0.00', style_right)])
				y += 1
			if group['code'] == 'F2':
				data.append([Paragraph('<strong>%s</strong>' % group['name'], style_left),
							 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % group['total']), style_right)])
				y += 1
				t = Table(data, internal_width, y*internal_height)
				t.setStyle(TableStyle(simple_style))
				elements.append(t)
				elements.append(spacer)
				data, y = [], 0

				data.append([Paragraph('<strong>%s</strong>' % 'UTILIDAD BRUTA', style_left),
							 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % (total_F1 + total_F2)), style_right)])
				y += 1
				t = Table(data, internal_width, y*internal_height)
				t.setStyle(TableStyle(simple_style))
				elements.append(t)
				elements.append(spacer)
				data, y = [], 0
			else:
				data.append([Paragraph('<strong>%s</strong>' % group['name'], style_left),
							 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % group['total']), style_right)])
				y += 1
				t = Table(data, internal_width, y*internal_height)
				t.setStyle(TableStyle(simple_style))
				elements.append(t)
				elements.append(spacer)
				data, y = [], 0

		doc.build(elements)

		f = open(direccion +'Resultado_por_Funcion.pdf', 'rb')
		return self.env['popup.it'].get_file('Formato 3.20 - Estado de Ganancias y Perdidas por Funcion.pdf',base64.encodebytes(b''.join(f.readlines())))
	
	def get_pdf_libro_37(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, 'FORMATO 3.7: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA ')
			c.drawCentredString((wReal/2)+20,hReal-18, 'CUENTA 20 - MERCADERIAS Y LA CUENTA 21 - PRODUCTOS TERMINADOS"')
			c.setFont("Helvetica-Bold", 10)
			c.drawString(50,hReal-35, 'EJERCICIO: %s'%self.fiscal_year_id.name)
			c.drawString(50,hReal-50, 'RUC: %s'%self.company_id.partner_id.vat)
			c.drawString(50,hReal-65, 'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s'%self.company_id.partner_id.name)
			c.drawString(50,hReal-80, u'MÉTODO DE EVALUACIÓN APLICADO: ')

			c.setFont("Helvetica-Bold", 9)

			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=7.5><b>CODIGO DE LA EXISTENCIA</b></font>",style), 
				Paragraph("<font size=7.5><b>TIPO DE EXISTENCIA (TABLA 5)</b></font>",style), 
				Paragraph(u"<font size=7.5><b>DESCRIPCIÓN</b></font>",style), 
				Paragraph(u"<font size=7.5><b>CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6)</b></font>",style),
				Paragraph("<font size=7.5><b>CANTIDAD</b></font>",style),
				Paragraph("<font size=7.5><b>COSTO UNITARIO</b></font>",style),
				Paragraph("<font size=7.5><b>COSTO TOTAL</b></font>",style)]]
			
			t=Table(data,colWidths=size_widths, rowHeights=[30])
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,50,500) 
			t.drawOn(c,50,hReal-120)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "libro_37.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-120
		pagina = 1

		size_widths = [60,70,260,80,100,80,80] #770
		###DESDE AQUI
		#capital = self.env['sunat.table.data.031601'].search([('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1)

		pdf_header(self,c,wReal,hReal,size_widths)

		c.setFont("Helvetica", 7)

		#for i in capital.line_ids:
		#	first_pos = 50

		#	c.setFont("Helvetica", 7)
		#	c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''),50) )
		#	first_pos += size_widths[0]

		#	c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.vat or ''),50) )
		#	first_pos += size_widths[1]

		#	c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.name or ''),250) )
		#	first_pos += size_widths[2]

		#	c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.tipo or ''),50) )
		#	first_pos += size_widths[3]

		#	c.drawRightString( first_pos+size_widths[4] ,pos_inicial,particionar_text( (str(i.num_acciones) or ''),130) )
		#	first_pos += size_widths[4]
		#	num_acciones += (i.num_acciones or 0)

		#	c.drawRightString( first_pos+size_widths[5] ,pos_inicial,particionar_text( (str(i.percentage) or ''),120) )
		#	percentage += (i.percentage or 0)

		#	pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,5,pagina,size_widths)

		c.setFont("Helvetica-Bold", 8)
		c.drawString( 600 ,pos_inicial-10,'COSTO TOTAL GENERAL:')
		c.drawRightString( 740,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % 0)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('Cuenta 20 - Mercaderias',base64.encodebytes(b''.join(f.readlines())))
	
	def get_pdf_libro_39(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, 'FORMATO 3.9: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA ')
			c.drawCentredString((wReal/2)+20,hReal-18, 'LA CUENTA 34 - INTANGIBLES"')
			c.setFont("Helvetica-Bold", 10)
			c.drawString(50,hReal-35, 'EJERCICIO: %s'%self.fiscal_year_id.name)
			c.drawString(50,hReal-50, 'RUC: %s'%self.company_id.partner_id.vat)
			c.drawString(50,hReal-65, 'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s'%self.company_id.partner_id.name)

			c.setFont("Helvetica-Bold", 9)

			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph(u"<font size=8><b>FECHA DE INICIO DE LA OPERACIÓN</b></font>",style), 
				Paragraph(u"<font size=8><b>DESCRIPCIÓN DEL INTANGIBLE</b></font>",style), 
				Paragraph("<font size=8><b>TIPO DE INTANGIBLE (TABLA 7)</b></font>",style), 
				Paragraph(u"<font size=8><b>VALOR CONTABLE DEL INTANGIBLE</b></font>",style),
				Paragraph("<font size=8><b>AMORTIZACIÓN CONTABLE ACUMULADA</b></font>",style),
				Paragraph("<font size=8><b>VALOR NETO CONTABLE DEL INTANGIBLE</b></font>",style)]]
			
			t=Table(data,colWidths=size_widths, rowHeights=[30])
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,50,500) 
			t.drawOn(c,50,hReal-105)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "libro_39.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-120
		pagina = 1

		size_widths = [100,300,70,80,100,80] #770
		
		detail = self.env['sunat.table.data.39'].search([('company_id', '=', self.company_id.id),('date', '>=', self.fiscal_year_id.date_from),('date', '<=', self.period_id.date_end)])

		pdf_header(self,c,wReal,hReal,size_widths)

		amount = amort_acum = total = 0

		for i in detail:
			first_pos = 50

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,i.date.strftime('%Y/%m/%d'))
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.name or ''),280) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.type or ''),100) )
			first_pos += size_widths[2]

			c.drawRightString( first_pos+size_widths[3]-2 ,pos_inicial,'{:,.2f}'.format((i.amount or 0)) )
			first_pos += size_widths[3]
			amount += (i.amount or 0)

			c.drawRightString( first_pos+size_widths[4]-2,pos_inicial,'{:,.2f}'.format((i.amort_acum or 0)) )
			first_pos += size_widths[4]
			amort_acum += (i.amort_acum or 0)

			c.drawRightString( first_pos+size_widths[5]-2,pos_inicial,'{:,.2f}'.format((i.total or 0)) )
			first_pos += size_widths[5]
			total += (i.total or 0)

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,15,pagina,size_widths)

		c.setFont("Helvetica-Bold", 8)
		c.drawString( 450 ,pos_inicial,'TOTALES')
		c.drawRightString( 598,pos_inicial,'{:,.2f}'.format(amount) )
		c.drawRightString( 698,pos_inicial,'{:,.2f}'.format(amort_acum) )
		c.drawRightString( 778,pos_inicial,'{:,.2f}'.format(total) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('Cuenta 34 - Intangibles',base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_38(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, 'FORMATO 3.8: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA ')
			c.drawCentredString((wReal/2)+20,hReal-18, 'LA CUENTA 31 - VALORES"')
			c.setFont("Helvetica-Bold", 10)
			c.drawString(50,hReal-35, 'EJERCICIO: %s'%self.fiscal_year_id.name)
			c.drawString(50,hReal-50, 'RUC: %s'%self.company_id.partner_id.vat)
			c.drawString(50,hReal-65, 'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s'%self.company_id.partner_id.name)

			c.setFont("Helvetica-Bold", 9)

			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL DEL ACCIONISTA O SOCIO</b></font>",style), 
				Paragraph("<font size=8><b>TITULO</b></font>",style),'','',
				Paragraph("<font size=8><b>VALOR EN LIBROS</b></font>",style),'',''],
				[Paragraph("<font size=8><b>TIPO (TABLA 2)</b></font>",style),
				Paragraph("<font size=8><b>NÚMERO</b></font>",style),'',
				Paragraph("<font size=8><b>DENOMINACIÓN</b></font>",style),
				Paragraph("<font size=8><b>VALOR NOMINAL UNITARIO</b></font>",style),
				Paragraph("<font size=8><b>CANTIDAD</b></font>",style),
				Paragraph("<font size=8><b>COSTO TOTAL</b></font>",style),
				Paragraph("<font size=8><b>PROVISIÓN TOTAL</b></font>",style),
				Paragraph("<font size=8><b>TOTAL NETO</b></font>",style)]]
			
			t=Table(data,colWidths=size_widths, rowHeights=[18,30])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,0)),
				('SPAN',(2,0),(2,1)),
				('SPAN',(3,0),(5,0)),
				('SPAN',(6,0),(8,0)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,50,500) 
			t.drawOn(c,50,hReal-130)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-142
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "banco_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-142
		pagina = 1

		size_widths = [40,70,200,130,60,50,60,60,60] #770
		detail = self.env['sunat.table.data.38'].search([('company_id', '=', self.company_id.id),('date', '>=', self.fiscal_year_id.date_from),('date', '<=', self.period_id.date_end)])

		pdf_header(self,c,wReal,hReal,size_widths)

		c.setFont("Helvetica", 7)

		prov_total, total = 0, 0

		for i in detail:
			first_pos = 50

			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''),50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.vat or ''),50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.name or ''),220) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.name or ''),140) )
			first_pos += size_widths[3]

			c.drawRightString( first_pos+size_widths[4]-2,pos_inicial,'{:,.2f}'.format((i.amount or 0)) )
			first_pos += size_widths[4]

			c.drawRightString( first_pos+size_widths[5]-2,pos_inicial,'{:,.2f}'.format((i.qty or 0)) )
			first_pos += size_widths[5]
			
			c.drawRightString( first_pos+size_widths[6]-2,pos_inicial,'{:,.2f}'.format((i.total_cost or 0)) )
			first_pos += size_widths[6]
			
			c.drawRightString( first_pos+size_widths[7]-2,pos_inicial,'{:,.2f}'.format((i.prov_total or 0)) )
			first_pos += size_widths[7]
			prov_total+=(i.prov_total or 0)
			
			c.drawRightString( first_pos+size_widths[8]-2,pos_inicial,'{:,.2f}'.format((i.total or 0)) )
			first_pos += size_widths[8]
			total+=(i.total or 0)

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,5,pagina,size_widths)

		c.setFont("Helvetica-Bold", 8)
		c.drawString( 600 ,pos_inicial,'TOTALES:')
		c.drawRightString( 718,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % prov_total)) )
		c.drawRightString( 778,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)))

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('Cuenta 31 - Valores',base64.encodebytes(b''.join(f.readlines())))
	
	#INICIO LIBROS
	
	# LIBRO DIARIO
	def get_libro_diario(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_libro_diario_xls()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_libro_diario()
	
	def get_libro_diario_xls(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'libro_diario.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Libro Diario")
		worksheet.set_tab_color('blue')

		x=2
		worksheet.merge_range(x,1,x,9,'LIBRO DIARIO DEL MES DE ' + self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=2	
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		date_new_format = workbook.add_format({'num_format':'dd-mm-yyyy'})
		date_new_format.set_align('justify')
		date_new_format.set_align('vcenter')
		date_new_format.set_font_size(10)
		date_new_format.set_font_name('Times New Roman')
		formats['date_new_format'] = date_new_format
		
		especialtotal_new = workbook.add_format({'bold': True})
		especialtotal_new.set_align('right')
		especialtotal_new.set_align('vcenter')
		especialtotal_new.set_text_wrap()
		especialtotal_new.set_font_size(10)
		especialtotal_new.set_font_name('Times New Roman')
		formats['especialtotal_new'] = especialtotal_new


		worksheet.merge_range(x,1,x+1,1,"N° CORREL. ASNTO COD. UNI. DE OPER.",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,2,x+1,2,u"FECHA DE LA OPERACIÓN",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,u"GLOSA O DESCRIPCION DE LA OPERACIÓN",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,5,u"CUENTA ASOCIADA A LA OPERACIÓN",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x,7,"MOVIMIENTO",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,4,u"CÓDIGO",formats_custom['especial_2_custom'])
		worksheet.write(x,5,u"DENOMINACIÓN",formats_custom['especial_2_custom'])
		worksheet.write(x,6,"DEBE",formats_custom['especial_2_custom'])
		worksheet.write(x,7,"HABER",formats_custom['especial_2_custom'])
		
		sql = self.env['account.base.sunat'].pdf_get_sql_vst_diariog(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		x+=1
		cont = 0
		libro = ''
		voucher = ''
		sum_debe = 0
		sum_haber = 0
  
		for i in res:
			if cont == 0:
				libro = i['libro']
				voucher = i['voucher']
				cont += 1
				worksheet.write(x,1,libro,formats['especial4'])
				x+=1
			if libro != i['libro']:
				x+=1
				worksheet.write(x,5,"TOTAL :",formats['especial2'])
				worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)),formats['especialtotal_new'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)),formats['especialtotal_new'])
				sum_debe = 0
				sum_haber = 0
				x+=2
				libro = i['libro']
				voucher = i['voucher']
				worksheet.write(x,1,libro,formats['especial4'])
				x+=1
			if voucher != i['voucher']:
				x+=1
				worksheet.write(x,5,"TOTAL :",formats['especial2'])
				worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)),formats['especialtotal_new'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)),formats['especialtotal_new'])
				sum_debe = 0
				sum_haber = 0
				x+=1
				voucher = i['voucher']
				x+=1
			x+=1
			worksheet.write(x,1, i['voucher'] if i['voucher'] else '',formats['especial4'])
			worksheet.write(x,2, i['fecha'] if i['fecha'] else '',formats['date_new_format'])
			worksheet.write(x,3, i['glosa'] if i['glosa'] else '',formats['especial4'])
			worksheet.write(x,4, i['cuenta'] if i['cuenta'] else '',formats['especial4'])
			worksheet.write(x,5, i['des'] if i['des'] else '',formats['especial4'])
			worksheet.write(x,6, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])),formats['numberdosespecial'])
			sum_debe += i['debe']
			worksheet.write(x,7, '{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])),formats['numberdosespecial'])
			sum_haber += i['haber']
		x+=1
		worksheet.write(x,5,"TOTAL :",formats['especial2'])
		worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)),formats['especialtotal_new'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)),formats['especialtotal_new'])
		
		widths = [8,20,14,24,13,28,9,9]
		worksheet = ReportBase.resize_cells(worksheet,widths)

		workbook.close()
		f = open(direccion +'libro_diario.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO  DIARIO '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))
	# FIN LIBRO DIARIO
 
 	# LIBRO MAYOR
	def get_libro_mayor(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_libro_mayor_xls()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_libro_mayor()

	def get_libro_mayor_xls(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'libro_mayor.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Libro Mayor")
		worksheet.set_tab_color('blue')
		x=2
		worksheet.merge_range(x,0,x,8,'LIBRO MAYOR DEL MES DE ' + self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1	
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=2
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x+1,1,"LIBRO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,2,x+1,2,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,u"NÚMERO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+1,4,"NRO. CORRELATIVO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+1,5,"FECHA",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+1,6,"DESCRIPCIÓN GLOSA",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x,8,"SALDOS Y MOVIMIENTOS",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,7,"DEUDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,8,"ACREEDOR",formats_custom['especial_2_custom'])
		

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_mayor(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		cuenta = ''
		sum_debe = 0
		sum_haber = 0
		saldo_debe = 0
		saldo_haber = 0

		

		date_new_format = workbook.add_format({'num_format':'dd-mm-yyyy'})
		date_new_format.set_align('justify')
		date_new_format.set_align('vcenter')
		date_new_format.set_font_size(10)
		date_new_format.set_font_name('Times New Roman')
		formats['date_new_format'] = date_new_format
		
		especialtotal_new = workbook.add_format({'bold': True})
		especialtotal_new.set_align('right')
		especialtotal_new.set_align('vcenter')
		especialtotal_new.set_text_wrap()
		especialtotal_new.set_font_size(10)
		especialtotal_new.set_font_name('Times New Roman')
		formats['especialtotal_new'] = especialtotal_new

		for i in res:
			x+=1
			if cont == 0:
				cuenta = i['cuenta']
				cont += 1
				worksheet.merge_range(x,1,x,8,'Cod. Cuenta: ' + cuenta + '' + i['name_cuenta'],formats['especial4'])
				x+=1
			if cuenta != i['cuenta']:
				x+=1
				worksheet.write(x,6,"TOTAL CUENTA:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)),formats['especialtotal_new'])
				worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)),formats['especialtotal_new'])
				x+=1
				worksheet.write(x,6,"SALDO FINAL:",formats['especial2'])
				saldo_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
				saldo_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_debe)),formats['especialtotal_new'])
				worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_haber)),formats['especialtotal_new'])
				x+=2
				sum_debe = 0
				sum_haber = 0
				cuenta = i['cuenta']
				worksheet.merge_range(x,1,x,8,'Cod. Cuenta: ' + cuenta if cuenta else '' + '' + i['name_cuenta'] if i['name_cuenta'] else '',formats['especial4'])
				x+=1
			worksheet.write(x,1, i['libro'] if i['libro'] else '',formats['especial4'])
			worksheet.write(x,2,i['td_sunat'] if i['td_sunat'] else '',formats['especial4'])
			worksheet.write(x,3,i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial4'])
			worksheet.write(x,4,i['voucher'] if i['voucher'] else '',formats['especial4'])
			worksheet.write(x,5,i['fecha'] if i['fecha'] else '',formats['date_new_format'])
			worksheet.write(x,6,i['glosa'] if i['glosa'] else '',formats['especial4'])
			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])),formats['numberdosespecial'])
			sum_debe += i['debe']
			worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])),formats['numberdosespecial'])
			sum_haber += i['haber']
		x+=1
		worksheet.write(x,6,"TOTAL CUENTA:",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)),formats['especialtotal_new'])
		worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)),formats['especialtotal_new'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL:",formats['especial2'])
		saldo_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
		saldo_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_debe)),formats['especialtotal_new'])
		worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_haber)),formats['especialtotal_new'])
		x+=2

		widths = [9,9,9,18,16,13,71,14,14]
		worksheet = ReportBase.resize_cells(worksheet,widths)

		workbook.close()
		f = open(direccion +'libro_mayor.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO  Mayor '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))
	# FIN LIBRO MAYOR
	
 	# LIBRO COMPRAS
	def get_compras(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_libro_compras_xls()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_compras()

	def get_libro_compras_xls(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'libro_compras.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Libro Compras")
		worksheet.set_tab_color('blue')
		x=2
		worksheet.merge_range(x,1,x,29,'REGISTRO DE COMPRAS DEL MES DE ' + self.period_id.name, formats['especial5'])
		x+=1

		worksheet.merge_range(x,1,x,3,self.company_id.name,formats['especial5'])
		x+=1
		worksheet.merge_range(x,1,x,3,self.company_id.partner_id.street if self.company_id.partner_id.street else '',formats['especial5'])
		x+=1	
		worksheet.merge_range(x,1,x,3,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '',formats['especial5'])
		x+=1
		worksheet.merge_range(x,1,x,3,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '',formats['especial5'])
		x+=2
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(9.8)
		especial_2_custom.set_font_name('Calibri')
		formats_custom['especial_2_custom'] = especial_2_custom

		date_new_format = workbook.add_format({'num_format':'dd-mm-yyyy'})
		date_new_format.set_align('justify')
		date_new_format.set_align('vcenter')
		date_new_format.set_font_size(10)
		date_new_format.set_font_name('Times New Roman')
		formats['date_new_format'] = date_new_format
		
		especialtotal_new = workbook.add_format({'bold': True})
		especialtotal_new.set_align('right')
		especialtotal_new.set_align('vcenter')
		especialtotal_new.set_text_wrap()
		especialtotal_new.set_font_size(10)
		especialtotal_new.set_font_name('Times New Roman')
		formats['especialtotal_new'] = especialtotal_new

		worksheet.merge_range(x,1,x+2,1,u"N° VOU.",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,2,x+2,2,u"F. EMISIÓN",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+2,3,u"F. VENC",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,u"COMPROBANTE DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,u"N° COMPROBANTE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,8,x,10,u"IMFORMACIÓN DEL PROVEEDOR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,11,x+1,12,u"ADQ. GRAV. DEST. A OPER. GRAV. Y/O EXP.",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,13,x+1,14,u"ADQ. GRAV. DEST. A OPER. GRAV. Y/O EXP. Y A OPER.",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,15,x+1,16,u"ADQ. GRAV. DEST. A OPER. NO GRABADAS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,17,x+2,17,u"VALOR DE ADQ NO GRABADAS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,18,x+2,18,u"I.S.C",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,19,x+2,19,u"ICBPER",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,20,x+2,20,u"OTROS TRIBUTOS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,21,x+2,21,u"IMPORTE TOTAL",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,22,x+2,22,u"N° COMP. DE PAGO EMITIDO POR SUJETO NO DOMICILIADO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,23,x+1,24,u"CONTANCIA DE DEPOSITO DE DETRACCIÓN",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,25,x+2,25,u"T.C",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,26,x,29,u"REFERENCIA DEL DOCUMENTO",formats_custom['especial_2_custom'])
		x+=1
		worksheet.merge_range(x,4,x+1,4,u"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+1,5,u"SERIE",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+1,6,u"AÑO DE EMISIÓN DUA O DSI",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,8,x,9,u"DOC. DE IDENTIDAD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,10,x+1,10,u"APELLIDOS Y NOMBRES O RAZON SOCIAL",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,26,x+1,26,u"FECHA",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,27,x+1,27,u"T/D",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,28,x+1,28,u"SERIE",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,29,x+1,29,u"NÚMERO COMPROBANTE DOC NÚMERO DE PAGO",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,8,"DOC",formats_custom['especial_2_custom'])
		worksheet.write(x,9,u"NÚMERO",formats_custom['especial_2_custom'])
		worksheet.write(x,11,u"BASE IMP.",formats_custom['especial_2_custom'])
		worksheet.write(x,12,u"I.G.V.",formats_custom['especial_2_custom'])
		worksheet.write(x,13,u"BASE IMP.",formats_custom['especial_2_custom'])
		worksheet.write(x,14,u"I.G.V.",formats_custom['especial_2_custom'])
		worksheet.write(x,15,u"BASE IMP.",formats_custom['especial_2_custom'])
		worksheet.write(x,16,u"I.G.V.",formats_custom['especial_2_custom'])
		worksheet.write(x,23,u"NÚMERO",formats_custom['especial_2_custom'])
		worksheet.write(x,24,u"FECHA EMI.",formats_custom['especial_2_custom'])
		

		sql = self.env['account.base.sunat']._get_sql_vst_compras(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()


		cont = 0
		td = ''
		base1, base2, base3, igv1, igv2, igv3, cng, isc, otros, icbper, total = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
		total_base1, total_base2, total_base3, total_igv1, total_igv2, total_igv3, total_cng, total_isc, total_icbper, total_otros, total_total = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

		for i in res:
			x+=1
			if cont == 0:
				td = i['td']
				cont += 1
				worksheet.write(x,1,"Tipo Doc.: " + (td or ''),formats['especial2'])
				x+=1
			if td != i['td']:
				worksheet.write(x,10,"TOTALES:",formats['especialtotal_new'])
				worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base1)),formats['numberdosespecial'])
				worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv1)),formats['numberdosespecial'])
				worksheet.write(x,13,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base2)),formats['numberdosespecial'])
				worksheet.write(x,14,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv2)),formats['numberdosespecial'])
				worksheet.write(x,15,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base3)),formats['numberdosespecial'])
				worksheet.write(x,16,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv3)),formats['numberdosespecial'])
				worksheet.write(x,17,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % cng)),formats['numberdosespecial'])
				worksheet.write(x,18,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % isc)),formats['numberdosespecial'])
				worksheet.write(x,19,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % icbper)),formats['numberdosespecial'])
				worksheet.write(x,20,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % otros)),formats['numberdosespecial'])
				worksheet.write(x,21,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)),formats['numberdosespecial'])
				base1, base2, base3, igv1, igv2, igv3, cng, isc, otros, icbper, total = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
				td = i['td']
				x+=1
				worksheet.write(x,1,"Tipo Doc.: " + (td or ''),formats['especial2'])
				x+=1
			worksheet.write(x,1,i['voucher'] if i['voucher'] else '',formats['especial4'])
			worksheet.write(x,2,i['fecha_e'] if i['fecha_e'] else '',formats['date_new_format'])
			worksheet.write(x,3,i['fecha_v'] if i['fecha_v'] else '',formats['date_new_format'])
			worksheet.write(x,4,i['td'] if i['td'] else '',formats['especial4'])
			worksheet.write(x,5,i['serie'] if i['serie'] else '',formats['especial4'])
			worksheet.write(x,6,i['anio'] if i['anio'] else '',formats['especial4'])
			worksheet.write(x,7,i['numero'] if i['numero'] else '',formats['especial4'])
			worksheet.write(x,8,i['tdp'] if i['tdp'] else '',formats['especial4'])
			worksheet.write(x,9,i['docp'] if i['docp'] else '',formats['especial4'])
			worksheet.write(x,10,i['namep'] if i['namep'] else '',formats['especial4'])
			worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['base1'])),formats['numberdosespecial'])
			base1 += i['base1']
			total_base1 += i['base1']
			worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['igv1'])),formats['numberdosespecial'])
			igv1 += i['igv1']
			total_igv1 += i['igv1']
			worksheet.write(x,13,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['base2'])),formats['numberdosespecial'])
			base2 += i['base2']
			total_base2 += i['base2']
			worksheet.write(x,14,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['igv2'])),formats['numberdosespecial'])
			igv2 += i['igv2']
			total_igv2 += i['igv2']
			worksheet.write(x,15,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['base3'])),formats['numberdosespecial'])
			base3 += i['base3']
			total_base3 += i['base3']
			worksheet.write(x,16,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['igv3'])),formats['numberdosespecial'])
			igv3 += i['igv3']
			total_igv3 += i['igv3']
			worksheet.write(x,17,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['cng'])),formats['numberdosespecial'])
			cng += i['cng']
			total_cng += i['cng']
			worksheet.write(x,18,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['isc'])),formats['numberdosespecial'])
			isc += i['isc']
			total_isc += i['isc']
			worksheet.write(x,19,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['icbper'])),formats['numberdosespecial'])
			icbper += i['icbper']
			total_icbper += i['icbper']
			worksheet.write(x,20,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['otros'])),formats['numberdosespecial'])
			otros += i['otros']
			total_otros += i['otros']
			worksheet.write(x,21,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['total'])),formats['numberdosespecial'])
			total += i['total']
			total_total += i['total']
			worksheet.write(x,22,i['nro_no_dom'] if i['nro_no_dom'] else '',formats['especial4'])
			worksheet.write(x,23,i['comp_det'] if i['comp_det'] else '',formats['especial4'])
			worksheet.write(x,24,i['fecha_det'] if i['fecha_det'] else '',formats['especial4'])
			worksheet.write(x,25,'{:,.4f}'.format(decimal.Decimal ("%0.4f" % i['currency_rate'])),formats['numberdosespecial'])
			worksheet.write(x,26,i['f_doc_m'] if i['f_doc_m'] else '',formats['especial4'])
			worksheet.write(x,27,i['td_doc_m'] if i['td_doc_m'] else '',formats['especial4'])
			worksheet.write(x,28,i['serie_m'] if i['serie_m'] else '',formats['especial4'])
			worksheet.write(x,29,i['numero_m'] if i['numero_m'] else '',formats['especial4'])
		x+=1
		worksheet.write(x,10,"TOTALES:",formats['especial2'])
		worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base1)),formats['especialtotal_new'])
		worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv1)),formats['especialtotal_new'])
		worksheet.write(x,13,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base2)),formats['especialtotal_new'])
		worksheet.write(x,14,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv2)),formats['especialtotal_new'])
		worksheet.write(x,15,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base3)),formats['especialtotal_new'])
		worksheet.write(x,16,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv3)),formats['especialtotal_new'])
		worksheet.write(x,17,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % cng)),formats['especialtotal_new'])
		worksheet.write(x,18,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % isc)),formats['especialtotal_new'])
		worksheet.write(x,19,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % icbper)),formats['especialtotal_new'])
		worksheet.write(x,20,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % otros)),formats['especialtotal_new'])
		worksheet.write(x,21,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)),formats['especialtotal_new'])
		x+=1
		worksheet.write(x,10,"TOTAL GENERAL:",formats['especial2'])
		worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_base1)),formats['especialtotal_new'])
		worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_igv1)),formats['especialtotal_new'])
		worksheet.write(x,13,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_base2)),formats['especialtotal_new'])
		worksheet.write(x,14,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_igv2)),formats['especialtotal_new'])
		worksheet.write(x,15,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_base3)),formats['especialtotal_new'])
		worksheet.write(x,16,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_igv3)),formats['especialtotal_new'])
		worksheet.write(x,17,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_cng)),formats['especialtotal_new'])
		worksheet.write(x,18,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_isc)),formats['especialtotal_new'])
		worksheet.write(x,19,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_icbper)),formats['especialtotal_new'])
		worksheet.write(x,20,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_otros)),formats['especialtotal_new'])
		worksheet.write(x,21,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_total)),formats['especialtotal_new'])
		

		widths = [2,15,11,11,8,7,8,13,13,13,61,13,13,13,15,15,15,11,12,11,17,12,22,16,13,8,8,25,8,27]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		worksheet.set_row(9, 25)  # Ajusta la altura de la fila 1 a 30 (puedes ajustar el valor según sea necesario)
		workbook.close()
		f = open(direccion +'libro_compras.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO COMPRAS '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))
	# FIN LIBRO COMPRAS
 
	# LIBRO VENTAS
	def get_ventas(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_libro_ventas_xls()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_ventas()

	def get_libro_ventas_xls(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'libro_ventas.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Libro Ventas")
		worksheet.set_tab_color('blue')
		
		x=2
		worksheet.merge_range(x,1,x,23,'REGISTRO DE VENTAS E INGRESOS DEL MES DE ' + self.period_id.name, formats['especial5'])
		x+=1
		worksheet.merge_range(x,1,x,3,self.company_id.name,formats['especial5'])
		x+=1
		worksheet.merge_range(x,1,x,3,self.company_id.partner_id.street if self.company_id.partner_id.street else '',formats['especial5'])
		x+=1	
		worksheet.merge_range(x,1,x,3,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '',formats['especial5'])
		x+=1
		worksheet.merge_range(x,1,x,3,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '',formats['especial5'])
		x+=2
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(9)
		especial_2_custom.set_font_name('Calibri')
		formats_custom['especial_2_custom'] = especial_2_custom

		date_new_format = workbook.add_format({'num_format':'dd-mm-yyyy'})
		date_new_format.set_align('justify')
		date_new_format.set_align('vcenter')
		date_new_format.set_font_size(10)
		date_new_format.set_font_name('Times New Roman')
		formats['date_new_format'] = date_new_format
		
		especialtotal_new = workbook.add_format({'bold': True})
		especialtotal_new.set_align('right')
		especialtotal_new.set_align('vcenter')
		especialtotal_new.set_text_wrap()
		especialtotal_new.set_font_size(10)
		especialtotal_new.set_font_name('Times New Roman')
		formats['especialtotal_new'] = especialtotal_new

		worksheet.merge_range(x,1,x+2,1,u"N° VOU.",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,2,x+2,2,u"F. EMISIÓN",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+2,3,u"F. VENC",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,u"COMPROBANTE DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x,9,u"IMFORMACIÓN DEL CLIENTE",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,10,x+2,10,u"VALOR FACTURADO DE LA EXPORTACIÓN",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,11,x+2,11,u"BASE. IMP. DE LA OPE. GRAVADA",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,12,x,13,u"IMP. TOTAL DE LA OPERACIÓN",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,14,x+2,14,u"I.S.C",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,15,x+2,15,u"I.G.V. Y/O IPM",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,16,x+2,16,u"ICBPER",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,17,x+2,17,u"OTROS TRIBUTOS Y CARGOS QUE NO FORMAN PARTE DE LA BASE IMPONIBLE",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,18,x+2,18,u"IMPORTE TOTAL",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,19,x+2,19,u"T.C",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,20,x,23,u"REFERENCIA DEL COMPROBANTE",formats_custom['especial_2_custom'])
		x+=1
		worksheet.merge_range(x,4,x+1,4,u"T/D",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+1,5,u"SERIE",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+1,6,u"NÚMERO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x,8,u"DOC. DE IDENTIDAD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,9,x+1,9,u"APELLIDOS Y NOMBRES O RAZON SOCIAL",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,12,x+1,12,u"EXONERADA",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,13,x+1,13,u"INAFECTA",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,20,x+1,20,u"FECHA",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,21,x+1,21,u"T/D",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,22,x+1,22,u"SERIE",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,23,x+1,23,u"NÚMERO",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,7,"DOC",formats_custom['especial_2_custom'])
		worksheet.write(x,8,u"NÚMERO",formats_custom['especial_2_custom'])
		

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_ventas(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		td = ''
		exp, venta_g, exo, inaf, isc_v, igv_v, icbper, otros_v, total = 0, 0, 0, 0, 0, 0, 0, 0, 0
		total_exp, total_venta_g, total_exo, total_inaf, total_isc_v, total_igv_v, total_icbper, total_otros_v, total_total = 0, 0, 0, 0, 0, 0, 0, 0, 0

		for i in res:
			x+=1
			if cont == 0:
				td = i['td']
				cont += 1
				worksheet.write(x,1,'Tipo Doc.: ' + (td or ''),formats['especialtotal_new'])
				x+=1
			if td != i['td']:
				worksheet.write(x,9,'TOTALES:',formats['especialtotal_new'])
				worksheet.write(x,10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % exp)),formats['numberdosespecial'])
				worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % venta_g)),formats['numberdosespecial'])
				worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % exo)),formats['numberdosespecial'])
				worksheet.write(x,13,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % inaf)),formats['numberdosespecial'])
				worksheet.write(x,14,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % isc_v)),formats['numberdosespecial'])
				worksheet.write(x,15,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv_v)),formats['numberdosespecial'])
				worksheet.write(x,16,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % icbper)),formats['numberdosespecial'])
				worksheet.write(x,17,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % otros_v)),formats['numberdosespecial'])
				worksheet.write(x,18,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)),formats['numberdosespecial'])
				exp, venta_g, exo, inaf, isc_v, igv_v, icbper, otros_v, total = 0, 0, 0, 0, 0, 0, 0, 0, 0
				x+=1
				td = i['td']
				worksheet.write(x,1,'Tipo Doc.: ' + (td or ''),formats['especialtotal_new'])
				x+=1
			worksheet.write(x,1,i['voucher'] if i['voucher'] else '',formats['especial4'])
			worksheet.write(x,2,i['fecha_e'] if i['fecha_e'] else '',formats['date_new_format'])
			worksheet.write(x,3,i['fecha_v'] if i['fecha_v'] else '',formats['date_new_format'])
			worksheet.write(x,4,i['td'] if i['td'] else '',formats['especial4'])
			worksheet.write(x,5,i['serie'] if i['serie'] else '',formats['especial4'])
			worksheet.write(x,6,i['numero'] if i['numero'] else '',formats['especial4'])
			worksheet.write(x,7,i['tdp'] if i['tdp'] else '',formats['especial4'])
			worksheet.write(x,8,i['docp'] if i['docp'] else '',formats['especial4'])
			worksheet.write(x,9,i['namep'] if i['namep'] else '',formats['especial4'])
			worksheet.write(x,10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['exp'])),formats['numberdosespecial'])
			exp += i['exp']
			total_exp += i['exp']
			worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['venta_g'])),formats['numberdosespecial'])
			venta_g += i['venta_g']
			total_venta_g += i['venta_g']
			worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['exo'])),formats['numberdosespecial'])
			exo += i['exo']
			total_exo += i['exo']
			worksheet.write(x,13,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['inaf'])),formats['numberdosespecial'])
			inaf += i['inaf']
			total_inaf += i['inaf']
			worksheet.write(x,14,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['isc_v'])),formats['numberdosespecial'])
			isc_v += i['isc_v']
			total_isc_v += i['isc_v']
			worksheet.write(x,15,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['igv_v'])),formats['numberdosespecial'])
			igv_v += i['igv_v']
			total_igv_v += i['igv_v']
			worksheet.write(x,16,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['icbper'])),formats['numberdosespecial'])
			icbper += i['icbper']
			total_icbper += i['icbper']
			worksheet.write(x,17,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['otros_v'])),formats['numberdosespecial'])
			otros_v += i['otros_v']
			total_otros_v += i['otros_v']
			worksheet.write(x,18,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['total'])),formats['numberdosespecial'])
			total += i['total']
			total_total += i['total']
			worksheet.write(x,19,'{:,.4f}'.format(decimal.Decimal ("%0.4f" % i['currency_rate'])),formats['numberdosespecial'])
			worksheet.write(x,20,i['f_doc_m'] if i['f_doc_m'] else '',formats['especial4'])
			worksheet.write(x,21,i['td_doc_m'] if i['td_doc_m'] else '',formats['especial4'])
			worksheet.write(x,22,i['serie_m'] if i['serie_m'] else '',formats['especial4'])
			worksheet.write(x,23,i['numero_m'] if i['numero_m'] else '',formats['especial4'])
		x+=1
		worksheet.write(x,9,'TOTALES:',formats['especialtotal_new'])
		worksheet.write(x,10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % exp)),formats['especialtotal_new'])
		worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % venta_g)),formats['especialtotal_new'])
		worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % exo)),formats['especialtotal_new'])
		worksheet.write(x,13,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % inaf)),formats['especialtotal_new'])
		worksheet.write(x,14,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % isc_v)),formats['especialtotal_new'])
		worksheet.write(x,15,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv_v)),formats['especialtotal_new'])
		worksheet.write(x,16,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % icbper)),formats['especialtotal_new'])
		worksheet.write(x,17,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % otros_v)),formats['especialtotal_new'])
		worksheet.write(x,18,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)),formats['especialtotal_new'])
		x+=1
		worksheet.write(x,9,'TOTAL GENERAL::',formats['especial2'])
		worksheet.write(x,10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_exp)),formats['especialtotal_new'])
		worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_venta_g)),formats['especialtotal_new'])
		worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_exo)),formats['especialtotal_new'])
		worksheet.write(x,13,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_inaf)),formats['especialtotal_new'])
		worksheet.write(x,14,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_isc_v)),formats['especialtotal_new'])
		worksheet.write(x,15,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_igv_v)),formats['especialtotal_new'])
		worksheet.write(x,16,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_icbper)),formats['especialtotal_new'])
		worksheet.write(x,17,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_otros_v)),formats['especialtotal_new'])
		worksheet.write(x,18,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_total)),formats['especialtotal_new'])
		
		widths = [2,15,12,13,4,8,11,10,12,61,16,16,14,12,9,10,9,31,12,9,15,9,15,10]
		
		worksheet = ReportBase.resize_cells(worksheet,widths)
		worksheet.set_row(9, 25)  # Ajusta la altura de la fila 1 a 30 (puedes ajustar el valor según sea necesario)
		workbook.close()
		f = open(direccion +'libro_ventas.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO VENTAS '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))
	# FIN LIBRO VENTAS
 
	# LIBRO CAJA
	def get_libro_caja(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_libro_caja_xls()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_libro_caja()

	def get_libro_caja_xls(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'libro_caja.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Libro Caja")
		worksheet.set_tab_color('blue')
		x=2
		worksheet.merge_range(x,1,x,5,'LIBRO CAJA - MOVIMIENTO DEL EFECTIVO DEL MES DE ' + self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1	
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=2
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x+1,1,u"NÚMERO DE VAUCHER",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,2,x+1,2,u"FECHA DE OPERACIÓN",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,u"DESCRIPCIÓN DE LA OPERACIÓN",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,5,u"SALDOS Y MOVIMIENTOS",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,4,"DEUDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,5,u"ACREEDOR",formats_custom['especial_2_custom'])
		
		
		sql = self.env['account.base.sunat'].pdf_get_sql_vst_caja(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		cont = 0
		cuenta = ''
		sum_debe = 0
		sum_haber = 0
		saldo_debe = 0
		saldo_haber = 0

		for i in res:
			x+=1
			if cont == 0:
				cuenta = i['cuenta']
				cont += 1
				worksheet.merge_range(x,1,x,5,'Cuenta: ' + cuenta + ' ' + i['name_cuenta'],formats['especial2'])
				x+=1

			if cuenta != i['cuenta']:
				worksheet.write(x,3,"TOTALES:",formats['especial2'])
				worksheet.write(x,4,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)),formats['numberdos'])
				worksheet.write(x,5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)),formats['numberdos'])
				x+=1
				worksheet.write(x,3,"SALDO FINAL:",formats['especial2'])
				saldo_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
				saldo_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)
				worksheet.write(x,4,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_debe)),formats['numberdos'])
				worksheet.write(x,5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_haber)),formats['numberdos'])
				x+=2
				sum_debe = 0
				sum_haber = 0
				cuenta = i['cuenta']
				worksheet.merge_range(x,1,x,5,'Cuenta: ' + cuenta + ' ' + i['name_cuenta'],formats['especial2'])
				x+=1
			worksheet.write(x,1,i['voucher'] if i['voucher'] else '',formats['especial4'])
			worksheet.write(x,2,i['fecha'] if i['fecha'] else '',formats['especial4'])
			worksheet.write(x,3,i['glosa'] if i['glosa'] else '',formats['especial4'])
			worksheet.write(x,4,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])),formats['numberdos'])
			sum_debe += i['debe']
			worksheet.write(x,5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])),formats['numberdos'])
			sum_haber += i['haber']
		x+=1
		worksheet.write(x,3,"TOTALES:",formats['especial2'])
		worksheet.write(x,4,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)),formats['numbertotal'])
		worksheet.write(x,5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)),formats['numbertotal'])
		x+=1
		worksheet.write(x,3,"SALDO FINAL:",formats['especial2'])
		saldo_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
		saldo_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)
		worksheet.write(x,4,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_debe)),formats['numbertotal'])
		worksheet.write(x,5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_haber)),formats['numbertotal'])
		
		widths = [8,16,15,39,17,17]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		
		workbook.close()
		f = open(direccion +'libro_caja.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO CAJA '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))
		
	# FIN LIBRO CAJA
 
	# LIBRO BANCO
	def get_libro_banco(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_libro_banco_xls()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_libro_banco()

	def get_libro_banco_xls(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'libro_banco.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Libro Banco")
		worksheet.set_tab_color('blue')
		x=2
		worksheet.merge_range(x,1,x,9,'LIBRO BANCO - MOVIMIENTOS DE LA CUENTA CORRIENTE DEL MES DE ' + self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1	
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=2
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x+1,1,u"N° VOU.",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,2,x+1,2,u"N° CORRELATIVO DEL LIBRO DIARIO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,u"FECHA OPERACIÓN",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,7,u"OPERACIONES BANCARIAS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,8,x,9,u"SALDOS Y MOVIMIENTOS",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,4,"MEDIO DE PAGO",formats_custom['especial_2_custom'])
		worksheet.write(x,5,u"DESC. OPERACIÓN",formats_custom['especial_2_custom'])
		worksheet.write(x,6,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL",formats_custom['especial_2_custom'])
		worksheet.write(x,7,u"N. TRANSACCIÓN BANCARIA DE DOCUMENTOS O DE CONTROL INTERNO DE LA OPERACIÓN",formats_custom['especial_2_custom'])
		worksheet.write(x,8,"DEUDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,9,u"ACREEDOR",formats_custom['especial_2_custom'])

		sql = self.env['account.base.sunat'].pdf_get_sql_vst_banco(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		
		cont = 0
		cuenta = ''
		debe, haber, sum_debe, sum_haber, final_debe, final_haber = 0, 0, 0, 0, 0, 0
		
		for i in res:
			x+=1
			if cont == 0:
				cuenta = i['cuenta']
				cont += 1
				worksheet.write(x,1,i['cuenta'],formats['especial2'])
				worksheet.write(x,2,i['nombre_cuenta'],formats['especial2'])
				worksheet.write(x,4,"Cod. Ent. Financiera:",formats['especial2'])
				worksheet.write(x,5,i['code_bank'] if i['code_bank'] else '',formats['especial2'])
				worksheet.write(x,6,"Número de cuenta:",formats['especial2'])
				worksheet.write(x,7,i['account_number'] if i['account_number'] else '',formats['especial2'])
				x+=1
			if cuenta != i['cuenta']:
				worksheet.write(x,7,"SUB TOTAL:",formats['especial1'])
				worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)),formats['numberdos'])
				worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)),formats['numberdos'])
				debe, haber = 0, 0
				x+=1
				cuenta = i['cuenta']
				worksheet.write(x,1,i['cuenta'],formats['especial2'])
				worksheet.write(x,2,i['nombre_cuenta'],formats['especial2'])
				worksheet.write(x,4,"Cod. Ent. Financiera:",formats['especial2'])
				worksheet.write(x,5,i['code_bank'] if i['code_bank'] else '',formats['especial2'])
				worksheet.write(x,6,"Número de cuenta:",formats['especial2'])
				worksheet.write(x,7,i['account_number'] if i['account_number'] else '',formats['especial2'])
				x+=1
			worksheet.write(x,1,i['libro'] if i['libro'] else '',formats['especial1'])
			worksheet.write(x,2,i['voucher'] if i['voucher'] else '',formats['especial1'])
			worksheet.write(x,3,i['fecha'] if i['fecha'] else '',formats['especial1'])
			worksheet.write(x,4,i['medio_pago'] if i['medio_pago'] else '',formats['especial1'])
			worksheet.write(x,5,i['glosa'] if i['glosa'] else '',formats['especial1'])
			worksheet.write(x,6,i['partner'] if i['partner'] else '',formats['especial1'])
			worksheet.write(x,7,i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1'])
			worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])),formats['numberdos'])
			debe += i['debe']
			sum_debe += i['debe']
			worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])),formats['numberdos'])
			haber += i['haber']
			sum_haber += i['haber']
		x+=1
		worksheet.write(x,7,"SUB TOTAL:",formats['especial2'])
		worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)),formats['numbertotal'])
		worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)),formats['numbertotal'])
		x+=1
		worksheet.write(x,7,"TOTALES:",formats['especial2'])
		worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)),formats['numbertotal'])
		worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)),formats['numbertotal'])
		x+=1
		worksheet.write(x,7,"SALDO FINAL TOTAL:",formats['especial2'])
		final_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
		final_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)

		worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_debe)),formats['numbertotal'])
		worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_haber)),formats['numbertotal'])

		widths = [8,9,36,13,22,37,68,54,14,14]
		worksheet = ReportBase.resize_cells(worksheet,widths)

		workbook.close()
		f = open(direccion +'libro_banco.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO BANCO '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))
		
	# FIN LIBRO BANCO
	
	# FIN LIBROS PDF Y EXCEL
	
	#FIN LIBROS

	#PLE EXCEL
	def get_excel_pdt_pi(self):
		return self.get_excel_pdt(1,self.company_id,self.period_id.date_start,self.period_id.date_end)

	def get_excel_pdt_p(self):
		return self.get_excel_pdt(0,self.company_id,self.period_id.date_start,self.period_id.date_end)
	
	def get_excel_pdt(self,type,company_id,date_start,date_end):
		ReportBase = self.env['report.base']
		type_doc = self.env['account.main.parameter'].search([('company_id','=',company_id.id)],limit=1).dt_perception
		if not type_doc:
			raise UserError(u'No existe un Tipo de Documento para Percepciones configurado en Parametros Principales de Contabilidad para su Compañía')
		if type == 1:
			name_doc = "PDT 0621PI.xlsx"
			HEADER = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6']
		if type == 0:
			name_doc = "PDT 0621P.xlsx"
			HEADER = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10']
		sql_ple = self.env['account.base.sunat']._get_sql_txt_percepciones(type,date_start,date_end,company_id.id,type_doc.code)
		workbook = ReportBase.get_excel_sql_export(sql_ple,HEADER)
		return self.env['popup.it'].get_file(name_doc,workbook)

	def get_excel_caja(self):
		ReportBase = self.env['report.base']
		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(9,self.period_id,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8',
					'CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12','CAMPO 13','CAMPO 14','CAMPO 15'])
		return self.env['popup.it'].get_file('PLE Caja.xlsx',workbook)
	
	def get_excel_banco(self):
		ReportBase = self.env['report.base']
		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(8,self.period_id,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8',
					'CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12','CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19'])
		return self.env['popup.it'].get_file('PLE Banco.xlsx',workbook)
	
	def get_excel_balance(self):
		ReportBase = self.env['report.base']
		sql_ple = self.env['account.base.sunat'].sql_txt_balance(self.fiscal_year_id,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8', 'CAMPO 9'])
		return self.env['popup.it'].get_file('BC Sunat.xlsx',workbook)
	
	def get_excel_pdb_currency_rate(self):
		ReportBase = self.env['report.base']
		sql_ple = self.env['account.base.sunat'].get_sql_pdb_currency_rate(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3'])
		return self.env['popup.it'].get_file('PDB Tipo de Cambio.xlsx',workbook)

	def get_excel_pdb_purchase(self):
		ReportBase = self.env['report.base']
		sql_ple = self.env['account.base.sunat'].get_sql_pdb_purchase(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8',
					'CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12','CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19',
					'CAMPO 20','CAMPO 21','CAMPO 22','CAMPO 23','CAMPO 24','CAMPO 25','CAMPO 26','CAMPO 27','CAMPO 28','CAMPO 29','CAMPO 30'])
		return self.env['popup.it'].get_file('PDB Compras.xlsx',workbook)

	def get_excel_pdb_sale(self):
		ReportBase = self.env['report.base']
		sql_ple = self.env['account.base.sunat'].get_sql_pdb_sale(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8',
					'CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12','CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19',
					'CAMPO 20','CAMPO 21','CAMPO 22','CAMPO 23','CAMPO 24','CAMPO 25','CAMPO 26','CAMPO 27','CAMPO 28','CAMPO 29','CAMPO 30'])
		return self.env['popup.it'].get_file('PDB Ventas.xlsx',workbook)

	def get_excel_pdb_payment(self):
		ReportBase = self.env['report.base']
		sql_ple = self.env['account.base.sunat'].get_sql_pdb_payment(self.period_id.date_start,self.period_id.date_end,self.company_id.id)
		workbook = ReportBase.get_excel_sql_export(sql_ple,['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8',
					'CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12'])
		return self.env['popup.it'].get_file('PDB Pagos.xlsx',workbook)
