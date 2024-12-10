# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class HrEmployeeNewsFortnightlyWizard(models.TransientModel):
	_name = 'hr.employee.news.fortnightly.wizard'
	_description = 'Hr Employee News Fortnightly Wizard'

	fortnightly_id = fields.Many2one('hr.fortnightly', string='Periodo')
	allemployees = fields.Boolean('Añadir Empleados',default=False)
	employees_ids = fields.Many2many('hr.employee', 'hr_payslip_employee_news_fortnightly_rel','payslip_run_id','employee_id', string=u'Nuevos Empleados', required=True)
	company_id = fields.Many2one('res.company', string=u'Compañia', required=True, default=lambda self: self.env.company, readonly=True)

	@api.onchange('allemployees')
	def onchange_allemployees(self):
		if self.allemployees:
			employee_ids = []
			for employe in self.fortnightly_id.slip_ids:
				employee_ids.append(employe.employee_id.id)
			# print("employee_ids",employee_ids)
			domain = {"employees_ids": [("id", "not in", employee_ids)]}
			return {"domain": domain}

	def insert(self):
		contracts = self.employees_ids._get_contracts(self.fortnightly_id.date_start, self.fortnightly_id.date_end, states=['open', 'close'])
		# print("contracts",contracts)
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		# struct_id = self.env['hr.payroll.structure'].search([('name', '=', 'ADE_QUINCENAL'),('active', '=',True),('company_id', '=', self.env.company.id)],limit=1)
		vals = []
		for contract in contracts:
			val = {
				'name': 'Quincena - %s - %s' % (contract.employee_id.name or '',self.fortnightly_id.name or ''),
				'employee_id': contract.employee_id.id,
				'identification_id': contract.employee_id.identification_id,
				'fortnightly_id': self.fortnightly_id.id,
				'date_from': self.fortnightly_id.date_start,
				'date_to': self.fortnightly_id.date_end,
				'contract_id': contract.id,
				'struct_id': contract.structure_id.id,
				# 'struct_type_id': structure_type_id,
				'wage': contract.wage,
				'labor_regime': contract.labor_regime,
				'social_insurance_id': contract.social_insurance_id.id,
				'distribution_id': contract.distribution_id.id,
				'membership_id': contract.membership_id.id,
				'commision_type': contract.commision_type,
				'fixed_commision': contract.membership_id.fixed_commision,
				'mixed_commision': contract.membership_id.mixed_commision,
				'prima_insurance': contract.membership_id.prima_insurance,
				'retirement_fund': contract.membership_id.retirement_fund,
				'insurable_remuneration': contract.membership_id.insurable_remuneration,
				# 'is_afp': contract.membership_id.is_afp,
				'rmv': MainParameter.rmv,
				'company_id': self.env.company.id
			}
			vals.append(val)
		# print("vals",vals)
		Payslip = self.env['hr.payslip'].create(vals)
		Payslip.generate_inputs_and_wd_lines()
		# Payslip._compute_name()
		Payslip.compute_sheet()
		Payslip.state = 'verify'