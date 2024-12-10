# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
import calendar

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	# salary_attachment_ids = fields.Many2many(compute='')
	# salary_attachment_count = fields.Integer(compute='')
	# input_line_ids = fields.One2many(compute='')

	def action_refresh_from_work_entries(self):
		# Actualizar toda la nómina en caso de que HR haya modificado algunas entradas de trabajo después de la generación de la nómina
		if any(p.state not in ['draft', 'verify'] for p in self):
			# print("p.state",self.state)
			raise UserError(_('Las nóminas deben estar en estado Borrador o En espera.'))
		# self.mapped('worked_days_line_ids').unlink()
		# self.mapped('line_ids').unlink()
		# print("prueba entro en ausencias")
		# self._compute_worked_days_line_ids()
		# self.compute_sheet()

	def refresh_from_work_entries(self):
		# Actualiza todo el recibo de nómina en caso de que RRHH. haya modificado algunas entradas de trabajo después de la generación del recibo de nómina.
		if any(p.state not in ['draft', 'verify'] for p in self):
			raise UserError(_('Las nóminas deben estar en estado Borrador o En espera.'))

		if not self or self.env.context.get('salary_simulation'):
			return
		valid_slips = self.filtered(lambda p: p.employee_id and p.date_from and p.date_to and p.contract_id and p.struct_id)
		if not valid_slips:
			return

		# MainParameter = self.env['hr.main.parameter'].get_main_parameter()

		for slip in valid_slips:
			if not slip.struct_id.use_worked_day_lines:
				continue

			if slip.contract_id.work_entry_source == 'manual':
				WD_DLAB = slip.worked_days_line_ids.filtered(lambda line: line.code == 'DLAB')
				Contract = slip.contract_id

				# DIAS_FAL = slip.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code') or wd.code == 'FER').mapped('code')
				WD_DAYS = slip.worked_days_line_ids.filtered(lambda line: line.code != 'DLAB')

				total_days = sum(WD_DAYS.mapped('number_of_days'))
				# print("total_days",total_days)

				if Contract.date_start > slip.date_from and Contract.date_start <= slip.date_to:
					result = slip.date_to.day - Contract.date_start.day + 1
					WD_DLAB.number_of_days = result-total_days
				else:
					WD_DLAB.number_of_days = slip.date_to.day - total_days

				if slip.contract_id.situation_id.name == 'BAJA':
					if slip.date_from <= slip.contract_id.date_end <= slip.date_to:
						if slip.contract_id.date_start >= slip.date_from:
							WD_DLAB.number_of_days = slip.contract_id.date_end.day + 1 - slip.contract_id.date_start.day - total_days
						elif slip.date_from.month == slip.contract_id.date_end.month:
							WD_DLAB.number_of_days = slip.contract_id.date_end.day + 1 - slip.date_from.day - total_days
						else:
							WD_DLAB.number_of_days = calendar.monthrange(slip.date_from.year, slip.date_from.month)[1] - slip.date_from.day + slip.contract_id.date_end.day - total_days

			else:
				for work_entries in slip._get_worked_day_lines():
					# print("_get_worked_day_lines",slip._get_worked_day_lines())
					for wd in slip.worked_days_line_ids:
						# print("wd",wd.code)
						if wd.work_entry_type_id.id == work_entries['work_entry_type_id']:
							# print("wd",wd.code)
							wd.number_of_days = work_entries['number_of_days']
							wd.number_of_hours = work_entries['number_of_hours']
			# slip.update({'worked_days_line_ids': slip._get_new_worked_days_lines()})

			suspension_type_id = self.env['hr.suspension.type'].search([('code', '=', '23')], limit=1)
			leave_vacations = self.env['hr.leave'].search(['|',('request_date_from', '>=', slip.date_from),
														   ('request_date_to', '<=',slip.date_to),
														   ('employee_id', '=', slip.employee_id.id),
														   ('work_suspension_id', '=', suspension_type_id.id)])
			# print("leave_vacations",leave_vacations)
			to_create = []
			for leave in leave_vacations:
				dias_periodo = 0
				year_1 = leave.request_date_from.year
				year_2 = leave.request_date_to.year
				if year_1 == year_2:
					nro_meses = (leave.request_date_to.month - leave.request_date_from.month) + 1
				else:
					nro_meses = (13 - leave.request_date_from.month) + leave.request_date_to.month
				date = leave.request_date_from
				# print("date",date)
				# print("nro_meses",nro_meses)
				for c, fee in enumerate(range(nro_meses), 1):
					last_day = calendar.monthrange(date.year, date.month)[1]
					# print("last_day",last_day)
					if c == 1 and c != nro_meses:
						# print("c pri",c)
						date_from = leave.request_date_from
						date_to = leave.request_date_from.replace(day=last_day)
						dias_periodo = last_day - leave.request_date_from.day + 1
					elif c == nro_meses:
						# print("c ult",c)
						if c == 1:
							date_from = leave.request_date_from
							date_to = leave.request_date_to
							dias_periodo = leave.number_of_days
						else:
							date_from = leave.request_date_to.replace(day=1)
							date_to = leave.request_date_to
							dias_periodo = leave.request_date_to.day
					else:
						# print("c",c)
						date_from = slip.date_from
						date_to = slip.date_to
						dias_periodo = last_day
					# print("date_from",date_from)
					# print("date_to",date_to)
					# print("dias_periodo",dias_periodo)
					if slip.date_from <= date_from <= slip.date_to:
						# payslip_run_id = self.env['hr.payslip.run'].search([('date_start', '<=', date_from), ('date_end', '>=', date_from)], limit=1).id
						vals = {
							'leave_id': leave.id,
							'slip_id': slip.id,
							'days': dias_periodo,
							'accrued_period': slip.payslip_run_id.id,
							'motive': leave.holiday_status_id.name,
							'date_aplication': date_from,
							'request_date_from': date_from,
							'request_date_to': date_to,
						}
						to_create.append(vals)
						# print("vals",vals)
						leave.payslip_state = 'done'

			for v in to_create:
				hav = self.env['hr.accrual.vacation'].search([('leave_id', '=', v['leave_id']), ('slip_id', '=', v['slip_id'])])
				if len(hav):
					hav[0].write(v)
				else:
					self.env['hr.accrual.vacation'].create(v)

		# self.compute_sheet()
		return self.env['popup.it'].get_message('Se Actualizo con exito el tareaje')

