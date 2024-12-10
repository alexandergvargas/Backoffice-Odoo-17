# -*- coding:utf-8 -*-
from datetime import date, datetime, time
from odoo import api, fields, models, _
from collections import defaultdict
from odoo.exceptions import UserError
import pytz

class HrContract(models.Model):
	_inherit = 'hr.contract'

	structure_id = fields.Many2one('hr.payroll.structure', string='Estructura Salarial', required=True, tracking=True)
	worker_type_id = fields.Many2one('hr.worker.type', string='Tipo de Trabajador', help='TABLA 08 SUNAT')

	membership_id = fields.Many2one('hr.membership', string='Afiliacion', required=True, tracking=True)
	is_afp = fields.Boolean(string='Es AFP', related='membership_id.is_afp')
	commision_type = fields.Selection([('flow','Flujo'),('mixed','Mixta')],string='Tipo Comision AFP', tracking=True)
	cuspp = fields.Char(string='CUSPP', tracking=True)
	social_insurance_id = fields.Many2one('hr.social.insurance', string='Seguro Social', tracking=True)
	distribution_id = fields.Many2one('hr.analytic.distribution', string='Distribucion Analitica', required=True, tracking=True)
	# workday_id = fields.Many2one('hr.workday', string='Jornada Laboral', required=True)
	situation_id = fields.Many2one('hr.situation', string='Situacion', required=True, help='TABLA 15 SUNAT', tracking=True)
	situation_code = fields.Char(related='situation_id.code')
	situation_reason_id = fields.Many2one('hr.reasons.leave',string='Motivo de Baja', help='TABLA 17 SUNAT')
	labor_regime = fields.Selection([('general', 'Regimen General'),
									 ('small', 'Pequeña Empresa'),
									 ('micro', 'Micro Empresa'),
									 ('practice', 'Practicante'),
									 ('fourth-fifth', 'Trabajadores de 4ta-5ta')], default='general', string='Regimen Laboral', required=True, tracking=True)
	less_than_four = fields.Boolean(string='Trabajador con menos de 4 Horas al dia', default=False, tracking=True)
	other_employers = fields.Boolean(string='Otros Empleadores', default=False, help='Otros Empleadores por Rentas de Quinta Categoria')
	# sctr_id = fields.Many2one('hr.sctr', string='SCTR')
	exception = fields.Selection([('L', 'Licencia sin remuneracion en el mes'),
								  ('U', 'Subsidio pagado directamente por ESSALUD'),
								  ('J', 'Pensionado por jubilacion en el mes'),
								  ('I', 'Pensionado por invalidez en el mes'),
								  ('P', 'Relacion laboral inicio despues del cierre de planillas'),
								  ('O', 'Otro Motivo')
								], string='Excepcion de aportar',
								help="""
									L - No corresponde aportar debido a licencia sin renumeracion. \n
									U - No corresponde aportar porque existe un subsidio pagado directamente por essalud y en el mes, no hubo remuneracion pagada por el empleador. \n
									J - No corresponde aportar porque el trabajador se encuentra jubilado. \n
									I - No corresponde aportar porque el trabajador pensionado por invalidez en el mes. \n
									P - No corresponde aportar debido a que la relacion laboral se inicio en el mes despues del cierre de planillas , el aporte del mes se incluira en el mes siguiente. \n
									O - No corresponde aportar debido a otro motivo , no hubo remuneracion en el mes.
								""")
	work_type = fields.Selection([('N', 'Dependiente Normal'),
								  ('C', 'Dependiente Construccion'),
								  ('M', 'Dependiente Mineria'),
								  ('P', 'Dependiente Pesqueria')
								], string='Tipo de Trabajo')

	is_older = fields.Boolean(string='Es Mayor a 65 Años', default=False, help="Resolución SBS N° 938-2001 Trabajadores jubilados y mayores a 65 años")

	hr_responsible_id = fields.Many2one(default=lambda self: self.env.user)

	work_suspension_ids = fields.One2many('hr.work.suspension', 'contract_id')

	contributions_ids = fields.Many2many('hr.contributions', 'contract_contribution_rel', 'contract_id', 'contribution_id', string="Contribuciones")

	work_entry_source = fields.Selection([('calendar', 'Horario de Trabajo'),('manual', 'Manual')], default='calendar',string='Origen Entrada de Trabajo')

	# work_entry_source = fields.Selection(
	# 	selection_add=[('manual', 'Manual')],
	# 	ondelete={'manual': 'set default'},
	# )

	wage_type = fields.Selection([
		('monthly', 'Valorizar Tareo en funcion a Dias'),
		('hourly', 'Valorizar Tareo en funcion a Horas')
	], string="Tipo de Calculo", default='monthly', compute='', store=True, readonly=False)
	# schedule_pay = fields.Selection(compute='', default='monthly')
	hourly_wage = fields.Monetary('Salario por Dia', tracking=True, help="Salario Basico por dia del empleado.")

	def _generate_work_entries(self, date_start, date_stop, force=False):
		# Generate work entries between 2 dates (datetime.datetime)
		# Este método considera que las fechas están correctamente localizadas
		# basado en la zona horaria de destino
		assert isinstance(date_start, datetime)
		assert isinstance(date_stop, datetime)
		self = self.with_context(tracking_disable=True)
		canceled_contracts = self.filtered(lambda c: c.state == 'cancel')
		if canceled_contracts:
			raise UserError(
				_("Lo sentimos, no se permite generar entradas de trabajo a partir de contratos cancelados.") + '\n%s' % (
					', '.join(canceled_contracts.mapped('name'))))
		vals_list = []
		self.write({'last_generation_date': fields.Date.today()})

		intervals_to_generate = defaultdict(lambda: self.env['hr.contract'])
		# In case the date_generated_from == date_generated_to, move it to the date_start to
		# avoid trying to generate several months/years of history for old contracts for which
		# we've never generated the work entries.
		self.filtered(lambda c: c.date_generated_from == c.date_generated_to).write({
			'date_generated_from': date_start,
			'date_generated_to': date_start,
		})
		utc = pytz.timezone('UTC')
		for contract in self:
			if contract.work_entry_source != 'manual':
				contract_tz = (contract.resource_calendar_id or contract.employee_id.resource_calendar_id).tz
				tz = pytz.timezone(contract_tz) if contract_tz else pytz.utc
				contract_start = tz.localize(fields.Datetime.to_datetime(contract.date_start)).astimezone(utc).replace(tzinfo=None)
				contract_stop = datetime.combine(fields.Datetime.to_datetime(contract.date_end or datetime.max.date()), datetime.max.time())
				if contract.date_end:
					contract_stop = tz.localize(contract_stop).astimezone(utc).replace(tzinfo=None)
				if date_start > contract_stop or date_stop < contract_start:
					continue
				date_start_work_entries = max(date_start, contract_start)
				date_stop_work_entries = min(date_stop, contract_stop)
				if force:
					intervals_to_generate[(date_start_work_entries, date_stop_work_entries)] |= contract
					continue

				# Para cada contrato, encontramos cada intervalo que debemos generar.
				# En algunos casos no queremos configurar las fechas generadas de antemano, ya que las entradas de trabajo basadas en asistencia son más dinámicas
				# queremos actualizar las fechas dentro de la función _get_work_entries_values
				is_static_work_entries = contract.has_static_work_entries()
				last_generated_from = min(contract.date_generated_from, contract_stop)
				if last_generated_from > date_start_work_entries:
					if is_static_work_entries:
						contract.date_generated_from = date_start_work_entries
					intervals_to_generate[(date_start_work_entries, last_generated_from)] |= contract

				last_generated_to = max(contract.date_generated_to, contract_start)
				if last_generated_to < date_stop_work_entries:
					if is_static_work_entries:
						contract.date_generated_to = date_stop_work_entries
					intervals_to_generate[(last_generated_to, date_stop_work_entries)] |= contract

		for interval, contracts in intervals_to_generate.items():
			date_from, date_to = interval
			vals_list.extend(contracts._get_work_entries_values(date_from, date_to))

		if not vals_list:
			return self.env['hr.work.entry']

		return self.env['hr.work.entry'].create(vals_list)

	# funciones para computar dias en hr_payslip
	def get_work_days(self, date_from, date_to, domain=None):
		# Get work hours between 2 dates (datetime.date)
		# To correctly englobe the period, the start and end periods are converted
		# using the calendar timezone.
		assert not isinstance(date_from, datetime)
		assert not isinstance(date_to, datetime)

		date_from = datetime.combine(fields.Datetime.to_datetime(date_from), datetime.min.time())
		date_to = datetime.combine(fields.Datetime.to_datetime(date_to), datetime.max.time())
		work_data = defaultdict(int)

		contracts_by_company_tz = defaultdict(lambda: self.env['hr.contract'])
		for contract in self:
			contracts_by_company_tz[(
				contract.company_id,
				(contract.resource_calendar_id or contract.employee_id.resource_calendar_id).tz
			)] += contract
		utc = pytz.timezone('UTC')

		for (company, contract_tz), contracts in contracts_by_company_tz.items():
			tz = pytz.timezone(contract_tz) if contract_tz else pytz.utc
			date_from_tz = tz.localize(date_from).astimezone(utc).replace(tzinfo=None)
			date_to_tz = tz.localize(date_to).astimezone(utc).replace(tzinfo=None)
			work_data_tz = contracts.with_company(company).sudo()._get_work_days(
				date_from_tz, date_to_tz, domain=domain)
			for work_entry_type_id, days in work_data_tz.items():
				work_data[work_entry_type_id] += days
		return work_data

	def _get_work_days(self, date_from, date_to, domain=None):
		assert isinstance(date_from, datetime)
		assert isinstance(date_to, datetime)

		# First, found work entry that didn't exceed interval.
		work_entries = self.env['hr.work.entry']._read_group(
			self._get_work_hours_domain(date_from, date_to, domain=domain, inside=True),
			['work_entry_type_id'],
			['cant_dias:sum']
		)
		work_data = defaultdict(int)
		work_data.update({work_entry_type.id: duration_sum for work_entry_type, duration_sum in work_entries})
		self._preprocess_work_hours_data(work_data, date_from, date_to)

		# Second, find work entry that exceeds interval and compute right duration.
		work_entries = self.env['hr.work.entry'].search(self._get_work_hours_domain(date_from, date_to, domain=domain, inside=False))

		for work_entry in work_entries:
			date_start = max(date_from, work_entry.date_start)
			date_stop = min(date_to, work_entry.date_stop)
			if work_entry.work_entry_type_id.is_leave:
				contract = work_entry.contract_id
				calendar = contract.resource_calendar_id
				employee = contract.employee_id
				contract_data = employee._get_work_days_data_batch(
					date_start, date_stop, compute_leaves=False, calendar=calendar
				)[employee.id]

				work_data[work_entry.work_entry_type_id.id] += contract_data.get('hours', 0)
			else:
				work_data[work_entry.work_entry_type_id.id] += work_entry._get_work_duration(date_start, date_stop)  # Number of hours
		return work_data


	####Esta función ayuda a obtener el primer contrato del empleado utilizando la situación como condicional para obtenerlo.
	def get_first_contract(self, employee, last_contract=False):
		domain = [('employee_id', '=', employee.id), ('date_start', '<=', last_contract.date_start)] if last_contract else [('employee_id', '=', employee.id)]
		Contracts = self.search(domain, order='date_start desc')
		aux, roll_back = None, None
		delimiter = len(Contracts)
		if delimiter > 1:
			for c, Contract in enumerate(Contracts):
				if Contract.situation_id.code == '0' and c == 0:
					aux = [Contract, c]
					continue
				if Contract.situation_id.code == '0' and aux and c - aux[1] == 1:
					return aux[0]
				if Contract.situation_id.code == '0' and aux and not c - aux[1] == 1:
					return roll_back
				if Contract.situation_id.code == '0' and not aux:
					return roll_back
				if Contract.situation_id.code != '0' and delimiter - 1 == c:
					return Contract
				roll_back = Contract
		else:
			return Contracts

class HrWorkSuspension(models.Model):
	_name = 'hr.work.suspension'
	_description = 'Hr Work Suspension'
	_order = 'request_date_from'

	contract_id = fields.Many2one('hr.contract', string='Contrato')
	employee_id = fields.Many2one('hr.employee', string='Empleado')
	request_date_from = fields.Date('Fecha Inicio')
	request_date_to = fields.Date('Fecha Fin')
	suspension_type_id = fields.Many2one('hr.suspension.type', string='Tipo de Suspension', required=True, help='TABLA 21 SUNAT')
	reason = fields.Char(string='Motivo')
	days = fields.Integer(string='Nro. Dias')
	# payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo', required=True)
	periodo_id = fields.Many2one('hr.period',string=u'Periodo',required=True)