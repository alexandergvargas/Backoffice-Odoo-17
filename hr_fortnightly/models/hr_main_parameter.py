# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	fortnightly_type = fields.Selection([('assistance','Tareo de Asistencias'),('percentage','Porcentaje')],string='Tipo de Calculo')
	tasa = fields.Float(string='Porcentaje',digits=(12,2))
	fortnightly_input_id = fields.Many2one('hr.payslip.input.type', string='Input Quincena')

	compute_afiliacion = fields.Boolean(string="Calcular Afiliacion", default=False)
	compute_af = fields.Boolean(string="Calcular Asig Fam", default=True)
	net_fortnightly_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Neto Quincenal', required=True)

	# quin_advance_id = fields.Many2one('hr.advance.type', string='Tipo de Adelanto')
	# quin_loan_id = fields.Many2one('hr.loan.type', string='Tipo de Prestamo')
	@api.onchange('fortnightly_type')
	def get_worked_days_lines(self):
		for rec in self:
			structure = self.env['hr.payroll.structure'].search([('name', '=', 'ADE_QUINCENAL')], limit=1)
			if structure:
				if rec.fortnightly_type == 'percentage':
					# print("structure",structure)
					structure.use_worked_day_lines = False
				elif rec.fortnightly_type == 'assistance':
					structure.use_worked_day_lines = True

	def check_quincena_values(self):
		if not self.fortnightly_input_id or \
			not self.net_fortnightly_sr_id:
			raise UserError(u'Faltan Configuraciones en la Pestaña de Adelantos Quincenales del Menu de Parametros Principales')