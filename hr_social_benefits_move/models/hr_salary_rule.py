# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSalaryRule(models.Model):
	_inherit = 'hr.salary.rule'

	@api.model
	def store_salary_rules_bs(self):
		for rule in self.env['hr.salary.rule'].search([('code','in',['REMAFE','VACAFE','NETVACA'])]):
			rule.active = False