# -*- coding:utf-8 -*-

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrFortnightly(models.Model):
	_name = 'hr.fortnightly'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Hr Fortnightly'
	_order = 'date_end desc'

	name = fields.Char(required=True)
	slip_ids = fields.One2many('hr.payslip', 'fortnightly_id', string='Nominas')
	state = fields.Selection([
		('draft', 'Nuevo'),
		('verify', 'Confirmado'),
		('exported', 'Exportado')], string='Estado', index=True, readonly=True, copy=False, default='draft')
	date_start = fields.Date(string='Desde', required=True, readonly=True,
							 default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
	date_end = fields.Date(string='Hasta', required=True, readonly=True,
						   default=lambda self: fields.Date.to_string(date.today().replace(day=15)))
	payslip_count = fields.Integer(compute='_compute_payslip_count')
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Planilla', required=True)
	company_id = fields.Many2one('res.company', string=u'Compañia', readonly=True, required=True, default=lambda self: self.env.company)


	def _compute_payslip_count(self):
		for payslip_run in self:
			payslip_run.payslip_count = len(payslip_run.slip_ids)

	def set_draft(self):
		self.slip_ids.action_payslip_cancel()
		self.slip_ids.unlink()
		self.state = 'draft'

	def compute_wds_by_lot(self):
		self.slip_ids.refresh_from_work_entries()
		return self.env['popup.it'].get_message('Se Actualizo con exito el tareaje')

	def recompute_payslips(self):
		self.slip_ids.generate_inputs_and_wd_lines(True)
		self.slip_ids.compute_sheet()

	def reopen_payroll(self):
		self.state = 'verify'
		self.slip_ids.action_payslip_verify()

	def action_open_payslips(self):
		self.ensure_one()
		return {
			"type": "ir.actions.act_window",
			"res_model": "hr.payslip",
			"views": [[False, "tree"], [False, "form"]],
			"domain": [['id', 'in', self.slip_ids.ids]],
			"context": {'default_fortnightly_id': self.id},
			"name": "Payslips",
		}

	@api.ondelete(at_uninstall=False)
	def _unlink_if_draft_or_cancel(self):
		if any(self.filtered(lambda payslip_run: payslip_run.state not in ('draft'))):
			raise UserError('¡No puede eliminar un lote de nómina que no sea borrador!')
		if any(self.mapped('slip_ids').filtered(lambda payslip: payslip.state not in ('draft', 'cancel'))):
			raise UserError('¡No puedes borrar una nómina que no esté en borrador o cancelada!')

	def _are_payslips_ready(self):
		return all(slip.state in ['done', 'cancel'] for slip in self.mapped('slip_ids'))

	def generate_wizard(self):
		return {
			'name': 'Adelanto Quincenal',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'hr.fortnightly.wizard',
			'context': {'default_date_start': self.date_start,
                        'default_date_end': self.date_end,
						'default_fortnightly_id': self.id},
			'target': 'new',
		}

	def set_amounts(self, line_ids, Lot, MainParameter):

		inp_adel_quince = MainParameter.fortnightly_input_id
		sr_neto_pagar = MainParameter.net_fortnightly_sr_id
		for line in line_ids:
			Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
			sr_neto = line.line_ids.filtered(lambda rs: rs.salary_rule_id == sr_neto_pagar)
			# print("sr_neto",sr_neto)
			for line_input in sr_neto:
				# print("line_input.amount",line_input.amount)
				extra_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_adel_quince)
				# print("extra_line.code",extra_line.code)
				extra_line.amount = line_input.amount

	def export_quincena(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		# MainParameter.check_gratification_values()
		Lot = self.payslip_run_id
		self.set_amounts(self.slip_ids, Lot, MainParameter)
		self.state = 'exported'
		self.slip_ids.action_payslip_hecho()
		return self.env['popup.it'].get_message('Se exporto exitosamente')

	def get_employees_news(self):
		wizard = self.env['hr.employee.news.fortnightly.wizard'].create({
			'fortnightly_id': self.id,
			'company_id':self.company_id.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_hr_employee_news_fortnightly_wizard' % module)
		return {
			'name':u'Seleccionar Empleados',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'hr.employee.news.fortnightly.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def tab_payroll(self):
		return {
			'name': 'Planilla Tabular',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'hr.planilla.tabular.fortnightly.wizard',
			'context': {'default_fortnightly_id': self.id},
			'target': 'new',
		}