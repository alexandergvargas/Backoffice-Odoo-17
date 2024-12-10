# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	# basic_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Basico')
	vacation_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Vacaciones')
	# household_allowance_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Asignacion Familiar')
	# commi_sr_ids = fields.Many2many('hr.salary.rule', 'sr_commi_main_parameter_rel', 'main_parameter_id', 'sr_id', string='RR. SS. Comisiones')
	# extra_hours_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Sobretiempo')
	otros_sr_ids = fields.Many2many('hr.salary.rule', 'sr_otros_main_parameter_rel', 'main_parameter_id', 'sr_id', string='R. S. Otros Ingresos')
	lack_sr_ids = fields.Many2many('hr.salary.rule', 'lack_main_parameter_rel', 'main_parameter_id', 'sr_id', string='R. S. Descuentos por Inasistencias')
	maternidad_input_id = fields.Many2one('hr.payslip.input.type', string='Input Maternidad')
	# maternidad_wd_id = fields.Many2one('hr.work.entry.type', string='Worked Day Maternidad')
	enfermedad_input_id = fields.Many2one('hr.payslip.input.type', string='Input Enfermedad')
	# enfermedad_wd_id = fields.Many2one('hr.work.entry.type', string='Worked Day Enfermedad')

	def check_maternidad_values(self):
		if not self.maternidad_input_id or \
			not self.enfermedad_input_id or \
			not self.vacation_sr_id or \
			not self.household_allowance_sr_id or \
			not self.commission_sr_ids or \
			not self.extra_hours_sr_id or \
			not self.otros_sr_ids or \
			not self.lack_sr_ids:
			raise UserError(u'Faltan Configuraciones en la Pestaña de Subsidios del Menu de Parametros Principales')
