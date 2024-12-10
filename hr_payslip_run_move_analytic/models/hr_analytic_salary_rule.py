# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSalaryRule(models.Model):
	_inherit = 'hr.salary.rule'

	detail_ids = fields.One2many('hr.salary.rule.line','salary_id','Detalle')

	def get_clear(self):
		self.detail_ids.unlink()

class hr_salary_rule_line(models.Model):
	_name = 'hr.salary.rule.line'
	_description = 'hr salary rule line'

	account_analityc = fields.Many2one('account.analytic.account',string='Cuenta Analitica')
	account_id  = fields.Many2one('account.account','Cuenta Contable',required=True)
	salary_id = fields.Many2one('hr.salary.rule','Regla Salarial')
