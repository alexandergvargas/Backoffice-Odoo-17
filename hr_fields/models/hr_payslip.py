# -*- coding:utf-8 -*-

from odoo import api, fields, models,Command, _
from odoo.exceptions import UserError
from odoo.tools import float_round, date_utils, convert_file, html2plaintext, is_html_empty, format_amount
from dateutil.relativedelta import relativedelta
from calendar import *

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'
	_order = 'employee_id'

	# income = fields.Monetary(compute='_compute_basic_net', string='total Ingresos', store=True)
	worker_contributions = fields.Monetary(compute='_compute_basic_net', string='Aportes Trabajador', store=True)
	net_discounts = fields.Monetary(compute='_compute_basic_net', string='Dsctos al Neto', store=True)
	# net_to_pay = fields.Monetary(compute='_compute_basic_net', string='Neto a Pagar', store=True)
	employer_contributions = fields.Monetary(compute='_compute_basic_net', string='Aportes Empleador', store=True)
	# holidays = fields.Integer(string='Dias Feriados y Domingos')
	basic_wage = fields.Monetary(compute='_compute_basic_net',string='Basico', store=True)
	gross_wage = fields.Monetary(compute='_compute_basic_net',string='Total Ingresos', store=True)
	net_wage = fields.Monetary(compute='_compute_basic_net',string='Neto a Pagar', store=True)

	identification_id = fields.Char(string="N° Ident.")
	wage = fields.Monetary('Salario')
	labor_regime = fields.Selection([('general', 'Regimen General'),
									 ('small', 'Pequeña Empresa'),
									 ('micro', 'Micro Empresa'),
									 ('practice', 'Practicante'),
									 ('fourth-fifth', 'Trabajadores de 4ta-5ta')], default='general', string='Regimen Laboral')
	social_insurance_id = fields.Many2one('hr.social.insurance', string='Seguro Social')
	distribution_id = fields.Many2one('hr.analytic.distribution', string='Distribucion Analitica')
	# workday_id = fields.Many2one('hr.workday', string='Jornada Laboral')

	membership_id = fields.Many2one('hr.membership', string='Afiliacion')
	commision_type = fields.Selection([('flow','Flujo'),('mixed','Mixta')],string='Tipo de Comision')
	fixed_commision = fields.Float(string='Comis. Sobre Flujo %')
	mixed_commision = fields.Float(string='Comision Mixta %')
	prima_insurance = fields.Float(string='Prima de Seguros %')
	retirement_fund = fields.Float(string='Aporte Fondo de Pensiones %')
	insurable_remuneration = fields.Float(string='Remuneracion Asegurable')
	is_afp = fields.Boolean(related='membership_id.is_afp', string="is_afp", store=True)

	struct_type_id = fields.Many2one('hr.payroll.structure.type', string='Tipo de Planilla', related='')

	rmv = fields.Float('R.M.V.',default=1025)

	# currency_id = fields.Many2one(related="company_id.currency_id")

	# CAMPOS NATIVOS NO NECESARIOS (OPTIMIZACION DE CODIGO)
	has_refund_slip = fields.Boolean(compute='')
	warning_message = fields.Char(compute='')
	is_wrong_duration = fields.Boolean(compute='')
	is_regular = fields.Boolean(compute='')
	negative_net_to_report_display = fields.Boolean(compute='')
	negative_net_to_report_message = fields.Char(compute='')
	negative_net_to_report_amount = fields.Float(compute='')

	# salary_attachment_ids = fields.Many2many(compute='')
	# salary_attachment_count = fields.Integer(compute='')
	# input_line_ids = fields.One2many(compute='')
	# journal_id = fields.Many2one(related="")
	# worked_days_line_ids = fields.One2many(compute='')

	@api.model
	def _get_attachment_types(self):
		attachment_types = self.env['hr.salary.attachment.type'].search([])
		input_types = self.env['hr.payslip.input.type'].search([('code', 'in', attachment_types.mapped('code'))])
		# missing_input_types = list(set(attachment_types.mapped('code')) - set(input_types.mapped('code')))
		# if missing_input_types:
		# 	raise UserError(_("No se encontró otro tipo de entrada para los siguientes códigos de tipos de adjuntos salariales:\n%s", '\n'.join(missing_input_types)))
		result = {}
		for attachment_type in attachment_types:
			for input_type in input_types:
				if input_type.code == attachment_type.code:
					result[attachment_type.code] = input_type
					break
		# print("result",result)
		return result

	@api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
	def _compute_input_line_ids(self):
		attachment_types = self._get_attachment_types()
		# print("attachment_types",attachment_types)
		attachment_type_ids = [f.id for f in attachment_types.values()]
		# print("attachment_type_ids",attachment_type_ids)
		for slip in self:
			# if not slip.employee_id or not slip.employee_id.salary_attachment_ids or not slip.struct_id:
			# 	lines_to_remove = slip.input_line_ids.filtered(lambda x: x.input_type_id.id in attachment_type_ids)
			# 	slip.update({'input_line_ids': [Command.unlink(line.id) for line in lines_to_remove]})
			if slip.employee_id.salary_attachment_ids and slip.date_to:
				# print("slip.employee_id",slip.employee_id.name)
				lines_inputs = slip.input_line_ids.filtered(lambda x: x.input_type_id.id in attachment_type_ids)

				valid_attachments = slip.employee_id.salary_attachment_ids.filtered(lambda a: a.state == 'open' and a.date_start <= slip.date_to)
				# print("valid_attachments",valid_attachments)

				# Toma sólo los tipos de deducción presentes en la estructura.
				# deduction_types = list(set(valid_attachments.deduction_type_id.mapped('code')))
				# struct_deduction_lines = list(set(slip.struct_id.rule_ids.mapped('code')))
				# included_deduction_types = [f for f in deduction_types if attachment_types[f].code in struct_deduction_lines]
				# print("included_deduction_types", included_deduction_types)
				for input_type in lines_inputs:
					# for deduction_type in included_deduction_types:
					# 	if input_type.code == deduction_type:
					# 		if not slip.struct_id.rule_ids.filtered(lambda r: r.active and r.code == attachment_types[deduction_type].code):
					# 			continue
					attachments = valid_attachments.filtered(lambda a: a.deduction_type_id.code == input_type.code)
					# print("attachments", attachments)
					amount = sum(attachments.mapped('active_amount'))
					input_type.amount = amount

	def refresh_from_work_entries(self):
		# Actualiza todo el recibo de nómina en caso de que RRHH. haya modificado algunas entradas de trabajo después de la generación del recibo de nómina.
		if any(p.state not in ['draft', 'verify'] for p in self):
			raise UserError(_('Las nóminas deben estar en estado Borrador o En espera.'))

		if not self or self.env.context.get('salary_simulation'):
			return
		valid_slips = self.filtered(lambda p: p.employee_id and p.date_from and p.date_to and p.contract_id and p.struct_id)
		if not valid_slips:
			return
		# Garantizar que se generen entradas de trabajo para todos los contratos.
		# generate_from = min(p.date_from for p in self)
		# current_month_end = date_utils.end_of(fields.Date.today(), 'month')
		# generate_to = max(min(fields.Date.to_date(p.date_to), current_month_end) for p in valid_slips)
		# print("generate_from",generate_from)
		# print("generate_to",generate_to)
		# self.mapped('contract_id')._generate_work_entries(generate_from, generate_to)

		# MainParameter = self.env['hr.main.parameter'].get_main_parameter()

		for slip in valid_slips:
			if not slip.struct_id.use_worked_day_lines:
				continue
			# print("_get_worked_day_lines",slip._get_worked_day_lines())
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
							WD_DLAB.number_of_days = monthrange(slip.date_from.year, slip.date_from.month)[1] - slip.date_from.day + slip.contract_id.date_end.day - total_days

			else:
				for work_entries in slip._get_worked_day_lines():
					for wd in slip.worked_days_line_ids:
						if wd.work_entry_type_id.id == work_entries['work_entry_type_id']:
							# print("wd",wd.code)
							wd.number_of_days = work_entries['number_of_days']
							wd.number_of_hours = work_entries['number_of_hours']
			# slip.update({'worked_days_line_ids': slip._get_new_worked_days_lines()})
		# self.compute_sheet()
		return self.env['popup.it'].get_message('Se Actualizo con exito el tareaje')

	def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
		""":returns: una lista de dict que contiene los valores de días trabajados que deben aplicarse para el recibo de sueldo determinado"""
		res = []
		# cumplimentar sólo si el contrato está vinculado a un horario de trabajo
		self.ensure_one()
		contract = self.contract_id
		if contract.resource_calendar_id:
			res = self._get_worked_day_lines_values(domain=domain)
			# print("res",res)
			if not check_out_of_contract:
				return res

			# Si el contrato no cubre todo el mes, cree líneas de worked_days para adaptar el salario en consecuencia
			# out_days, out_hours = 0, 0
			# reference_calendar = self._get_out_of_contract_calendar()
			# print("reference_calendar",reference_calendar)
			# if self.date_from < contract.date_start:
			# 	start = fields.Datetime.to_datetime(self.date_from)
			# 	stop = fields.Datetime.to_datetime(contract.date_start) + relativedelta(days=-1, hour=23, minute=59)
			# 	out_time = reference_calendar.get_work_duration_data(start, stop, compute_leaves=False, domain=['|', ('work_entry_type_id', '=', False), ('work_entry_type_id.is_leave', '=', False)])
			# 	out_days += out_time['days']
			# 	out_hours += out_time['hours']
			# if contract.date_end and contract.date_end < self.date_to:
			# 	start = fields.Datetime.to_datetime(contract.date_end) + relativedelta(days=1)
			# 	stop = fields.Datetime.to_datetime(self.date_to) + relativedelta(hour=23, minute=59)
			# 	out_time = reference_calendar.get_work_duration_data(start, stop, compute_leaves=False, domain=['|', ('work_entry_type_id', '=', False), ('work_entry_type_id.is_leave', '=', False)])
			# 	out_days += out_time['days']
			# 	out_hours += out_time['hours']
			# if out_days or out_hours:
			# 	work_entry_type = self.env.ref('hr_payroll.hr_work_entry_type_out_of_contract')
			# 	res.append({
			# 		'sequence': work_entry_type.sequence,
			# 		'work_entry_type_id': work_entry_type.id,
			# 		'number_of_days': out_days,
			# 		'number_of_hours': out_hours,
			# 	})
		return res

	def _get_worked_day_lines_values(self, domain=None):
		self.ensure_one()
		res = []
		# hours_per_day = self._get_worked_day_lines_hours_per_day()
		work_hours = self.contract_id.get_work_hours(self.date_from, self.date_to, domain=domain)
		work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
		# print("work_hours_ordered",work_hours_ordered)

		work_days = self.contract_id.get_work_days(self.date_from, self.date_to, domain=domain)
		work_days_ordered = sorted(work_days.items(), key=lambda x: x[1])
		# print("work_days_ordered",work_days_ordered)

		biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
		add_days_rounding = 0
		for work_entry_type_day_id, days in work_days_ordered:
			for work_entry_type_id, hours in work_hours_ordered:
				if work_entry_type_day_id == work_entry_type_id:
					work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
					# print("work_entry_type",work_entry_type)
					# print("hours",hours)
					# days = round(hours / hours_per_day, 5) if hours_per_day else 0
					days = round(days, 2)
					# print("days",days)
					if work_entry_type_id == biggest_work:
						days += add_days_rounding
					day_rounded = self._round_days(work_entry_type, days)
					# print("day_rounded",day_rounded)
					add_days_rounding += (days - day_rounded)
					attendance_line = {
						'sequence': work_entry_type.sequence,
						'work_entry_type_id': work_entry_type_id,
						'number_of_days': day_rounded,
						'number_of_hours': hours,
					}
					res.append(attendance_line)

		# Sort by Work Entry Type sequence
		work_entry_type = self.env['hr.work.entry.type']
		return sorted(res, key=lambda d: work_entry_type.browse(d['work_entry_type_id']).sequence)

	def get_dlabs(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_voucher_values()
		#### WORKED DAYS ####
		DLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dlab.mapped('code'))
		# DNLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code'))
		DSUB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dsub.mapped('code'))
		DVAC = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dvac.mapped('code'))
		DOM = self.worked_days_line_ids.filtered(lambda wd: wd.code in ('DOM'))

		DIA_VAC = sum(DVAC.mapped('number_of_days'))
		DIA_SUB = sum(DSUB.mapped('number_of_days'))

		# if sum(DLAB.mapped('number_of_days'))==30:
		# if DIA_SUB == self.date_to.day:
		# 	return 0
		# elif DIA_VAC == self.date_to.day:
		# 	return 0
		# elif (DIA_SUB + DIA_VAC) == self.date_to.day:
		# 	return 0
		# else:
		return sum(DLAB.mapped('number_of_days')) - sum(DOM.mapped('number_of_days')) - DIA_SUB - DIA_VAC

	def generate_inputs_and_wd_lines(self, recompute=False):
		for payslip in self:
			if recompute:
				input_type_lines = payslip.input_line_ids.mapped('input_type_id')
			input_types = payslip.struct_id.mapped('input_line_type_ids')

			for type in input_types:
				vals = {'input_type_id': type.id,
						'payslip_id': payslip.id,
						'amount': 0,
						# 'code': type.code,
						# 'contract_id': payslip.contract_id.id,
						# 'struct_id': payslip.struct_id.id
						}
				if recompute and type not in input_type_lines:
					self.env['hr.payslip.input'].create(vals)
					# print("vals con recompute",vals)
				if not recompute:
					self.env['hr.payslip.input'].create(vals)
					# print("vals nuevo",vals)
			wd_type_lines = payslip.worked_days_line_ids.mapped('work_entry_type_id')
			wd_types = payslip.struct_id.mapped('wd_types_ids')
			# print("wd_type_lines",wd_type_lines.ids)
			# print("wd_types",wd_types)
			for type in wd_types:
				if type.id in wd_type_lines.ids:
					continue
				else:
					vals = {'work_entry_type_id': type.id,
							'payslip_id': payslip.id,
							}
				if recompute and type not in wd_type_lines:
					self.env['hr.payslip.worked_days'].create(vals)
				if not recompute:
					self.env['hr.payslip.worked_days'].create(vals)

	@api.depends('line_ids.total')
	def _compute_basic_net(self):
		line_values = (self._origin)._get_line_values(['BAS', 'TINGR', 'TAT', 'TDESN', 'NETO', 'AEM'])
		# print("line_values",line_values)
		for payslip in self:
			payslip.basic_wage = line_values['BAS'][payslip._origin.id]['total']
			payslip.gross_wage = line_values['TINGR'][payslip._origin.id]['total']
			payslip.worker_contributions = line_values['TAT'][payslip._origin.id]['total']
			payslip.net_discounts = line_values['TDESN'][payslip._origin.id]['total']
			payslip.net_wage = line_values['NETO'][payslip._origin.id]['total']
			payslip.employer_contributions = line_values['AEM'][payslip._origin.id]['total']

	def action_payslip_hecho(self):
		work_entries = self.env['hr.work.entry']
		for slip in self:
			work_entries |= self.env['hr.work.entry'].search([
				('date_start', '<=', slip.date_to),
				('date_stop', '>=', slip.date_from),
				('employee_id', '=', slip.employee_id.id),
			])
		if work_entries:
			work_entries.action_validate()
		return self.write({'state' : 'done'})

	def action_payslip_verify(self):
		work_entries = self.env['hr.work.entry']
		for slip in self:
			work_entries |= self.env['hr.work.entry'].search([
				('date_start', '<=', slip.date_to),
				('date_stop', '>=', slip.date_from),
				('employee_id', '=', slip.employee_id.id),
			])
		if work_entries:
			# print("work_entries",work_entries)
			work_entries.write({'state': 'draft'})
		return self.write({'state' : 'verify'})