# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	def import_subsidies_by_lot(self):
		return self.slip_ids.import_subsidies()