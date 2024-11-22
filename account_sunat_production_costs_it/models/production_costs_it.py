# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
_MODELS = [
	("annual_cost_of_sales", "Costo de ventas anual"),
	("monthly_cost_elements", "Elementos del costo mensual"),
	("annual_valued_cost_of_production", "Costo de producción valorizado anual"),
	("cost_centers", "Centros de costos"),
]
_TABLA21 = [
	("1",'PROCESO PRODUCTIVO'),
	("2",u'LÍNEA DE PRODUCCIÓN'),
	("3",'PRODUCTO'),
	("4",'PROYECTO'),
	("9",'OTROS'),
]

class production_costs_it(models.Model):
	_name = 'production.costs.it'
	_description = 'Costo de Produccion'
	
	def get_fiscal_year(self):
		today = fields.Date.context_today(self)
		fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
		if not fiscal_year:
			raise UserError(u'No existe un año fiscal con el año actual.')
		else:
			return fiscal_year.id

	name = fields.Char(
		string='Nombre')
	
	fiscal_year_id = fields.Many2one(
		comodel_name='account.fiscal.year',
		string=u'Ejercicio',
		default=lambda self:self.get_fiscal_year())	
	
	period_id = fields.Many2one(
		comodel_name='account.period',
		string=u'Periodo')


	inventory_cost = fields.Float(
		string='Inventario inicial',
		help=u"Campo 2: Costo del inventario inicial de productos terminados contable",
		digits=(12,2))
	
	production_cost = fields.Float(
		string=u'Costo productos terminados',
		help=u"Campo 3: Costo de producción de productos terminados contable",
		digits=(12,2))
	
	inventory_sale_cost = fields.Float(
		string='Inventario final productos terminados',
		help=u"Campo 4: Costos del inventario final de productos terminados disponibles para la venta contable",
		digits=(12,2))
	
	other_settings = fields.Float(
		string='Otros ajustes',
		help="Campo 5: Ajustes diversos contables",
		digits=(12,2))
	
	materials_cost = fields.Float(
		string='Costo Materiales Y Suministros',
		help="Costo de Materiales y Suministros Directos",
		digits=(12,2))	
	
	
	labor_cost = fields.Float(
		string='Costo de Mano de Obra',
		help="Costo de la Mano de Obra Directa",
		digits=(12,2))
	
	other_cost = fields.Float(
		string='Otros Costos',
		help="Otros Costos Directos",
		digits=(12,2))
	
	materials_expense = fields.Float(
		string='Gasto Materiales Y Suministros',
		help=u"Gastos de Producción Indirectos: Materiales y Suministros Indirectos",
		digits=(12,2))	
	
	labor_expense = fields.Float(
		string='Gasto de Mano de Obra',
		help=u"Gastos de Producción  Indirectos:Mano de Obra Indirecta",
		digits=(12,2))
	
	other_expense = fields.Float(
		string='Gastos Costos',
		help=u"Otros Gastos de Producción Indirectos",
		digits=(12,2))

	id_code = fields.Char(
		string=u'Codigo de identificación',
		help=u"Código de identificación del Proceso informado" 
			  "(La información podrá agruparse optativamente" 
			  "por proceso productivo, línea de producción, producto o proyecto)")
	
	id_description = fields.Char(
		string=u'Descripción del Proceso',
		help=u"Descripción del Proceso informado")
	
	inventory_ini = fields.Float(
		string='Inventario Inicial',
		help=u"Inventario inicial de productos en proceso",
		digits=(12,2))
	
	inventory_fin = fields.Float(
		string='Inventario Final	',
		help=u"Inventario final de productos en proceso",
		digits=(12,2))
	
	table_21 = fields.Selection(
		selection=_TABLA21,
		string="Codigo Agrupamiento",
		help=u"CÓDIGO DE AGRUPAMIENTO DEL COSTO DE PRODUCCIÓN VALORIZADO ANUAL")
	
	sequence = fields.Char(string='Correlativo')

	u_code = fields.Char(
		string=u'Código de la Unidad de Operación',
		help=u"1. Código de la Unidad de Operación, de la Unidad Económica Administrativa, de la Unidad de Negocio, de la Unidad de Producción, de la Línea, de la Concesión, del Local o del Lote, de corresponder."
			 u"2. Se puede utilizar varios códigos a la vez en este campo, separandolos con el carácter '&'.")
	
	u_description = fields.Char(
		string=u'Descripción de la Unidad',
		help=u"1. Descripción de la Unidad de Operación, de la Unidad Económica Administrativa, de la Unidad de Negocio, de la Unidad de Producción, de la Línea, de la Concesión, del Local o del Lote."
			 u"2. Se puede utilizar la descripción de varios códigos a la vez en este campo, separandolos con el carácter '&'.")	
	
	cc_code = fields.Char(
		string=u'Código del Centro de Costos',
		help=u"Código del Centro de Costos, Centro de Utilidades o Centro de Inversión, de corresponder")	
	
	cc_description = fields.Char(
		string=u'Descripción del Centro de Costos',
		help=u"Descripción del Centro de Costos, Centro de Utilidades o Centro de Inversión")		
	#FIELDS GENERALES
	state = fields.Selection([
		('1', '1'),
		('8', '8'),
		('9', '9')
	], string=u'Estado de la operación',
	default="1",
	help=u"Registrar '1' cuando la operación corresponde al periodo y/o ejercicio."
		 u"Registrar '8' cuando la operación corresponde a un periodo anterior y NO ha sido anotada en dicho periodo y/o ejercicio."
		 u"Registrar '9' cuando la operación corresponde a un periodo anterior y SI ha sido anotada en dicho periodo y/o ejercicio.")

	type_cost = fields.Selection(
		selection=_MODELS,
		string="Tipo Costo",
		tracking=True,
		required=True)
	
	company_id = fields.Many2one(
		comodel_name='res.company', 
		string=u'Compañia',
		required=True, 
		default=lambda self: self.env.company,
		readonly=True)
	
	@api.onchange('type_cost')
	def _onchange_name(self):
		for i in self:
			match i.type_cost:
				case 'annual_cost_of_sales':
					i.name="Costo de ventas anual"
				case 'monthly_cost_elements':
					i.name="Elementos del costo mensual"
				case 'annual_valued_cost_of_production':
					i.name="Costo de producción valorizado anual"
				case 'cost_centers':
					i.name="Centros de costos"
				case _:
					i.name="Costo de Produccion"

	@api.model
	def create(self, vals):
		id_seq = self.env['ir.sequence'].search([('name', '=', 'Centro de Costo SUNAT IT'),('company_id','=',self.env.company.id)],limit=1)

		if not id_seq:
			id_seq = self.env['ir.sequence'].create({'name': 'Centro de Costo SUNAT IT', 
											'company_id': self.env.company.id, 
											'implementation': 'no_gap',
											'active': True, 
											'prefix': 'CC-', 
											'padding': 6, 
											'number_increment': 1, 
											'number_next_actual': 1})
		if vals['type_cost'] == 'cost_centers':
			vals['sequence'] = id_seq._next()
		t = super(production_costs_it, self).create(vals)
		return t
	
	def get_sql_account(self,fiscal_year_id,company_id,account_ids,codes=None):
		sql_codes = ""
		if codes:
			sql_codes = "AND am.code_warehouse_type in (%s)"%(','.join("'%s'"%i for i in codes.split(',')))
		sql = """SELECT 
			sum(case when right(periodo_de_fecha(am.date,am.is_opening_close)::character varying,2) = '00' then (aml.debit-aml.credit) else 0 end) as initial,
			sum(case when (right(periodo_de_fecha(am.date,am.is_opening_close)::character varying,2) between '01' and '12') then (aml.debit-aml.credit) else 0 end) as production_cost,
			sum(case when (right(periodo_de_fecha(am.date,am.is_opening_close)::character varying,2) between '00' and '12') then (aml.debit-aml.credit) else 0 end) as saldo
			from account_move_line aml
			left join account_move am on am.id = aml.move_id
			where EXTRACT (YEAR FROM am.date)::character varying = '{year}' and am.company_id = {company_id} and aml.account_id in ({account_ids}) {sql_codes}""".format(
				year = fiscal_year_id.name,
				company_id = company_id.id,
				account_ids = ','.join(str(i.id) for i in account_ids),
				sql_codes = sql_codes
			)
		return sql
	
	def get_sql_account_period(self,period_id,company_id,account_ids):
		sql = """SELECT 
			sum(aml.debit-aml.credit) as saldo
			from account_move_line aml
			left join account_move am on am.id = aml.move_id
			where periodo_de_fecha(am.date,am.is_opening_close)::character varying = '{period}' and am.company_id = {company_id} and aml.account_id in ({account_ids})""".format(
				period = period_id.code,
				company_id = company_id.id,
				account_ids = ','.join(str(i.id) for i in account_ids)
			)
		return sql
	
	def get_sql_account_analytic(self,fiscal_year_id,company_id,account_analytic_ids):
		sql = """SELECT 
			sum(case when right(periodo_de_fecha(aal.date,am.is_opening_close)::character varying,2) = '00' then (aal.amount) else 0 end) as initial,
			sum(case when (right(periodo_de_fecha(aal.date,am.is_opening_close)::character varying,2) between '01' and '12') then (aal.amount) else 0 end) as production_cost,
			sum(case when (right(periodo_de_fecha(aal.date,am.is_opening_close)::character varying,2) between '00' and '12') then (aal.amount) else 0 end) as saldo
			from account_analytic_line aal
			left join account_move_line aml on aml.id = aal.move_line_id
			left join account_move am on am.id = aml.move_id
			where EXTRACT (YEAR FROM aal.date)::character varying = '{year}' and aal.company_id = {company_id} and aal.account_id in ({account_analytic_ids})""".format(
				year = fiscal_year_id.name,
				company_id = company_id.id,
				account_analytic_ids = ','.join(str(i.id) for i in account_analytic_ids)
			)
		return sql
	
	def get_sql_account_analytic_period(self,period_id,company_id,account_analytic_ids):
		sql = """SELECT 
			sum(aal.amount) as saldo
			from account_analytic_line aal
			left join account_move_line aml on aml.id = aal.move_line_id
			left join account_move am on am.id = aml.move_id
			where periodo_de_fecha(aal.date,am.is_opening_close)::character varying = '{period}' and aal.company_id = {company_id} and aal.account_id in ({account_analytic_ids})""".format(
				period = period_id.code,
				company_id = company_id.id,
				account_analytic_ids = ','.join(str(i.id) for i in account_analytic_ids)
			)
		return sql

	def action_get_data(self):
		for i in self:
			param = self.env['production.costs.parameter'].search([('company_id','=',i.company_id.id)],limit=1)
			if not param:
				raise UserError(u'Faltan configurar parametros principales.')
			match i.type_cost:
				case 'annual_cost_of_sales':
					if not param.account_cv_ids:
						raise UserError(u'Falta configurar Cuentas de Productos Terminado en Pestaña Costo de Venta de Parámetros Principales de Compañía')
					if not param.account_cv_adjustment_ids:
						raise UserError(u'Falta configurar Cuentas de Ajustes en Pestaña Costo de Venta de Parámetros Principales de Compañía')
					if not param.codes_cv:
						raise UserError(u'Falta configurar Códigos Tipos de Operación para Producción en Pestaña Costo de Venta de Parámetros Principales de Compañía')
					if not param.codes_cv_adjustment:
						raise UserError(u'Falta configurar Códigos Tipos de Operación para Ajustes en Pestaña Costo de Venta de Parámetros Principales de Compañía')

					self.env.cr.execute(self.get_sql_account(i.fiscal_year_id,i.company_id,param.account_cv_ids))
					data_1 = self.env.cr.dictfetchone()
					self.env.cr.execute(self.get_sql_account(i.fiscal_year_id,i.company_id,param.account_cv_ids,param.codes_cv))
					data_2 = self.env.cr.dictfetchone()
					self.env.cr.execute(self.get_sql_account(i.fiscal_year_id,i.company_id,param.account_cv_adjustment_ids, param.codes_cv_adjustment))
					data_3 = self.env.cr.dictfetchone()

					i.inventory_cost = data_1['initial']
					i.production_cost = data_2['production_cost']
					i.inventory_sale_cost = data_1['saldo']
					i.other_settings = data_3['saldo']

				case 'monthly_cost_elements':
					if param.account_cm_type == 'account':
						if not param.materials_cost_account_cm_ids:
							raise UserError(u'Falta configurar Cuentas Costo de Materiales y Suministros Directos de Parámetros Principales de Compañía')
						if not param.labor_cost_account_cm_ids:
							raise UserError(u'Falta configurar Cuentas Costo de la Mano de Obra Directa de Parámetros Principales de Compañía')
						if not param.other_cost_account_cm_ids:
							raise UserError(u'Falta configurar Cuentas Otros Costos Directos de Parámetros Principales de Compañía')
						if not param.materials_expense_account_cm_ids:
							raise UserError(u'Falta configurar Cuentas Gastos de Producción Indirectos: Materiales y Suministros Indirectos de Parámetros Principales de Compañía')
						if not param.labor_expense_account_cm_ids:
							raise UserError(u'Falta configurar Cuentas Gastos de Producción Indirectos:Mano de Obra Indirecta de Parámetros Principales de Compañía')
						if not param.other_expense_account_cm_ids:
							raise UserError(u'Falta configurar Cuentas Otros Gastos de Producción Indirectos de Parámetros Principales de Compañía')
					else:
						if not param.cc_materials_cost_analytic_cm_ids:
							raise UserError(u'Falta configurar Cuentas Analíticas Costo de Materiales y Suministros Directos de Parámetros Principales de Compañía')
						if not param.cc_labor_cost_analytic_cm_ids:
							raise UserError(u'Falta configurar Cuentas Analíticas Costo de la Mano de Obra Directa de Parámetros Principales de Compañía')
						if not param.cc_other_cost_analytic_cm_ids:
							raise UserError(u'Falta configurar Cuentas Analíticas Otros Costos Directos de Parámetros Principales de Compañía')
						if not param.cc_materials_expense_analytic_cm_ids:
							raise UserError(u'Falta configurar Cuentas Analíticas Gastos de Producción Indirectos: Materiales y Suministros Indirectos de Parámetros Principales de Compañía')
						if not param.cc_labor_expense_analytic_cm_ids:
							raise UserError(u'Falta configurar Cuentas Analíticas Gastos de Producción Indirectos:Mano de Obra Indirecta de Parámetros Principales de Compañía')
						if not param.cc_other_expense_analytic_cm_ids:
							raise UserError(u'Falta configurar Cuentas Analíticas Otros Gastos de Producción Indirectos de Parámetros Principales de Compañía')
						
					periods = self.env['account.period'].search([('fiscal_year_id','=',i.fiscal_year_id.id),('is_opening_close','=', False)])

					for period in periods:
						reg = self.env['production.costs.it'].search([('type_cost','=','monthly_cost_elements'),('period_id','=',period.id),('company_id','=',i.company_id.id)],limit=1)
						if not reg:
							reg = self.env['production.costs.it'].create({
								'type_cost': 'monthly_cost_elements',
								'period_id': period.id,
								'company_id': i.company_id.id,
							})
							reg._onchange_name()
						if param.account_cm_type == 'account':
							self.env.cr.execute(self.get_sql_account_period(period,i.company_id,param.materials_cost_account_cm_ids))
							data_1 = self.env.cr.dictfetchone()	
							self.env.cr.execute(self.get_sql_account_period(period,i.company_id,param.labor_cost_account_cm_ids))
							data_2 = self.env.cr.dictfetchone()	
							self.env.cr.execute(self.get_sql_account_period(period,i.company_id,param.other_cost_account_cm_ids))
							data_3 = self.env.cr.dictfetchone()	
							self.env.cr.execute(self.get_sql_account_period(period,i.company_id,param.materials_expense_account_cm_ids))
							data_4 = self.env.cr.dictfetchone()	
							self.env.cr.execute(self.get_sql_account_period(period,i.company_id,param.labor_expense_account_cm_ids))
							data_5 = self.env.cr.dictfetchone()	
							self.env.cr.execute(self.get_sql_account_period(period,i.company_id,param.other_expense_account_cm_ids))
							data_6 = self.env.cr.dictfetchone()	
						else:
							self.env.cr.execute(self.get_sql_account_analytic_period(period,i.company_id,param.cc_materials_cost_analytic_cm_ids))
							data_1 = self.env.cr.dictfetchone()	
							self.env.cr.execute(self.get_sql_account_analytic_period(period,i.company_id,param.cc_labor_cost_analytic_cm_ids))
							data_2 = self.env.cr.dictfetchone()	
							self.env.cr.execute(self.get_sql_account_analytic_period(period,i.company_id,param.cc_other_cost_analytic_cm_ids))
							data_3 = self.env.cr.dictfetchone()	
							self.env.cr.execute(self.get_sql_account_analytic_period(period,i.company_id,param.cc_materials_expense_analytic_cm_ids))
							data_4 = self.env.cr.dictfetchone()	
							self.env.cr.execute(self.get_sql_account_analytic_period(period,i.company_id,param.cc_labor_expense_analytic_cm_ids))
							data_5 = self.env.cr.dictfetchone()	
							self.env.cr.execute(self.get_sql_account_analytic_period(period,i.company_id,param.cc_other_expense_analytic_cm_ids))
							data_6 = self.env.cr.dictfetchone()	
						reg.materials_cost = data_1['saldo']
						reg.labor_cost = data_2['saldo']
						reg.other_cost = data_3['saldo']
						reg.materials_expense = data_4['saldo']
						reg.labor_expense = data_5['saldo']
						reg.other_expense = data_6['saldo']
						
				case 'annual_valued_cost_of_production':
					i.name="Costo de producción valorizado anual"
				case 'cost_centers':
					if not param.account_analytic_cc_ids:
						raise UserError(u'Falta configurar las Cuentas Analticas de la Pestaña Centro de Costo de Parámetros Principales de Compañía')
					c = 0
					for analytic in param.account_analytic_cc_ids:
						if c == 0:
							i.u_code = analytic.plan_id.code
							i.u_description = analytic.plan_id.name
							i.cc_code = analytic.code
							i.cc_description = analytic.name
						else:
							reg = self.env['production.costs.it'].create({
								'type_cost': 'cost_centers',
								'fiscal_year_id': i.fiscal_year_id.id,
								'company_id': i.company_id.id,
								'u_code' : analytic.plan_id.code,
								'u_description' : analytic.plan_id.name,
								'cc_code' : analytic.code,
								'cc_description' : analytic.name
							})
							reg._onchange_name()
						c+=1

				case _:
					i.name="Costo de Produccion"