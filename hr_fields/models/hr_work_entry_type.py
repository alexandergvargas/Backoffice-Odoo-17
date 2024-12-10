# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrWorkEntryType(models.Model):
	_inherit = 'hr.work.entry.type'

	# company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company.id, required=True)
	rate = fields.Integer(string='Tasa o Monto')
	struct_ids = fields.Many2many('hr.payroll.structure', 'payroll_structure_wd_rel', 'worked_day_type_id', 'structure_id', string='Disponibilidad de la Estructura')

	@api.model
	def store_work_entry(self):
		for rule in self.env['hr.work.entry.type'].search([('code', 'in',
															['LEAVE100', 'LEAVE105', 'WORK110', 'LEAVE90',
															 'LEAVE110', 'LEAVE120', 'OUT', 'OVERTIME'])]):
			rule.active = False