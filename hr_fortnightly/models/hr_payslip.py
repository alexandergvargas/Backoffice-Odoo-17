# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	fortnightly_id = fields.Many2one('hr.fortnightly', string='Nombre del lote', readonly=True,
		copy=False, ondelete='cascade',	domain="[('company_id', '=', company_id)]")

	@api.depends('line_ids.total')
	def _compute_basic_net(self):
		line_values = (self._origin)._get_line_values(['BAS', 'TINGR', 'TAT', 'TDESN', 'NETO', 'AEM','BAS_AQ', 'TINGR_AQ', 'TAT_AQ', 'TDESN_AQ', 'NETO_AQ'])
		# print("line_values",line_values)
		for payslip in self:
			if payslip.fortnightly_id:
				payslip.basic_wage = line_values['BAS_AQ'][payslip._origin.id]['total']
				payslip.gross_wage = line_values['TINGR_AQ'][payslip._origin.id]['total']
				payslip.worker_contributions = line_values['TAT_AQ'][payslip._origin.id]['total']
				payslip.net_discounts = line_values['TDESN_AQ'][payslip._origin.id]['total']
				payslip.net_wage = line_values['NETO_AQ'][payslip._origin.id]['total']
			else:
				payslip.basic_wage = line_values['BAS'][payslip._origin.id]['total']
				payslip.gross_wage = line_values['TINGR'][payslip._origin.id]['total']
				payslip.worker_contributions = line_values['TAT'][payslip._origin.id]['total']
				payslip.net_discounts = line_values['TDESN'][payslip._origin.id]['total']
				payslip.net_wage = line_values['NETO'][payslip._origin.id]['total']
				payslip.employer_contributions = line_values['AEM'][payslip._origin.id]['total']