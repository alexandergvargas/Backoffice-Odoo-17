# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSalaryRule(models.Model):
	_inherit = 'hr.salary.rule'

	account_debit = fields.Many2one('account.account', 'Cuenta de debito', domain=[('deprecated', '=', False)])
	account_credit = fields.Many2one('account.account', 'Cuenta de Credito', domain=[('deprecated', '=', False)])
	is_detail_cta = fields.Boolean(string='Detallar Cuenta Credito', default=False)
