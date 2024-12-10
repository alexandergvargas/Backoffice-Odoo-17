# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	def import_subsidies(self):
		# MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		log = ''
		for record in self:
			sql = """
				select sum(hsp.total_sub) as amount,
				sum(hsp.days) as days,
				hsp.maternidad_input_id,
				--hsp.maternidad_wd_id,
				hsp.enfermedad_input_id,
				--hsp.enfermedad_wd_id,
				hs.type
				from hr_subsidies_periodo hsp
				left join hr_subsidies hs on hs.id = hsp.subsidies_id
				where hsp.periodo_id = {0} and
					  hsp.employee_id = {1} and
					  hsp.validation = 'not payed'
				group by hsp.maternidad_input_id,hsp.enfermedad_input_id,hs.type
				""".format(record.payslip_run_id.periodo_id.id, record.employee_id.id)
			self._cr.execute(sql)
			data = self._cr.dictfetchall()
			for line in data:
				if line['type'] == 'maternity':
					inp_line = record.input_line_ids.filtered(lambda inp: inp.input_type_id.id == line['maternidad_input_id'])
					inp_line.amount = line['amount']
					# WDLine = record.worked_days_line_ids.filtered(lambda wd: wd.work_entry_type_id.id == line['maternidad_wd_id'])
					# dia_line = record.worked_days_line_ids.filtered(lambda wd: wd.work_entry_type_id == MainParameter.payslip_working_wd)
					# WDLine.number_of_days = line['days'] if line['days']<=30 else 30
					# dia_line.number_of_days = 30-WDLine.number_of_days
				else:
					inp_line = record.input_line_ids.filtered(lambda inp: inp.input_type_id.id == line['enfermedad_input_id'])
					inp_line.amount = line['amount']
					# WDLine = record.worked_days_line_ids.filtered(lambda wd: wd.work_entry_type_id.id == line['enfermedad_wd_id'])
					# dia_line = record.worked_days_line_ids.filtered(lambda wd: wd.work_entry_type_id == MainParameter.payslip_working_wd)
					# WDLine.number_of_days = line['days'] if line['days']<=30 else 30
					# dia_line.number_of_days = 30-WDLine.number_of_days
			self.env['hr.subsidies.periodo'].search([('periodo_id', '=', record.payslip_run_id.periodo_id.id),
											('employee_id', '=', record.employee_id.id),
											('validation', '=', 'not payed')]).turn_paid_out()
			if data:
				log += '%s\n' % record.employee_id.name
		if log:
			return self.env['popup.it'].get_message('Se importo los subsidios de los siguientes empleados:\n' + log)
		else:
			return self.env['popup.it'].get_message('No se importo ningun subsidio')