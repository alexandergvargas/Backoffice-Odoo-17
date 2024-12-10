# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrAdvanceLoanWizard(models.TransientModel):
	_name = 'hr.advance.loan.wizard'
	_description = 'Hr Advance Loan Wizard'

	name = fields.Char()
	company_ids = fields.Many2many('res.company', string='Compañias')

	def duplicate_by_company_advance(self):
		Advances = self.env['hr.advance.type'].browse(self._context.get('active_ids'))
		for rec in Advances:
			for comp in self.company_ids:
				acc = self.env['hr.payslip.input.type'].search([('company_id', '=', comp.id), ('code', '=', rec.input_id.code)])
				rec.copy(default={'company_id': comp.id, 'input_id': acc.id if acc else None})

	def duplicate_by_company_loan(self):
		Loans = self.env['hr.loan.type'].browse(self._context.get('active_ids'))
		for rec in Loans:
			for comp in self.company_ids:
				acc = self.env['hr.payslip.input.type'].search([('company_id', '=', comp.id), ('code', '=', rec.input_id.code)])
				rec.copy(default={'company_id': comp.id, 'input_id': acc.id if acc else None})
