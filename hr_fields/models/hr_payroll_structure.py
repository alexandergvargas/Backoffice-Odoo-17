# -*- coding: utf-8 -*-

from odoo import api, fields, models

class HrPayrollStructure(models.Model):
	_inherit = 'hr.payroll.structure'

	company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company.id)
	wd_types_ids = fields.Many2many('hr.work.entry.type', 'payroll_structure_wd_rel', 'structure_id', 'worked_day_type_id')
	# journal_id = fields.Many2one(required=False)

	@api.returns('self', lambda value: value.id)
	def copy(self, default=None):
		self.ensure_one()
		default = dict(default or {})
		if 'name' not in default:
			default['name'] = self.name
		return super(HrPayrollStructure, self).copy(default=default)

	def get_wizard(self):
		wizard = self.env['hr.payroll.structure.wizard'].create({'name':'Generacion de Estructuras'})
		return {
			'type':'ir.actions.act_window',
			'res_id':wizard.id,
			'view_mode':'form',
			'res_model':'hr.payroll.structure.wizard',
			'views':[[self.env.ref('hr_fields.hr_payroll_structure_wizard_form_inherit').id,'form']],
			'target':'new'
		}

	@api.model
	def store_payroll_structure(self):
		for rule in self.env['hr.payroll.structure'].search([('name','in',['Regular Pay','Worker Pay'])]):
			rule.active = False