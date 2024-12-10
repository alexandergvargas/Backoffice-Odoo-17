# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrPayslipWorkedDays(models.Model):
	_inherit = 'hr.payslip.worked_days'

	rate = fields.Integer(related='work_entry_type_id.rate', string='Tasa o Monto')
	name = fields.Char(compute='')
	amount = fields.Monetary(compute='')
	is_paid = fields.Boolean(compute='')