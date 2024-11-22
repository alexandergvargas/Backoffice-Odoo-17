# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductionCostsParameter(models.Model):
	_name = 'production.costs.parameter'
	_description = 'Parametros'
	
	name = fields.Char(
		string='Nombre',
		default="Parametros")
	
	company_id = fields.Many2one(
		comodel_name='res.company', 
		string=u'Compañia',
		required=True, 
		default=lambda self: self.env.company,
		readonly=True)
	
	# COSTO VENTA

	account_cv_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cv_rel', 
		'parameter_id', 
		'account_id', 
		string='Cuentas Productos Terminados')

	account_cv_adjustment_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cv_adjustment_rel', 
		'parameter_id', 
		'account_id', 
		string='Cuentas para Ajustes')
	
	codes_cv = fields.Char(string=u'Códigos Tipos de Operación para Producción')
	codes_cv_adjustment = fields.Char(string=u'Códigos Tipos de Operación para Ajustes')

	@api.constrains('codes_cv')
	def check_codes_cv(self):
		for i in self:
			i.check_len_caracter(i.codes_cv,2)

	@api.constrains('codes_cv_adjustment')
	def check_codes_cv_adjustment(self):
		for i in self:
			i.check_len_caracter(i.codes_cv_adjustment,2)

	def check_len_caracter(self,text,size):
		codes = text.split(',')
		for code in codes:
			if len(code)>size:
				raise UserError(u'El código no puede tener más de %d caracteres'%size)

	# COSTO MENSUAL
	account_cm_type = fields.Selection([
		('account', 'Cuentas Contables'),
		('account_analytic', 'Cuentas Analiticas')
		], string='Tipo Cuenta',
		default='account')

	materials_cost_account_cm_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cm_1_rel', 
		'parameter_id', 
		'account_id', 
		string='Cuentas Costo de Materiales y Suministros Directos')
	
	labor_cost_account_cm_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cm_2_rel', 
		'parameter_id', 
		'account_id', 
		string='Cuentas Costo de la Mano de Obra Directa')
	
	other_cost_account_cm_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cm_3_rel', 
		'parameter_id', 
		'account_id', 
		string='Cuentas Otros Costos Directos')
	
	materials_expense_account_cm_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cm_4_rel', 
		'parameter_id', 
		'account_id', 
		string=u'Cuentas Gastos de Producción Indirectos: Materiales y Suministros Indirectos')
	
	labor_expense_account_cm_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cm_5_rel', 
		'parameter_id', 
		'account_id', 
		string=u'Cuentas Gastos de Producción Indirectos:Mano de Obra Indirecta')
	
	other_expense_account_cm_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cm_6_rel', 
		'parameter_id', 
		'account_id', 
		string=u'Cuentas Otros Gastos de Producción Indirectos')
	
	cc_materials_cost_analytic_cm_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cm_1_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string=u'Cuentas Analíticas Costo de Materiales y Suministros Directos')
	
	cc_labor_cost_analytic_cm_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cm_2_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string=u'Cuentas Analíticas Costo de la Mano de Obra Directa')
	
	cc_other_cost_analytic_cm_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cm_3_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string=u'Cuentas Analíticas Otros Costos Directos')
	
	cc_materials_expense_analytic_cm_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cm_4_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string=u'Cuentas Analíticas Gastos de Producción Indirectos: Materiales y Suministros Indirectos')
	
	cc_labor_expense_analytic_cm_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cm_5_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string=u'Cuentas Analíticas Gastos de Producción  Indirectos:Mano de Obra Indirecta')
	
	cc_other_expense_analytic_cm_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cm_6_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string=u'Cuentas Analíticas Otros Gastos de Producción Indirectos')
	
	# COSTO PRODUCCION
	account_cp_type = fields.Selection([
		('account', 'Cuentas Contables'),
		('account_analytic', 'Cuentas Analiticas')
		], string='Tipo Cuenta',
		default='account')
	
	pp_account_cp_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cp_pp_rel', 
		'parameter_id', 
		'account_id', 
		string=u'Cuentas Productos en Proceso')

	materials_cost_account_cp_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cp_1_rel', 
		'parameter_id', 
		'account_id', 
		string='Cuentas Costo de Materiales y Suministros Directos')
	
	labor_cost_account_cp_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cp_2_rel', 
		'parameter_id', 
		'account_id', 
		string='Cuentas Costo de la Mano de Obra Directa')
	
	other_cost_account_cp_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cp_3_rel', 
		'parameter_id', 
		'account_id', 
		string='Cuentas Otros Costos Directos')
	
	materials_expense_account_cp_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cp_4_rel', 
		'parameter_id', 
		'account_id', 
		string=u'Cuentas Gastos de Producción Indirectos: Materiales y Suministros Indirectos')
	
	labor_expense_account_cp_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cp_5_rel', 
		'parameter_id', 
		'account_id', 
		string=u'Cuentas Gastos de Producción Indirectos:Mano de Obra Indirecta')
	
	other_expense_account_cp_ids = fields.Many2many(
		'account.account', 
		'production_costs_parameter_account_cp_6_rel', 
		'parameter_id', 
		'account_id', 
		string=u'Cuentas Otros Gastos de Producción Indirectos')
	
	cc_materials_cost_analytic_cp_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cp_1_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string=u'Cuentas Analíticas Costo de Materiales y Suministros Directos')
	
	cc_labor_cost_analytic_cp_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cp_2_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string=u'Cuentas Analíticas Costo de la Mano de Obra Directa')
	
	cc_other_cost_analytic_cp_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cp_3_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string=u'Cuentas Analíticas Otros Costos Directos')
	
	cc_materials_expense_analytic_cp_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cp_4_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string=u'Cuentas Analíticas Gastos de Producción Indirectos: Materiales y Suministros Indirectos')
	
	cc_labor_expense_analytic_cp_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cp_5_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string=u'Cuentas Analíticas Gastos de Producción  Indirectos:Mano de Obra Indirecta')
	
	cc_other_expense_analytic_cp_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cp_6_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string=u'Cuentas Analíticas Otros Gastos de Producción Indirectos')

	# CENTRO DE COSTO
	account_analytic_cc_ids = fields.Many2many(
		'account.analytic.account', 
		'production_costs_parameter_analytic_cc_rel', 
		'parameter_id', 
		'analytic_account_id', 
		string='Cuentas Analticas')