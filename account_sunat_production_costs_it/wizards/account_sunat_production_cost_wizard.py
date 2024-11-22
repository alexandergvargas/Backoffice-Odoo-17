# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from io import BytesIO
import re
import uuid

class AccountSunatProductionCostWizard(models.TransientModel):
	_name = 'account.sunat.production.cost.wizard'
	_description = 'Account Sunat Production Cost Wizard'

	name = fields.Char()

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio')
	show_1 = fields.Boolean(string=u'ESTADO DE COSTO DE VENTAS ANUAL',default=True)
	show_2 = fields.Boolean(string=u'ELEMENTOS DEL COSTO MENSUAL',default=True)
	show_3 = fields.Boolean(string=u'ESTADO DE COSTO DE PRODUCCION VALORIZADO ANUAL',default=True)
	show_4 = fields.Boolean(string=u'CENTRO DE COSTOS',default=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def get_production_cost(self):
		output_name_1,output_file_1 = (self._get_ple(1)) if self.show_1 else (None,None)
		output_name_2,output_file_2 = (self._get_ple(2)) if self.show_2 else (None,None)
		output_name_3,output_file_3 = (self._get_ple(3)) if self.show_3 else (None,None)
		output_name_4,output_file_4 = (self._get_ple(4)) if self.show_4 else (None,None)
		return self.env['popup.it.production.cost'].get_file(output_name_1,output_file_1,
																output_name_2,output_file_2,
																output_name_3,output_file_3,
																output_name_4,output_file_4)

	def _get_sql_1(self,fiscal_year_id,company_id):
		sql = """
		SELECT 
		'{year}'||'0000' as campo1,
		pc.inventory_cost as campo2,
		pc.production_cost as campo3,
		pc.inventory_sale_cost as campo4,
		pc.other_settings as campo5,
		pc.state as campo6,
		NULL as campo7
		FROM production_costs_it pc
		WHERE pc.fiscal_year_id = {fiscal_year_id} and pc.company_id = {company} and pc.type_cost = 'annual_cost_of_sales'
		""".format(
			company = company_id,
			fiscal_year_id = fiscal_year_id.id,
			year = fiscal_year_id.name
		)
		return sql
	
	def _get_sql_2(self,fiscal_year_id,company_id):
		sql = """
		SELECT 
		ap.code ||'00' as campo1,
		pc.materials_cost as campo2,
		pc.labor_cost as campo3,
		pc.other_cost as campo4,
		pc.materials_expense as campo5,
		pc.labor_expense as campo6,
		pc.other_expense as campo7,
		pc.state as campo8,
		NULL as campo9
		FROM production_costs_it pc
		LEFT JOIN account_period ap on ap.id = pc.period_id
		WHERE ap.fiscal_year_id = {fiscal_year_id} and pc.company_id = {company} and pc.type_cost = 'monthly_cost_elements'
		""".format(
			company = company_id,
			fiscal_year_id = fiscal_year_id.id
		)
		return sql
	
	def _get_sql_3(self,fiscal_year_id,company_id):
		sql = """
		SELECT 
		'{year}'||'0000' as campo1,
		pc.id_code as campo2,
		pc.id_description as campo3,
		pc.materials_cost as campo4,
		pc.labor_cost as campo5,
		pc.other_cost as campo6,
		pc.materials_expense as campo7,
		pc.labor_expense as campo8,
		pc.other_expense as campo9,
		pc.inventory_ini as campo10,
		pc.inventory_fin as campo11,
		pc.table_21 as campo12,
		pc.state as campo13,
		NULL as campo14
		FROM production_costs_it pc
		WHERE pc.fiscal_year_id = {fiscal_year_id} and pc.company_id = {company} and pc.type_cost = 'annual_valued_cost_of_production'
		""".format(
			company = company_id,
			fiscal_year_id = fiscal_year_id.id,
			year = fiscal_year_id.name
		)
		return sql
	
	def _get_sql_4(self,fiscal_year_id,company_id):
		sql = """
		SELECT 
		'{year}'||'0000' as campo1,
		pc.sequence_number as campo2,
		pc.u_code as campo3,
		pc.u_description as campo4,
		pc.cc_code as campo5,
		pc.cc_description as campo6,
		pc.state as campo7,
		NULL as campo8
		FROM production_costs_it pc
		WHERE pc.fiscal_year_id = {fiscal_year_id} and pc.company_id = {company} and pc.type_cost = 'cost_centers'
		""".format(
			company = company_id,
			fiscal_year_id = fiscal_year_id.id,
			year = fiscal_year_id.name
		)
		return sql

	def _get_sql_nom(self,type):
		sql = ""
		nomenclatura = ""
		
		if type == 1:
			sql = self._get_sql_1(self.fiscal_year_id,self.company_id.id)
			nomenclatura = "100100"

		elif type == 2:
			sql = self._get_sql_2(self.fiscal_year_id,self.company_id.id)
			nomenclatura = "100200"

		elif type == 3:
			sql = self._get_sql_3(self.fiscal_year_id,self.company_id.id)
			nomenclatura = "100300"

		elif type == 4:
			sql = self._get_sql_4(self.fiscal_year_id,self.company_id.id)
			nomenclatura = "100400"
		return sql,nomenclatura

	def _get_ple(self,type):
		ruc = self.company_id.partner_id.vat
		mond = self.company_id.currency_id.name

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		if not mond:
			raise UserError('No configuro la moneda de su Compañia.')

		#LE + RUC + AÑO(YYYY) + MES(MM) + DIA(00) 
		name_doc = "LE"+str(ruc)+str(self.fiscal_year_id.name)+"0000"
		sql_ple,nomenclatura = self._get_sql_nom(type)
		self.env.cr.execute(sql_ple)
		sql_ple = "COPY (%s) TO STDOUT WITH %s" % (sql_ple, "CSV DELIMITER '|'")

		try:
			output = BytesIO()
			self.env.cr.copy_expert(sql_ple, output)
			res = base64.b64encode(output.getvalue())
			output.close()
		finally:
			res = res.decode('utf-8')

		# IDENTIFICADOR DEL LIBRO

		name_doc += nomenclatura

		# CODIGO DE OPORTUNIDAD DE PRESENTACION DEL EEFF (cc) +
		# INDICADOR DE OPERACIONES (1) +
		# INDICADOR DE CONTENIDO Con informacion(1), Sin informacion(0) +
		# INDICADOR DE MONEDA UTILIZADA Nuevos Soles(1), US Dolares(2) +
		# INDICADOR DE LIBRO ELECTRONICO GENERADO POR EL PLE (1)

		name_doc += "00"+"1"+("1" if len(res) > 0 else "0") + ("1" if mond == 'PEN' else "2") + "1.txt"

		return name_doc,res if res else base64.encodestring(b"== Sin Registros ==")