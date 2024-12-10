# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class HrEmployeePlanningWizard(models.TransientModel):
	_name = 'hr.employee.planning.wizard'
	_description = 'Hr Employee Planning Wizard'

	assistance_planning_id = fields.Many2one('hr.assistance.planning','Planificacion Asistencia',ondelete='cascade')
	employees = fields.Many2many('hr.employee', 'hr_employee_planning_rel','assistance_planning_id','employee_id',
								 string=u'Empleados', required=True)
	company_id = fields.Many2one('res.company', string=u'Compañia', required=True, default=lambda self: self.env.company, readonly=True)

	def insert(self):
		vals = []
		for employee in self.employees:
			val = {
				'assistance_employee_id': self.assistance_planning_id.id,
				'calendar_id': employee.resource_calendar_id.id,
				'work_location_id': employee.work_location_id.id,
				'employee_id': employee.id
			}
			vals.append(val)
		self.env['hr.assistance.planning.employee'].create(vals)