# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

class HrAdvanceType(models.Model):
	_name = 'hr.advance.type'
	_description = 'Advance Type'

	name = fields.Char(string='Nombre')
	input_id = fields.Many2one('hr.payslip.input.type', string='Input de Planillas')
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id)

	def get_advance_wizard(self):
		wizard = self.env['hr.advance.loan.wizard'].create({'name':'Duplicar Tipos de Adelanto'})
		return {
			'type':'ir.actions.act_window',
			'res_id':wizard.id,
			'view_mode':'form',
			'res_model':'hr.advance.loan.wizard',
			'views':[[self.env.ref('hr_advances_and_loans.hr_duplicate_advance_wizard_form').id,'form']],
			'context': self._context,
			'target':'new'
		}

class HrAdvance(models.Model):
	_name = 'hr.advance'
	_description = 'Adelanto'
	_inherit = ['mail.thread']

	name = fields.Char()
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True)
	employee_id = fields.Many2one('hr.employee', string='Empleado',tracking=True)
	amount = fields.Float(string='Monto',tracking=True)
	date = fields.Date(string='Fecha de Adelanto')
	discount_date = fields.Date(string='Fecha de Descuento',tracking=True)
	advance_type_id = fields.Many2one('hr.advance.type', string='Tipo de Adelanto',tracking=True)
	state = fields.Selection([('not payed', 'No Pagado'), ('paid out', 'Pagado')], default='not payed',string='Estado',tracking=True)
	observations = fields.Text(string='Observaciones')

	active = fields.Boolean(string='Activo', default=True)

	def turn_paid_out(self):
		for record in self:
			record.state = 'paid out'

	def set_not_payed(self):
		self.state = 'not payed'

	@api.onchange('employee_id', 'advance_type_id')
	def _get_name(self):
		for record in self:
			if record.advance_type_id and record.employee_id:
				record.name = '%s %s' % (record.advance_type_id.name, record.employee_id.name)

	def unlink(self):
		for advance in self:
			if advance.state in ('paid out'):
				raise UserError("No puedes eliminar una adelanto que ya fue Aplicado.")
		return super(HrAdvance, self).unlink()