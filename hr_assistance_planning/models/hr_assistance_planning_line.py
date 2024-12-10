# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import date, datetime, timedelta, time
from dateutil.relativedelta import relativedelta
import logging
import pytz
from math import modf

from odoo import api, fields, models, _
from odoo.addons.resource.models.utils import Intervals, sum_intervals, string_to_datetime
from odoo.addons.resource.models.resource_mixin import timezone_datetime
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_utils, format_datetime, get_timedelta

_logger = logging.getLogger(__name__)

def days_span(start_datetime, end_datetime):
	if not isinstance(start_datetime, datetime):
		raise ValueError
	if not isinstance(end_datetime, datetime):
		raise ValueError
	end = datetime.combine(end_datetime, datetime.min.time())
	start = datetime.combine(start_datetime, datetime.min.time())
	duration = end - start
	return duration.days + 1

class HrAssistancePlanningLine(models.Model):
	_name='hr.assistance.planning.line'
	_description='Planificación de asistencia detalle'
	_order = 'start_datetime desc, id desc'
	_rec_name = 'name'
	_check_company_auto = True

	def _default_start_datetime(self):
		return datetime.combine(fields.Date.context_today(self), time.min)

	def _default_end_datetime(self):
		return datetime.combine(fields.Date.context_today(self), time.max)

	# CAMPOS DE ODOO 15 PERSONALIZADOS
	assistance_planning_id = fields.Many2one('hr.assistance.planning','Planificacion Asistencia',ondelete='cascade')
	is_day_rest = fields.Boolean(u'Día de descanso')
	fecha = fields.Date('Fecha',compute='_compute_fecha',store=True)
	horario = fields.Char('Horario',compute='_compute_horario',store=True)
	day_name = fields.Char('Día', compute='_compute_fecha',store=True)
	lunch_time = fields.Float('Refrigerio')

	# CAMPOS NATIVOS DE PLANIFICACION
	name = fields.Text('Nota')
	resource_id = fields.Many2one('resource.resource', 'Empleado', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", group_expand='_group_expand_resource_id')
	resource_type = fields.Selection(related='resource_id.resource_type')
	resource_color = fields.Integer(related='resource_id.color', string="Color del recurso")
	employee_id = fields.Many2one('hr.employee', 'Employee', compute='_compute_employee_id', store=True)
	work_email = fields.Char("Correo electrónico", related='employee_id.work_email')
	work_location_id = fields.Many2one('hr.work.location', string="Establecimiento") #service_location_id
	department_id = fields.Many2one(related='employee_id.department_id', store=True)
	user_id = fields.Many2one('res.users', string="Usuario", related='resource_id.user_id', store=True, readonly=True)
	job_title = fields.Char(related='employee_id.job_title')

	company_id = fields.Many2one('res.company',u'Compañía',required=True, default=lambda self: self.env.company,readonly=True)
	role_id = fields.Many2one('attendance.activity', string="Tipo de Turno", compute="_compute_role_id", store=True, readonly=False, copy=True, group_expand='_read_group_role_id',
							  help="Defina los tipos de turnos que desempeñan sus empleados (por ejemplo: mañana, tarde, noche...). Crea turnos abiertos para los horarios que necesitas. Luego asigna esos turnos abiertos a los empleados que estén disponibles.")
	color = fields.Integer("Color", compute='_compute_color')
	was_copied = fields.Boolean("Este cambio fue copiado de la semana anterior", default=False, readonly=True)

	start_datetime = fields.Datetime("Fecha de Inicio", compute='_compute_datetime', store=True, readonly=False, required=True,copy=True)
	end_datetime = fields.Datetime("Fecha Final", compute='_compute_datetime', store=True, readonly=False, required=True, copy=True)

	# Campos y advertencias de la interfaz de usuario
	conflicting_slot_ids = fields.Many2many('hr.assistance.planning.line', compute='_compute_overlap_slot_count')
	overlap_slot_count = fields.Integer('Slots superpuestos', compute='_compute_overlap_slot_count',	search='_search_overlap_slot_count')
	is_past = fields.Boolean('¿Es este cambio en el pasado?', compute='_compute_past_shift')

	# asignación de tiempo
	allocation_type = fields.Selection([
		('planning', 'Planificación'),
		('forecast', 'Pronóstico')], compute='_compute_allocation_type')
	allocated_hours = fields.Float("Horas Asignadas", compute='_compute_allocated_hours', store=True, readonly=False)
	allocated_percentage = fields.Float("Tiempo Asignado %", default=100, compute='_compute_allocated_percentage', store=True, readonly=False, group_operator="avg")
	working_days_count = fields.Float("Días laborables", compute='_compute_working_days_count', store=True)
	duration = fields.Float("Duracion", compute="_compute_slot_duration")

	# publicación y envío
	publication_warning = fields.Boolean("Modificado desde la última publicación", default=False, compute='_compute_publication_warning',store=True, readonly=True, copy=False,
		help="Si está marcado, significa que el contenido del turno ha cambiado desde su última publicación.")
	state = fields.Selection([
		('draft', 'Borrador'),
		('published', 'Publicado'),], string='Estado', default='draft')

	# campos ficticios de plantilla (solo para fines de interfaz de usuario)
	template_autocomplete_ids = fields.Many2many('hr.shift.template', store=False, compute='_compute_template_autocomplete_ids')
	template_id = fields.Many2one('hr.shift.template', string='Plantillas de Turnos', compute='_compute_template_id', readonly=False, store=True)
	template_reset = fields.Boolean()
	previous_template_id = fields.Many2one('hr.shift.template')

	# Recurrente (los campos `repeat_` no se almacenan, solo se usan para fines de interfaz de usuario)
	recurrency_id = fields.Many2one('hr.assistance.planning.recurrency', readonly=True, index=True, ondelete="set null", copy=False)
	repeat = fields.Boolean("Repetir", compute='_compute_repeat', inverse='_inverse_repeat',
							help="Para evitar contaminar su base de datos y problemas de rendimiento, los turnos solo se crean para los próximos 6 meses. Luego se crean gradualmente a medida que pasa el tiempo para tener siempre turnos con 6 meses de anticipación. Este valor se puede modificar desde la configuración de Planificación, en modo de depuración.")
	repeat_interval = fields.Integer("Repite cada", default=1, compute='_compute_repeat_interval', inverse='_inverse_repeat')
	repeat_unit = fields.Selection([
		('day', 'Dias'),
		('week', 'Semanas'),
		('month', 'Meses'),
		('year', 'Años'),], default='day', compute='_compute_repeat_unit', inverse='_inverse_repeat', required=True)
	repeat_type = fields.Selection([('forever', 'Por siempre'), ('until', 'Hasta'), ('x_times', 'Numero de Ocurrencias')],
								   string='Tipo de repetición', default='until', compute='_compute_repeat_type',inverse='_inverse_repeat')
	repeat_until = fields.Date("Repetir Hasta", compute='_compute_repeat_until', inverse='_inverse_repeat')
	repeat_number = fields.Integer("Repeticiones", default=1, compute='_compute_repeat_number', inverse='_inverse_repeat')
	recurrence_update = fields.Selection([
		('this', 'Este Turno'),
		('subsequent', 'Este y los siguientes turnos'),
		('all', 'Todos los turnos'),
	], default='this', store=False)
	confirm_delete = fields.Boolean('Confirmar la eliminación de Slots', compute='_compute_confirm_delete')

	_sql_constraints = [
		('check_start_date_lower_end_date', 'CHECK(end_datetime > start_datetime)','La fecha de finalización de un turno debe ser posterior a su fecha de inicio.'),
		('check_allocated_hours_positive', 'CHECK(allocated_hours >= 0)','Las horas asignadas y el porcentaje de tiempo asignado no pueden ser negativos.'),
	]

	# FUNCIONES NUEVAS
	@api.depends('start_datetime')
	def _compute_fecha(self):
		for slot in self:
			if slot.start_datetime:
				datetime_obj = (slot.start_datetime-timedelta(hours=5)).date()
				# print("datetime_obj", datetime_obj)
				if datetime_obj.weekday()==0:
					dia='Lunes'
				elif datetime_obj.weekday()==1:
					dia='Martes'
				elif datetime_obj.weekday()==2:
					dia='Miercoles'
				elif datetime_obj.weekday()==3:
					dia='Jueves'
				elif datetime_obj.weekday()==4:
					dia='Viernes'
				elif datetime_obj.weekday()==5:
					dia='Sábado'
				elif datetime_obj.weekday()==6:
					dia='Domingo'
				slot.fecha = datetime_obj
				slot.day_name = dia
			else:
				slot.fecha = False
				slot.day_name = False

	@api.depends('start_datetime','end_datetime')
	def _compute_horario(self):
		for slot in self:
			if slot.start_datetime and slot.end_datetime:
				# formato de salida ---> '07:30 - 19:45'
				slot.horario = str((slot.start_datetime-timedelta(hours=5)).hour).rjust(2,'0')+':'+str((slot.start_datetime-timedelta(hours=5)).minute).rjust(2,'0')+' - '\
							+str((slot.end_datetime-timedelta(hours=5)).hour).rjust(2,'0')+':'+str((slot.end_datetime-timedelta(hours=5)).minute).rjust(2,'0')
				# print("slot.hora", slot.hora)
			else:
				slot.horario = False

	# FUNCIONES NATIVAS
	@api.depends('role_id.color', 'resource_id.color')
	def _compute_color(self):
		for slot in self:
			slot.color = slot.role_id.color or slot.resource_id.color

	@api.depends('repeat_until', 'repeat_number')
	def _compute_confirm_delete(self):
		for slot in self:
			if slot.recurrency_id and slot.repeat_until and slot.repeat_number:
				recurrence_end_dt = slot.repeat_until or slot.recurrency_id._get_recurrence_last_datetime()
				slot.confirm_delete = fields.Date.to_date(recurrence_end_dt) > slot.repeat_until
			else:
				slot.confirm_delete = False

	@api.constrains('repeat_until')
	def _check_repeat_until(self):
		if any([slot.repeat_until and slot.repeat_until < slot.start_datetime.date() for slot in self]):
			raise UserError("La fecha de finalización de la repeticion debe ser posterior a la fecha de inicio del turno.")

	@api.onchange('repeat_until')
	def _onchange_repeat_until(self):
		self._check_repeat_until()

	@api.depends('start_datetime')
	def _compute_past_shift(self):
		now = fields.Datetime.now()
		for slot in self:
			if slot.end_datetime:
				if slot.end_datetime < now:
					slot.is_past = True
				else:
					slot.is_past = False
			else:
				slot.is_past = False

	@api.depends('resource_id.employee_id', 'resource_type')
	def _compute_employee_id(self):
		for slot in self:
			slot.employee_id = slot.resource_id.with_context(
				active_test=False).employee_id if slot.resource_type == 'user' else False

	@api.depends('employee_id', 'template_id')
	def _compute_role_id(self):
		for slot in self:
			if not slot.role_id:
				slot.role_id = slot.resource_id.default_types_shift_id
			if slot.template_id:
				slot.previous_template_id = slot.template_id
				if slot.template_id.role_id:
					slot.role_id = slot.template_id.role_id
			elif slot.previous_template_id and not slot.template_id and slot.previous_template_id.role_id == slot.role_id:
				slot.role_id = False

	@api.depends('start_datetime', 'end_datetime')
	def _compute_allocation_type(self):
		for slot in self:
			if slot.start_datetime and slot.end_datetime and slot._get_slot_duration() < 24:
				slot.allocation_type = 'planning'
			else:
				slot.allocation_type = 'forecast'

	@api.depends('start_datetime', 'end_datetime', 'employee_id.resource_calendar_id', 'allocated_hours')
	def _compute_allocated_percentage(self):
		allocated_hours_field = self._fields['allocated_hours']
		slots = self.filtered(lambda slot: not self.env.is_to_compute(allocated_hours_field,slot) and slot.start_datetime and slot.end_datetime and slot.start_datetime != slot.end_datetime)
		if not slots:
			return
		# if there are at least one slot having start or end date, call the _get_valid_work_intervals
		start_utc = pytz.utc.localize(min(slots.mapped('start_datetime')))
		end_utc = pytz.utc.localize(max(slots.mapped('end_datetime')))
		resource_work_intervals, calendar_work_intervals = slots.resource_id.filtered('calendar_id') \
			._get_valid_work_intervals(start_utc, end_utc, calendars=slots.company_id.resource_calendar_id)
		for slot in slots:
			if not slot.resource_id and slot.allocation_type == 'planning' or not slot.resource_id.calendar_id:
				slot.allocated_percentage = 100 * slot.allocated_hours / slot._calculate_slot_duration()
			else:
				work_hours = slot._get_working_hours_over_period(start_utc, end_utc, resource_work_intervals, calendar_work_intervals)
				slot.allocated_percentage = 100 * slot.allocated_hours / work_hours if work_hours else 100

	@api.depends('start_datetime', 'end_datetime')
	def _compute_allocated_hours(self):
		for slot in self:
			# for each planning slot, compute the duration
			slot.allocated_hours = slot._calculate_slot_duration()
			# print("slot.allocated_hours",slot.allocated_hours)

	@api.depends('start_datetime', 'end_datetime', 'resource_id')
	def _compute_working_days_count(self):
		slots_per_calendar = defaultdict(set)
		planned_dates_per_calendar_id = defaultdict(lambda: (datetime.max, datetime.min))
		for slot in self:
			if not slot.employee_id:
				slot.working_days_count = 0
				continue
			calendar = slot.resource_id.calendar_id or slot.resource_id.company_id.resource_calendar_id
			slots_per_calendar[calendar].add(slot.id)
			datetime_begin, datetime_end = planned_dates_per_calendar_id[calendar.id]
			datetime_begin = min(datetime_begin, slot.start_datetime)
			datetime_end = max(datetime_end, slot.end_datetime)
			planned_dates_per_calendar_id[calendar.id] = datetime_begin, datetime_end
		for calendar, slot_ids in slots_per_calendar.items():
			slots = self.env['hr.assistance.planning.line'].browse(list(slot_ids))
			if not calendar:
				slots.working_days_count = 0
				continue
			datetime_begin, datetime_end = planned_dates_per_calendar_id[calendar.id]
			datetime_begin = timezone_datetime(datetime_begin)
			datetime_end = timezone_datetime(datetime_end)
			resources = slots.resource_id
			day_total = calendar._get_resources_day_total(datetime_begin, datetime_end, resources)
			intervals = calendar._work_intervals_batch(datetime_begin, datetime_end, resources)
			for slot in slots:
				slot.working_days_count = calendar._get_days_data(
					intervals[slot.resource_id.id] & Intervals([(
						timezone_datetime(slot.start_datetime),
						timezone_datetime(slot.end_datetime),
						self.env['resource.calendar.attendance']
					)]),
					day_total[slot.resource_id.id]
				)['days']

	@api.depends('start_datetime', 'end_datetime', 'resource_id')
	def _compute_overlap_slot_count(self):
		if self.ids:
			self.flush_model(['start_datetime', 'end_datetime', 'resource_id'])
			query = """
	                SELECT S1.id,ARRAY_AGG(DISTINCT S2.id) as conflict_ids FROM
	                    hr_assistance_planning_line S1, hr_assistance_planning_line S2
	                WHERE
	                    S1.start_datetime < S2.end_datetime
	                    AND S1.end_datetime > S2.start_datetime
	                    AND S1.id <> S2.id AND S1.resource_id = S2.resource_id
	                    AND S1.allocated_percentage + S2.allocated_percentage > 100
	                    and S1.id in %s
	                GROUP BY S1.id;
	            """
			self.env.cr.execute(query, (tuple(self.ids),))
			overlap_mapping = dict(self.env.cr.fetchall())
			for slot in self:
				slot_result = overlap_mapping.get(slot.id, [])
				slot.overlap_slot_count = len(slot_result)
				slot.conflicting_slot_ids = [(6, 0, slot_result)]
		else:
			# Allow fetching overlap without id if there is only one record
			# This is to allow displaying the warning when creating a new record without having an ID yet
			if len(self) == 1 and self.employee_id and self.start_datetime and self.end_datetime:
				query = """
	                    SELECT ARRAY_AGG(s.id) as conflict_ids
	                      FROM hr_assistance_planning_line s
	                     WHERE s.employee_id = %s
	                       AND s.start_datetime < %s
	                       AND s.end_datetime > %s
	                       AND s.allocated_percentage + %s > 100
	                """
				self.env.cr.execute(query, (self.employee_id.id, self.end_datetime,
											self.start_datetime, self.allocated_percentage))
				overlaps = self.env.cr.dictfetchall()
				if overlaps[0]['conflict_ids']:
					self.overlap_slot_count = len(overlaps[0]['conflict_ids'])
					self.conflicting_slot_ids = [(6, 0, overlaps[0]['conflict_ids'])]
				else:
					self.overlap_slot_count = False
			else:
				self.overlap_slot_count = False

	@api.model
	def _search_overlap_slot_count(self, operator, value):
		if operator not in ['=', '>'] or not isinstance(value, int) or value != 0:
			raise NotImplementedError(_('Operación no admitida, siempre debe comparar el valor de overlap_slot_count = 0, o con el operador >.'))

		query = """
	            SELECT S1.id
	            FROM hr_assistance_planning_line S1
	            WHERE EXISTS (
	                SELECT 1
	                  FROM hr_assistance_planning_line S2
	                 WHERE S1.id <> S2.id
	                   AND S1.resource_id = S2.resource_id
	                   AND S1.start_datetime < S2.end_datetime
	                   AND S1.end_datetime > S2.start_datetime
	                   AND S1.allocated_percentage + S2.allocated_percentage > 100
	            )
	        """
		operator_new = (operator == ">") and "inselect" or "not inselect"
		return [('id', operator_new, (query, ()))]

	@api.depends('start_datetime', 'end_datetime')
	def _compute_slot_duration(self):
		for slot in self:
			slot.duration = slot._get_slot_duration()

	def _get_slot_duration(self):
		"""Return the slot (effective) duration expressed in hours."""
		self.ensure_one()
		if not self.start_datetime:
			return False
		return (self.end_datetime - self.start_datetime).total_seconds() / 3600.0

	def _get_domain_template_slots(self):
		domain = []
		if self.resource_type == 'material':
			domain += [('role_id', '=', False)]
		elif self.role_id:
			domain += ['|', ('role_id', '=', self.role_id.id), ('role_id', '=', False)]
		# elif self.employee_id and self.employee_id.sudo().planning_role_ids:
		elif self.employee_id:
			# domain += ['|', ('role_id', 'in', self.employee_id.sudo().planning_role_ids.ids), ('role_id', '=', False)]
			domain += [('role_id', '=', False)]
		return domain

	@api.depends('role_id', 'employee_id')
	def _compute_template_autocomplete_ids(self):
		domain = self._get_domain_template_slots()
		templates = self.env['hr.shift.template'].search(domain, order='start_time', limit=10)
		self.template_autocomplete_ids = templates + self.template_id

	@api.depends('employee_id', 'role_id', 'start_datetime', 'end_datetime')
	def _compute_template_id(self):
		for slot in self.filtered(lambda s: s.template_id):
			slot.previous_template_id = slot.template_id
			slot.template_reset = False
			if slot._different_than_template():
				slot.template_id = False
				slot.previous_template_id = False
				slot.template_reset = True

	def _different_than_template(self, check_empty=True):
		self.ensure_one()
		if not self.start_datetime:
			return True
		template_fields = self._get_template_fields().items()
		for template_field, slot_field in template_fields:
			if self.template_id[template_field] or not check_empty:
				if template_field == 'start_time':
					h = int(self.template_id.start_time)
					m = round(modf(self.template_id.start_time)[0] * 60.0)
					slot_time = self[slot_field].astimezone(pytz.timezone(self._get_tz()))
					if slot_time.hour != h or slot_time.minute != m:
						return True
				else:
					if self[slot_field] != self.template_id[template_field]:
						return True
		return False

	@api.depends('recurrency_id')
	def _compute_repeat(self):
		for slot in self:
			if slot.recurrency_id:
				slot.repeat = True
			else:
				slot.repeat = False

	@api.depends('recurrency_id.repeat_interval')
	def _compute_repeat_interval(self):
		recurrency_slots = self.filtered('recurrency_id')
		for slot in recurrency_slots:
			if slot.recurrency_id:
				slot.repeat_interval = slot.recurrency_id.repeat_interval
		(self - recurrency_slots).update(self.default_get(['repeat_interval']))

	@api.depends('recurrency_id.repeat_until', 'repeat', 'repeat_type')
	def _compute_repeat_until(self):
		for slot in self:
			repeat_until = False
			if slot.repeat and slot.repeat_type == 'until':
				if slot.recurrency_id and slot.recurrency_id.repeat_until:
					repeat_until = slot.recurrency_id.repeat_until
				elif slot.start_datetime:
					repeat_until = slot.start_datetime + relativedelta(weeks=1)
			slot.repeat_until = repeat_until

	@api.depends('recurrency_id.repeat_number', 'repeat_type')
	def _compute_repeat_number(self):
		recurrency_slots = self.filtered('recurrency_id')
		for slot in recurrency_slots:
			slot.repeat_number = slot.recurrency_id.repeat_number
		(self - recurrency_slots).update(self.default_get(['repeat_number']))

	@api.depends('recurrency_id.repeat_unit')
	def _compute_repeat_unit(self):
		non_recurrent_slots = self.env['hr.assistance.planning.line']
		for slot in self:
			if slot.recurrency_id:
				slot.repeat_unit = slot.recurrency_id.repeat_unit
			else:
				non_recurrent_slots += slot
		non_recurrent_slots.update(self.default_get(['repeat_unit']))

	@api.depends('recurrency_id.repeat_type')
	def _compute_repeat_type(self):
		recurrency_slots = self.filtered('recurrency_id')
		for slot in recurrency_slots:
			if slot.recurrency_id:
				slot.repeat_type = slot.recurrency_id.repeat_type
		(self - recurrency_slots).update(self.default_get(['repeat_type']))

	def _inverse_repeat(self):
		for slot in self:
			if slot.repeat and not slot.recurrency_id.id:  # create the recurrence
				repeat_until = False
				repeat_number = 0
				if slot.repeat_type == "until":
					repeat_until = datetime.combine(fields.Date.to_date(slot.repeat_until), datetime.max.time())
					repeat_until = repeat_until.replace(tzinfo=pytz.timezone(slot.company_id.resource_calendar_id.tz or 'UTC')).astimezone(pytz.utc).replace(tzinfo=None)
				if slot.repeat_type == 'x_times':
					repeat_number = slot.repeat_number
				recurrency_values = {
					'repeat_interval': slot.repeat_interval,
					'repeat_unit': slot.repeat_unit,
					'repeat_until': repeat_until,
					'repeat_number': repeat_number,
					'repeat_type': slot.repeat_type,
					'company_id': slot.company_id.id,
				}
				recurrence = self.env['hr.assistance.planning.recurrency'].create(recurrency_values)
				slot.recurrency_id = recurrence
				slot.recurrency_id._repeat_slot()
			# user wants to delete the recurrence
			# here we also check that we don't delete by mistake a slot of which the repeat parameters have been changed
			elif not slot.repeat and slot.recurrency_id.id:
				slot.recurrency_id._delete_slot(slot.end_datetime)
				slot.recurrency_id.unlink()  # will set recurrency_id to NULL

	@api.model
	def _calculate_start_end_dates(self,
								   start_datetime,
								   end_datetime,
								   resource_id,
								   template_id,
								   previous_template_id,
								   template_reset):

		def convert_datetime_timezone(dt, tz):
			return dt and pytz.utc.localize(dt).astimezone(tz)

		resource = resource_id or self.env.user.employee_id.resource_id
		company = self.company_id or self.env.company
		employee = resource_id.employee_id if resource_id.resource_type == 'user' else False
		user_tz = pytz.timezone(self.env.user.tz
								or employee and employee.tz
								or resource_id.tz
								or self._context.get('tz')
								or self.env.user.company_id.resource_calendar_id.tz
								or 'UTC')

		if start_datetime and end_datetime and not template_id:
			# Transform the current column's start/end_datetime to the user's timezone from UTC
			current_start = convert_datetime_timezone(start_datetime, user_tz)
			current_end = convert_datetime_timezone(end_datetime, user_tz)
			# Look at the work intervals to examine whether the current start/end_datetimes are inside working hours
			calendar_id = resource.calendar_id or company.resource_calendar_id
			work_interval = calendar_id._work_intervals_batch(current_start, current_end)[False]
			intervals = [(date_start, date_stop) for date_start, date_stop, attendance in work_interval]
			if not intervals:
				# If we are outside working hours, we do not edit the start/end_datetime
				# Return the start/end times back at UTC and remove the tzinfo from the object
				return (current_start.astimezone(pytz.utc).replace(tzinfo=None),
						current_end.astimezone(pytz.utc).replace(tzinfo=None))

		# start_datetime and end_datetime are from 00:00 to 23:59 in user timezone
		# Converted in UTC, it gives an offset for any other timezone, _convert_datetime_timezone removes the offset
		start = convert_datetime_timezone(start_datetime, user_tz) if start_datetime else user_tz.localize(self._default_start_datetime())
		end = convert_datetime_timezone(end_datetime, user_tz) if end_datetime else user_tz.localize(self._default_end_datetime())

		if resource:
			work_interval_start, work_interval_end = \
			resource._adjust_to_calendar(start.replace(tzinfo=pytz.timezone(resource.tz)), end.replace(tzinfo=pytz.timezone(resource.tz)), compute_leaves=False)[resource]
			start, end = (work_interval_start or start, work_interval_end or end)

		if not previous_template_id and not template_reset:
			start = start.astimezone(pytz.utc).replace(tzinfo=None)
			end = end.astimezone(pytz.utc).replace(tzinfo=None)

		if template_id and start_datetime:
			h = int(template_id.start_time)
			m = round(modf(template_id.start_time)[0] * 60.0)
			start = pytz.utc.localize(start_datetime).astimezone(pytz.timezone(resource.tz) if resource else user_tz)
			start = start.replace(hour=int(h), minute=int(m))
			start = start.astimezone(pytz.utc).replace(tzinfo=None)

			h, m = divmod(template_id.duration, 1)
			delta = timedelta(hours=int(h), minutes=int(round(m * 60)))
			end = start + delta
		return (start, end)

	@api.depends('template_id')
	def _compute_datetime(self):
		for slot in self.filtered(lambda s: s.template_id):
			slot.start_datetime, slot.end_datetime = self._calculate_start_end_dates(slot.start_datetime,
																					 slot.end_datetime,
																					 slot.resource_id,
																					 slot.template_id,
																					 slot.previous_template_id,
																					 slot.template_reset)

	@api.depends(lambda self: self._get_fields_breaking_publication())
	def _compute_publication_warning(self):
		for slot in self:
			slot.publication_warning = slot.resource_id and slot.resource_type != 'material' and slot.state == 'published'

	def _company_working_hours(self, start, end):
		company = self.company_id or self.env.company
		work_interval = company.resource_calendar_id._work_intervals_batch(start, end)[False]
		intervals = [(date_start, date_stop) for date_start, date_stop, attendance in work_interval]
		start_datetime, end_datetime = (start, end)
		if intervals and (end_datetime - start_datetime).days == 0:  # Then we want the first working day and keep the end hours of this day
			start_datetime = intervals[0][0]
			end_datetime = [stop for start, stop in intervals if stop.date() == start_datetime.date()][-1]
		elif intervals and (end_datetime - start_datetime).days >= 0:
			start_datetime = intervals[0][0]
			end_datetime = intervals[-1][1]
		return (start_datetime, end_datetime)

	# ----------------------------------------------------
	# ORM overrides
	# ----------------------------------------------------
	@api.model
	def _read_group_fields_nullify(self):
		return ['working_days_count']

	@api.model
	def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
		res = super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
		if lazy:
			return res
		null_fields = [f for f in self._read_group_fields_nullify() if any(f2.startswith(f) for f2 in fields)]
		if null_fields:
			for r in res:
				for f in null_fields:
					if r[f] == 0:
						r[f] = False
		return res

	@api.model
	def default_get(self, fields_list):
		res = super(HrAssistancePlanningLine, self).default_get(fields_list)

		if res.get('resource_id'):
			resource_id = self.env['resource.resource'].browse(res.get('resource_id'))
			template_id, previous_template_id = [res.get(key) for key in ['template_id', 'previous_template_id']]
			template_id = template_id and self.env['hr.shift.template'].browse(template_id)
			previous_template_id = template_id and self.env['hr.shift.template'].browse(previous_template_id)
			res['start_datetime'], res['end_datetime'] = self._calculate_start_end_dates(res.get('start_datetime'),
																						 res.get('end_datetime'),
																						 resource_id,
																						 template_id,
																						 previous_template_id,
																						 res.get('template_reset'))
		else:
			if 'start_datetime' in fields_list:
				start_datetime = fields.Datetime.from_string(res.get('start_datetime')) if res.get('start_datetime') else self._default_start_datetime()
				end_datetime = fields.Datetime.from_string(res.get('end_datetime')) if res.get('end_datetime') else self._default_end_datetime()
				start = pytz.utc.localize(start_datetime)
				end = pytz.utc.localize(end_datetime) if end_datetime else self._default_end_datetime()
				opening_hours = self._company_working_hours(start, end)
				res['start_datetime'] = opening_hours[0].astimezone(pytz.utc).replace(tzinfo=None)

				if 'end_datetime' in fields_list:
					res['end_datetime'] = opening_hours[1].astimezone(pytz.utc).replace(tzinfo=None)
		return res

	@api.depends(lambda self: self._display_name_fields())
	@api.depends_context('group_by')
	def _compute_display_name(self):
		group_by = self.env.context.get('group_by', [])
		field_list = [fname for fname in self._display_name_fields() if fname not in group_by]

		# Sudo as a planning manager is not able to read private project if he is not project manager.
		self = self.sudo()
		for slot in self.with_context(hide_partner_ref=True):
			# label part, depending on context `groupby`
			name_values = [
							  self._fields[fname].convert_to_display_name(slot[fname], slot) if fname != 'resource_id' else slot.resource_id.name
							  for fname in field_list
							  if slot[fname]
						  ][:4]  # limit to 4 labels
			name = ' - '.join(name_values) or slot.resource_id.name

			# add unicode bubble to tell there is a note
			if slot.name:
				name = f'{name} \U0001F4AC'

			slot.display_name = name + ' ' + str(slot.fecha) or ''

	@api.model_create_multi
	def create(self, vals_list):
		Resource = self.env['resource.resource']
		for vals in vals_list:
			if vals.get('resource_id'):
				resource = Resource.browse(vals.get('resource_id'))
				if not vals.get('company_id'):
					vals['company_id'] = resource.company_id.id
				if resource.resource_type == 'material':
					vals['state'] = 'published'
			if not vals.get('company_id'):
				vals['company_id'] = self.env.company.id
		return super().create(vals_list)

	def write(self, values):
		new_resource = self.env['resource.resource'].browse(values['resource_id']) if 'resource_id' in values else None
		if new_resource and new_resource.resource_type == 'material':
			values['state'] = 'published'
		# if the resource_id is changed while the shift has already been published and the resource is human, that means that the shift has been re-assigned
		# and thus we should send the email about the shift re-assignment
		if (new_resource and self.state == 'published'
				and self.resource_type == 'user'
				and new_resource.resource_type == 'user'):
			self._send_shift_assigned(self, new_resource)

		recurrence_update = values.pop('recurrence_update', 'this')
		if recurrence_update != 'this':
			recurrence_domain = []
			if recurrence_update == 'subsequent':
				for slot in self:
					recurrence_domain = expression.OR([recurrence_domain,
													   ['&', ('recurrency_id', '=', slot.recurrency_id.id),
														('start_datetime', '>=', slot.start_datetime)]
													   ])
					recurrence_slots = self.search(recurrence_domain)
					if any(field_name in values	for field_name in ('start_datetime', 'end_datetime')):
						recurrence_slots -= slot
						values["repeat_type"] = slot.repeat_type
						self -= recurrence_slots
						recurrence_slots.unlink()
					else:
						self |= recurrence_slots
			else:
				recurrence_slots = self.search([('recurrency_id', 'in', self.recurrency_id.ids)])
				if any(field_name in values	for field_name in ('start_datetime', 'end_datetime')):
					slot = recurrence_slots[-1]
					values["repeat_type"] = slot.repeat_type  # this is to ensure that the subsequent slots are recreated
					recurrence_slots -= slot
					recurrence_slots.unlink()
					self -= recurrence_slots
					self |= slot
				else:
					self |= recurrence_slots

		result = super().write(values)
		# recurrence
		if any(key in ('repeat', 'repeat_unit', 'repeat_type', 'repeat_until', 'repeat_interval', 'repeat_number') for key in values):
			# User is trying to change this record's recurrence so we delete future slots belonging to recurrence A
			# and we create recurrence B from now on w/ the new parameters
			for slot in self:
				recurrence = slot.recurrency_id
				if recurrence and values.get('repeat') is None:
					repeat_type = values.get('repeat_type') or recurrence.repeat_type
					repeat_until = values.get('repeat_until') or recurrence.repeat_until
					repeat_number = values.get('repeat_number', 0) or slot.repeat_number
					if repeat_type == 'until':
						repeat_until = datetime.combine(fields.Date.to_date(repeat_until), datetime.max.time())
						repeat_until = repeat_until.replace(tzinfo=pytz.timezone(slot.company_id.resource_calendar_id.tz or 'UTC')).astimezone(pytz.utc).replace(tzinfo=None)
					recurrency_values = {
						'repeat_interval': values.get('repeat_interval') or recurrence.repeat_interval,
						'repeat_unit': values.get('repeat_unit') or recurrence.repeat_unit,
						'repeat_until': repeat_until if repeat_type == 'until' else False,
						'repeat_number': repeat_number,
						'repeat_type': repeat_type,
						'company_id': slot.company_id.id,
					}
					recurrence.write(recurrency_values)
					if slot.repeat_type == 'x_times':
						recurrency_values['repeat_until'] = recurrence._get_recurrence_last_datetime()
					end_datetime = slot.end_datetime if values.get('repeat_unit') else recurrency_values.get('repeat_until')
					recurrence._delete_slot(end_datetime)
					recurrence._repeat_slot()
		return result

	@api.returns(None, lambda value: value[0])
	def copy_data(self, default=None):
		if default is None:
			default = {}
		if self._context.get('planning_split_tool'):
			default['state'] = self.state
		return super().copy_data(default=default)

	@api.returns('self', lambda value: value.id)
	def copy(self, default=None):
		result = super().copy(default=default)
		# force recompute of stored computed fields depending on start_datetime
		if default and "start_datetime" in default:
			result._compute_allocated_hours()
			result._compute_working_days_count()
		return result

	# ----------------------------------------------------
	# Actions
	# ----------------------------------------------------
	def action_address_recurrency(self, recurrence_update):
		""" :param recurrence_update: the occurences to be targetted (this, subsequent, all)"""
		if recurrence_update == 'this':
			return
		domain = [('id', 'not in', self.ids)]
		if recurrence_update == 'all':
			domain = expression.AND([domain, [('recurrency_id', 'in', self.recurrency_id.ids)]])
		elif recurrence_update == 'subsequent':
			start_date_per_recurrency_id = {}
			sub_domain = []
			for shift in self:
				if shift.recurrency_id.id not in start_date_per_recurrency_id \
						or shift.start_datetime < start_date_per_recurrency_id[shift.recurrency_id.id]:
					start_date_per_recurrency_id[shift.recurrency_id.id] = shift.start_datetime
			for recurrency_id, start_datetime in start_date_per_recurrency_id.items():
				sub_domain = expression.OR([sub_domain,
											['&', ('recurrency_id', '=', recurrency_id),
											 ('start_datetime', '>', start_datetime)]
											])
			domain = expression.AND([domain, sub_domain])
		sibling_slots = self.env['hr.assistance.planning.line'].search(domain)
		self.recurrency_id.unlink()
		sibling_slots.unlink()

	def action_unlink(self):
		self.unlink()
		return {'type': 'ir.actions.act_window_close'}

	def action_see_overlaping_slots(self):
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'hr.assistance.planning.line',
			'name': _('Turnos con Conflictos'),
			'view_mode': 'gantt,list,form',
			'context': {
				'initialDate': min(self.mapped('start_datetime')),
				'search_default_conflict_shifts': True,
				'search_default_resource_id': self.resource_id.ids
			}
		}

	# ----------------------------------------------------
	# Gantt - Calendar view
	# ----------------------------------------------------
	@api.model
	def gantt_resource_work_interval(self, slot_ids):
		""" Returns the work intervals of the resources corresponding to the provided slots
            This method is used in a rpc call
        :param slot_ids: The slots the work intervals have to be returned for.
        :return: list of dicts { resource_id: [Intervals] } and { resource_id: flexible_hours }."""
		# Get the oldest start date and latest end date from the slots.
		domain = [("id", "in", slot_ids)]
		read_group_fields = ["start_datetime:min", "end_datetime:max", "resource_id:recordset", "__count"]
		planning_slot_read_group = self.env["hr.assistance.planning.line"]._read_group(domain, [], read_group_fields)
		start_datetime, end_datetime, resources, count = planning_slot_read_group[0]
		if not count:
			return [{}]

		# Get default start/end datetime if any.
		default_start_datetime = (fields.Datetime.to_datetime(self._context.get('default_start_datetime')) or datetime.min).replace(tzinfo=pytz.utc)
		default_end_datetime = (fields.Datetime.to_datetime(self._context.get('default_end_datetime')) or datetime.max).replace(tzinfo=pytz.utc)

		start_datetime = max(default_start_datetime, start_datetime.replace(tzinfo=pytz.utc))
		end_datetime = min(default_end_datetime, end_datetime.replace(tzinfo=pytz.utc))

		# Get slots' resources and current company work intervals.
		work_intervals_per_resource, dummy = resources._get_valid_work_intervals(start_datetime, end_datetime)
		company_calendar = self.env.company.resource_calendar_id
		company_calendar_work_intervals = company_calendar._work_intervals_batch(start_datetime, end_datetime)

		# Export work intervals in UTC
		work_intervals_per_resource[False] = company_calendar_work_intervals[False]
		work_interval_per_resource = defaultdict(list)
		for resource_id, resource_work_intervals in work_intervals_per_resource.items():
			for resource_work_interval in resource_work_intervals:
				work_interval_per_resource[resource_id].append((resource_work_interval[0].astimezone(pytz.UTC), resource_work_interval[1].astimezone(pytz.UTC)))
		# Add the flexible status per resource to the output
		flexible_per_resource = {resource.id: not bool(resource.calendar_id) for resource in set(resources)}
		flexible_per_resource[False] = True
		return [work_interval_per_resource, flexible_per_resource]

	@api.model
	def get_unusual_days(self, date_from, date_to=None):
		return self.env.user.employee_id._get_unusual_days(date_from, date_to)

	# ----------------------------------------------------
	# Period Duplication
	# ----------------------------------------------------
	@api.model
	def action_copy_previous_week(self, date_start_week, view_domain):
		date_end_copy = datetime.strptime(date_start_week, DEFAULT_SERVER_DATETIME_FORMAT)
		date_start_copy = date_end_copy - relativedelta(days=7)
		# print("date_end_copy",date_end_copy)
		# print("date_start_copy",date_start_copy)
		domain = [
			# ('recurrency_id', '=', False),
			('employee_id', '!=', False),
			('was_copied', '=', False)
		]
		for dom in view_domain:
			if dom in ['|', '&', '!']:
				domain.append(dom)
			elif dom[0] == 'start_datetime':
				domain.append(('start_datetime', '>=', date_start_copy))
			elif dom[0] == 'end_datetime':
				domain.append(('end_datetime', '<=', date_end_copy))
			else:
				domain.append(tuple(dom))
		# print("domain",domain)
		slots_to_copy = self.search(domain)
		# print("slots_to_copy",slots_to_copy)
		new_slot_values = []
		new_slot_values = slots_to_copy._copy_slots(date_start_copy, date_end_copy, relativedelta(days=7))
		# print("new_slot_values",new_slot_values)
		slots_to_copy.write({'was_copied': True})
		if new_slot_values:
			return [self.create(new_slot_values).ids, slots_to_copy.ids]
		return False

	def action_rollback_copy_previous_week(self, copied_slot_ids):
		self.browse(copied_slot_ids).was_copied = False
		self.unlink()

	# ----------------------------------------------------
	# Sending Shifts
	# ----------------------------------------------------

	def _get_notification_action(self, notif_type, message):
		return {
			'type': 'ir.actions.client',
			'tag': 'display_notification',
			'params': {
				'type': notif_type,
				'message': message,
				'next': {'type': 'ir.actions.act_window_close'},
			}
		}

	def action_send(self):
		for rec in self:
			rec.ensure_one()
			if rec.employee_id:
				rec.state = 'published'
		# employee_ids = self._get_employees_to_send_slot()
		# self._send_slot(employee_ids, self.start_datetime, self.end_datetime)
		message = _("El turno ha sido publicado exitosamente.")
		return self._get_notification_action('success', message)

	def action_unpublish(self):
		if not self.env.user.has_group('hr_attendance.group_hr_attendance_manager'):
			raise AccessError(_('No se le permite restablecer los turnos de borrador.'))
		published_shifts = self.filtered(lambda shift: shift.state == 'published' and shift.resource_type != 'material')
		if published_shifts:
			published_shifts.write({'state': 'draft', 'publication_warning': False, })
			notif_type = "success"
			message = _('Los turnos se han restablecido exitosamente al borrador.')
		else:
			notif_type = "warning"
			message = _('No hay turnos para restablecer al draft.')
		return self._get_notification_action(notif_type, message)

	# ----------------------------------------------------
	# Business Methods
	# ----------------------------------------------------
	def _calculate_slot_duration(self):
		self.ensure_one()
		if not self.start_datetime or not self.end_datetime:
			return 0.0
		period = self.end_datetime - self.start_datetime
		# print("period",period)
		slot_duration = period.total_seconds() / 3600
		# print("slot_duration",slot_duration)
		# max_duration = (period.days + (1 if period.seconds else 0)) * self.company_id.resource_calendar_id.hours_per_day
		# if not max_duration or max_duration >= slot_duration:
		return slot_duration
		# return max_duration

	# ----------------------------------------------------
	# Copy Slots
	# ----------------------------------------------------
	def _add_delta_with_dst(self, start, delta):
		""" Add to start, adjusting the hours if needed to account for a shift in the local timezone between the
        start date and the resulting date (typically, because of DST)
        :param start: origin date in UTC timezone, but without timezone info (a naive date)
        :return resulting date in the UTC timezone (a naive date)"""
		try:
			tz = pytz.timezone(self._get_tz())
		except pytz.UnknownTimeZoneError:
			tz = pytz.UTC
		start = start.replace(tzinfo=pytz.utc).astimezone(tz).replace(tzinfo=None)
		result = start + delta
		return tz.localize(result).astimezone(pytz.utc).replace(tzinfo=None)

	def _get_half_day_interval(self, values):
		""" This method computes the afternoon and/or the morning whole interval where the planning slot exists.
            The resulting interval frames the slot in a bigger interval beginning before the slot (max 11:59:59 sooner)
            and finishing later (max 11:59:59 later)
            :param values: a dict filled in with new hr.assistance.planning.line vals
            :return an interval"""
		return Intervals([(
			self._get_half_day_datetime(values['start_datetime']),
			self._get_half_day_datetime(values['end_datetime'], end=True),
			self.env['resource.calendar.attendance']
		)])

	def _get_half_day_datetime(self, dt, end=False):
		""" This method computes a datetime in order to frame the slot in a bigger interval begining at midnight or
            noon and ending at midnight or noon.
            This method returns :
            - If end is False : Greatest datetime between midnight and noon that is sooner than the `dt` datetime;
            - Otherwise : Lowest datetime between midnight and noon that is later than the `dt` datetime.
            :param dt: input datetime
            :param end: wheter the dt is the end, resp. the start, of the interval if set, resp. not set.
            :return a datetime"""
		self.ensure_one()
		tz = pytz.timezone(self._get_tz())
		localized_dt = pytz.utc.localize(dt).astimezone(tz)
		midday = localized_dt.replace(hour=12, minute=0, second=0)
		if end:
			return midday if midday > localized_dt else (
						localized_dt.replace(hour=0, minute=0, second=0) + timedelta(days=1))
		return midday if midday < localized_dt else localized_dt.replace(hour=0, minute=0, second=0)

	def _init_remaining_hours_to_plan(self, remaining_hours_to_plan):
		""" Inits the remaining_hours_to_plan dict for a given slot and returns wether
            there are enough remaining hours.
            :return a bool representing wether or not there are still hours remaining"""
		self.ensure_one()
		return True

	def _update_remaining_hours_to_plan_and_values(self, remaining_hours_to_plan, values):
		""" Update the remaining_hours_to_plan with the allocated hours of the slot in `values`
            and returns wether there are enough remaining hours.

            If remaining_hours is strictly positive, and the allocated hours of the slot in `values` is
            higher than remaining hours, than update the values in order to consume at most the
            number of remaining_hours still available.
            :return a bool representing wether or not there are still hours remaining"""
		self.ensure_one()
		return True

	def _get_split_slot_values(self, values, intervals, remaining_hours_to_plan, unassign=False):
		""" Generates and returns slots values within the given intervals

            The slot in values, which represents a forecast planning slot, is split in multiple parts
            filling the (available) intervals.
            :return a vals list of the slot to create"""
		self.ensure_one()
		splitted_slot_values = []
		for start_inter, end_inter, _resource in intervals:
			new_slot_vals = {
				**values,
				'start_datetime': start_inter.astimezone(pytz.utc).replace(tzinfo=None),
				'end_datetime': end_inter.astimezone(pytz.utc).replace(tzinfo=None),
			}
			was_updated = self._update_remaining_hours_to_plan_and_values(remaining_hours_to_plan, new_slot_vals)
			new_slot_vals['allocated_hours'] = float_utils.float_round(
				((end_inter - start_inter).total_seconds() / 3600.0) * (self.allocated_percentage / 100.0),	precision_digits=2)
			if not was_updated:
				return splitted_slot_values
			if unassign:
				new_slot_vals['resource_id'] = False
			splitted_slot_values.append(new_slot_vals)
		return splitted_slot_values

	def _copy_slots(self, start_dt, end_dt, delta):
		""" Copy slots planned between `start_dt` and `end_dt`, after a `delta`
            Takes into account the resource calendar and the slots already planned.
            All the slots will be copied, whatever the value of was_copied is.
            :return a vals list of the slot to create """
		resource_per_calendar = defaultdict(lambda: self.env['resource.resource'])
		resource_calendar_validity_intervals = defaultdict(dict)
		attendance_intervals_per_resource = defaultdict(Intervals)  # key: resource, values: attendance intervals
		unavailable_intervals_per_resource = defaultdict(Intervals)  # key: resource, values: unavailable intervals
		attendance_intervals_per_calendar = defaultdict(Intervals)  # key: calendar, values: attendance intervals (used for company calendars)
		leave_intervals_per_calendar = defaultdict(Intervals)  # key: calendar, values: leave intervals (used for company calendars)
		new_slot_values = []
		# date utils variable
		start_dt_delta = start_dt + delta
		end_dt_delta = end_dt + delta
		start_dt_delta_utc = pytz.utc.localize(start_dt_delta)
		end_dt_delta_utc = pytz.utc.localize(end_dt_delta)
		# 1)
		# Search for all resource slots already planned
		resource_slots = self.search([
			('start_datetime', '>=', start_dt_delta),
			('end_datetime', '<=', end_dt_delta),
			('resource_id', 'in', self.resource_id.ids)
		])
		# And convert it into intervals
		for slot in resource_slots:
			unavailable_intervals_per_resource[slot.resource_id] |= Intervals([(
				pytz.utc.localize(slot.start_datetime),
				pytz.utc.localize(slot.end_datetime),
				self.env['resource.calendar.leaves'])])
		# 2)
		resource_calendar_validity_intervals = self.resource_id.sudo()._get_calendars_validity_within_period(start_dt_delta_utc, end_dt_delta_utc)
		for slot in self:
			if slot.resource_id:
				for calendar in resource_calendar_validity_intervals[slot.resource_id.id]:
					resource_per_calendar[calendar] |= slot.resource_id
			company_calendar_id = slot.company_id.resource_calendar_id
			resource_per_calendar[company_calendar_id] |= self.env['resource.resource']  # ensures the company_calendar will be in resource_per_calendar keys.
		# 3)
		for calendar, resources in resource_per_calendar.items():
			# For each calendar, retrieves the work intervals of every resource
			attendances = calendar._attendance_intervals_batch(
				start_dt_delta_utc,
				end_dt_delta_utc,
				resources=resources
			)
			leaves = calendar._leave_intervals_batch(
				start_dt_delta_utc,
				end_dt_delta_utc,
				resources=resources
			)
			attendance_intervals_per_calendar[calendar] = attendances[False]
			leave_intervals_per_calendar[calendar] = leaves[False]
			for resource in resources:
				# for each resource, adds his/her attendances and unavailabilities for this calendar, during the calendar validity interval.
				attendance_intervals_per_resource[resource] |= (
							attendances[resource.id] & resource_calendar_validity_intervals[resource.id][calendar])
				unavailable_intervals_per_resource[resource] |= (
							leaves[resource.id] & resource_calendar_validity_intervals[resource.id][calendar])
		# 4)
		remaining_hours_to_plan = {}
		for slot in self:
			if not slot._init_remaining_hours_to_plan(remaining_hours_to_plan):
				continue
			values = slot.copy_data(default={'state': 'draft'})[0]
			if not values.get('start_datetime') or not values.get('end_datetime'):
				continue
			values['start_datetime'] = slot._add_delta_with_dst(values['start_datetime'], delta)
			values['end_datetime'] = slot._add_delta_with_dst(values['end_datetime'], delta)
			if any(
					new_slot['resource_id'] == values['resource_id'] and
					new_slot['start_datetime'] <= values['end_datetime'] and
					new_slot['end_datetime'] >= values['start_datetime']
					for new_slot in new_slot_values
			):
				values['resource_id'] = False
			interval = Intervals([(
				pytz.utc.localize(values.get('start_datetime')),
				pytz.utc.localize(values.get('end_datetime')),
				self.env['resource.calendar.attendance']
			)])
			company_calendar = slot.company_id.resource_calendar_id
			# Check if interval is contained in the resource work interval
			attendance_resource = attendance_intervals_per_resource[slot.resource_id] if slot.resource_id else attendance_intervals_per_calendar[company_calendar]
			attendance_interval_resource = interval & attendance_resource
			# Check if interval is contained in the company attendances interval
			attendance_interval_company = interval & attendance_intervals_per_calendar[company_calendar]
			# Check if interval is contained in the company leaves interval
			unavailable_interval_company = interval & leave_intervals_per_calendar[company_calendar]
			if slot.allocation_type == 'planning' and not unavailable_interval_company and not attendance_interval_resource:
				# If the slot is not a forecast and there are no expected attendance, neither a company leave
				# check if the slot is planned during an afternoon or a morning during which the resource/company works/is opened

				# /!\ Name of such attendance is an "Extended Attendance", see hereafter
				interval = slot._get_half_day_interval(values)  # Get the afternoon and/or the morning whole interval where the planning slot exists.
				attendance_interval_resource = interval & attendance_resource
				attendance_interval_company = interval & attendance_intervals_per_calendar[company_calendar]
				unavailable_interval_company = interval & leave_intervals_per_calendar[company_calendar]
			unavailable_interval_resource = unavailable_interval_company if not slot.resource_id else (
						interval & unavailable_intervals_per_resource[slot.resource_id])
			if (attendance_interval_resource - unavailable_interval_company) or (
					attendance_interval_company - unavailable_interval_company):
				# Either the employee has, at least, some attendance that are not during the company unavailability
				# Either the company has, at least, some attendance that are not during the company unavailability

				if slot.allocation_type == 'planning':
					# /!\ It can be an "Extended Attendance" (see hereabove), and the slot may be unassigned.
					if unavailable_interval_resource or not attendance_interval_resource:
						# if the slot is during an resourece unavailability, or the employee is not attending during the slot
						if slot.resource_type != 'user':
							# if the resource is not an employee and the resource is not available, do not copy it nor unassign it
							continue
						values['resource_id'] = False
					if not slot._update_remaining_hours_to_plan_and_values(remaining_hours_to_plan, values):
						# make sure the hours remaining are enough
						continue
					new_slot_values.append(values)
				else:
					if attendance_interval_resource:
						# if the resource has attendances, at least during a while of the future slot lifetime,
						# 1) Work interval represents the availabilities of the employee
						# 2) The unassigned intervals represents the slots where the employee should be unassigned
						#    (when the company is not unavailable and the employee is unavailable)
						work_interval_employee = (attendance_interval_resource - unavailable_interval_resource)
						unassigned_interval = unavailable_interval_resource - unavailable_interval_company
						split_slot_values = slot._get_split_slot_values(values, work_interval_employee,	remaining_hours_to_plan)
						if slot.resource_type == 'user':
							split_slot_values += slot._get_split_slot_values(values, unassigned_interval, remaining_hours_to_plan, unassign=True)
					elif slot.resource_type != 'user':
						# If the resource type is not user and the slot can not be assigned to the resource, do not copy not unassign it
						continue
					else:
						# When the employee has no attendance at all, we are in the case where the employee has a calendar different than the
						# company (or no more calendar), so the slot will be unassigned
						unassigned_interval = attendance_interval_company - unavailable_interval_company
						split_slot_values = slot._get_split_slot_values(values, unassigned_interval, remaining_hours_to_plan, unassign=True)
					# merge forecast slots in order to have visually bigger slots
					new_slot_values += self._merge_slots_values(split_slot_values, unassigned_interval)
		return new_slot_values

	def _display_name_fields(self):
		""" List of fields that can be displayed in the display_name """
		return ['resource_id', 'role_id']

	def _get_fields_breaking_publication(self):
		""" Fields list triggering the `publication_warning` to True when updating shifts """
		return [
			'resource_id',
			'resource_type',
			'start_datetime',
			'end_datetime',
			'role_id',
		]

	@api.model
	def _get_template_fields(self):
		# key -> field from template
		# value -> field from slot
		return {'role_id': 'role_id', 'start_time': 'start_datetime', 'duration': 'duration'}

	def _get_tz(self):
		return (self.env.user.tz
				or self.employee_id.tz
				or self.resource_id.tz
				or self._context.get('tz')
				or self.company_id.resource_calendar_id.tz
				or 'UTC')

	def _manage_archived_resources(self, departure_date):
		shift_vals_list = []
		shift_ids_to_remove_resource = []
		for slot in self:
			split_time = pytz.timezone(self._get_tz()).localize(departure_date).astimezone(pytz.utc).replace(tzinfo=None)
			if (slot.start_datetime < split_time) and (slot.end_datetime > split_time):
				shift_vals_list.append({
					'start_datetime': split_time,
					**slot._prepare_shift_vals(),
				})
				if split_time > slot.start_datetime:
					slot.write({'end_datetime': split_time})
			elif slot.start_datetime >= split_time:
				shift_ids_to_remove_resource.append(slot.id)
		if shift_vals_list:
			self.sudo().create(shift_vals_list)
		if shift_ids_to_remove_resource:
			self.sudo().browse(shift_ids_to_remove_resource).write({'resource_id': False})

	def _group_expand_resource_id(self, resources, domain, order):
		dom_tuples = [(dom[0], dom[1]) for dom in domain if isinstance(dom, (tuple, list)) and len(dom) == 3]
		resource_ids = self.env.context.get('filter_resource_ids', False)
		if resource_ids:
			return self.env['resource.resource'].search([('id', 'in', resource_ids)], order=order)
		if self.env.context.get('planning_expand_resource') and ('start_datetime', '<=') in dom_tuples and ('end_datetime', '>=') in dom_tuples:
			if ('resource_id', '=') in dom_tuples or ('resource_id', 'ilike') in dom_tuples or ('resource_id', 'in') in dom_tuples:
				filter_domain = self._expand_domain_m2o_groupby(domain, 'resource_id')
				return self.env['resource.resource'].search(filter_domain, order=order)
			filters = self._expand_domain_dates(domain)
			resources = self.env['hr.assistance.planning.line'].search(filters).mapped('resource_id')
			return resources.search([('id', 'in', resources.ids)], order=order)
		return resources

	def _read_group_role_id(self, roles, domain, order):
		dom_tuples = [(dom[0], dom[1]) for dom in domain if isinstance(dom, list) and len(dom) == 3]
		if self._context.get('planning_expand_role') and ('start_datetime', '<=') in dom_tuples and ('end_datetime', '>=') in dom_tuples:
			if ('role_id', '=') in dom_tuples or ('role_id', 'ilike') in dom_tuples:
				filter_domain = self._expand_domain_m2o_groupby(domain, 'role_id')
				return self.env['attendance.activity'].search(filter_domain, order=order)
			filters = expression.AND([[('role_id.active', '=', True)], self._expand_domain_dates(domain)])
			return self.env['hr.assistance.planning.line'].search(filters).mapped('role_id')
		return roles

	@api.model
	def _expand_domain_m2o_groupby(self, domain, filter_field=False):
		filter_domain = []
		for dom in domain:
			if dom[0] == filter_field:
				field = self._fields[dom[0]]
				if field.type == 'many2one' and len(dom) == 3:
					if dom[1] in ['=', 'in']:
						filter_domain = expression.OR([filter_domain, [('id', dom[1], dom[2])]])
					elif dom[1] == 'ilike':
						rec_name = self.env[field.comodel_name]._rec_name
						filter_domain = expression.OR([filter_domain, [(rec_name, dom[1], dom[2])]])
		return filter_domain

	def _expand_domain_dates(self, domain):
		filters = []
		for dom in domain:
			if len(dom) == 3 and dom[0] == 'start_datetime' and dom[1] == '<=':
				max_date = dom[2] if dom[2] else datetime.now()
				max_date = max_date if isinstance(max_date, date) else datetime.strptime(max_date, '%Y-%m-%d %H:%M:%S')
				max_date = max_date + timedelta(days=7)
				filters.append((dom[0], dom[1], max_date))
			elif len(dom) == 3 and dom[0] == 'end_datetime' and dom[1] == '>=':
				min_date = dom[2] if dom[2] else datetime.now()
				min_date = min_date if isinstance(min_date, date) else datetime.strptime(min_date, '%Y-%m-%d %H:%M:%S')
				min_date = min_date - timedelta(days=7)
				filters.append((dom[0], dom[1], min_date))
			else:
				filters.append(dom)
		return filters

	@api.model
	def _format_datetime_to_user_tz(self, datetime_without_tz, record_env, tz=None, lang_code=False):
		return format_datetime(record_env, datetime_without_tz, tz=tz, dt_format='short', lang_code=lang_code)

	def _send_shift_assigned(self, slot, human_resource):
		email_from = slot.company_id.email or ''
		assignee = slot.resource_id.employee_id

		template = self.env.ref('planning.email_template_shift_switch_email', raise_if_not_found=False)
		start_datetime = self._format_datetime_to_user_tz(slot.start_datetime, assignee.env, tz=assignee.tz, lang_code=assignee.user_partner_id.lang)
		end_datetime = self._format_datetime_to_user_tz(slot.end_datetime, assignee.env, tz=assignee.tz, lang_code=assignee.user_partner_id.lang)
		template_context = {
			'old_assignee_name': assignee.name,
			'new_assignee_name': human_resource.employee_id.name,
			'start_datetime': start_datetime,
			'end_datetime': end_datetime,
		}
		if template and assignee != human_resource.employee_id:
			template.with_context(**template_context).send_mail(
				slot.id,
				email_values={
					'email_to': assignee.work_email,
					'email_from': email_from,
				},
				email_layout_xmlid='mail.mail_notification_light',
			)

	# ---------------------------------------------------
	# Slots generation/copy
	# ---------------------------------------------------
	@api.model
	def _merge_slots_values(self, slots_to_merge, unforecastable_intervals):
		if not slots_to_merge:
			return slots_to_merge
		# resulting vals_list of the merged slots
		new_slots_vals_list = []
		# accumulator for mergeable slots
		sum_allocated_hours = 0
		to_merge = []
		# invariants for mergeable slots
		common_allocated_percentage = slots_to_merge[0]['allocated_percentage']
		resource_id = slots_to_merge[0].get('resource_id')
		start_datetime = slots_to_merge[0]['start_datetime']
		previous_end_datetime = start_datetime
		for slot in slots_to_merge:
			mergeable = True
			if (not slot['start_datetime']
					or common_allocated_percentage != slot['allocated_percentage']
					or resource_id != slot['resource_id']
					or (slot['start_datetime'] - previous_end_datetime).total_seconds() > 3600 * 24):
				# last condition means the elapsed time between the previous end time and the
				# start datetime of the current slot should not be bigger than 24hours
				# if it's the case, then the slot can not be merged.
				mergeable = False
			if mergeable:
				end_datetime = slot['end_datetime']
				interval = Intervals([(
					pytz.utc.localize(start_datetime),
					pytz.utc.localize(end_datetime),
					self.env['resource.calendar.attendance']
				)])
				if not (interval & unforecastable_intervals):
					sum_allocated_hours += slot['allocated_hours']
					if (end_datetime - start_datetime).total_seconds() < 3600 * 24:
						# If the elapsed time between the first start_datetime and the
						# current end_datetime is not higher than 24hours,
						# slots cannot be merged as it won't be a forecast
						to_merge.append(slot)
					else:
						to_merge = [{
							**slot,
							'start_datetime': start_datetime,
							'allocated_hours': sum_allocated_hours,
						}]
				else:
					mergeable = False
			if not mergeable:
				new_slots_vals_list += to_merge
				to_merge = [slot]
				start_datetime = slot['start_datetime']
				common_allocated_percentage = slot['allocated_percentage']
				resource_id = slot.get('resource_id')
				sum_allocated_hours = slot['allocated_hours']
			previous_end_datetime = slot['end_datetime']
		new_slots_vals_list += to_merge
		return new_slots_vals_list

	def _get_working_hours_over_period(self, start_utc, end_utc, work_intervals, calendar_intervals):
		start = max(start_utc, pytz.utc.localize(self.start_datetime))
		end = min(end_utc, pytz.utc.localize(self.end_datetime))
		slot_interval = Intervals([(start, end, self.env['resource.calendar.attendance'])])
		working_intervals = work_intervals[self.resource_id.id] if self.resource_id else calendar_intervals[self.company_id.resource_calendar_id.id]
		return sum_intervals(slot_interval & working_intervals)

	def _get_duration_over_period(self, start_utc, stop_utc, work_intervals, calendar_intervals, has_allocated_hours=True):
		assert start_utc.tzinfo and stop_utc.tzinfo
		self.ensure_one()
		start, stop = start_utc.replace(tzinfo=None), stop_utc.replace(tzinfo=None)
		if has_allocated_hours and self.start_datetime >= start and self.end_datetime <= stop:
			return self.allocated_hours
		# if the slot goes over the gantt period, compute the duration only within
		# the gantt period
		ratio = self.allocated_percentage / 100.0
		working_hours = self._get_working_hours_over_period(start_utc, stop_utc, work_intervals, calendar_intervals)
		return working_hours * ratio

	def _gantt_progress_bar_resource_id(self, res_ids, start, stop):
		start_naive, stop_naive = start.replace(tzinfo=None), stop.replace(tzinfo=None)
		resources = self.env['resource.resource'].with_context(active_test=False).search([('id', 'in', res_ids)])
		planning_slots = self.env['hr.assistance.planning.line'].search([
			('resource_id', 'in', res_ids),
			('start_datetime', '<=', stop_naive),
			('end_datetime', '>=', start_naive),
		])
		planned_hours_mapped = defaultdict(float)
		resource_work_intervals, calendar_work_intervals = resources.sudo()._get_valid_work_intervals(start, stop)
		for slot in planning_slots:
			planned_hours_mapped[slot.resource_id.id] += slot._get_duration_over_period(
				start, stop, resource_work_intervals, calendar_work_intervals
			)
		# Compute employee work hours based on its work intervals.
		work_hours = {
			resource_id: sum_intervals(work_intervals)
			for resource_id, work_intervals in resource_work_intervals.items()
		}
		return {
			resource.id: {
				'is_material_resource': resource.resource_type == 'material',
				'resource_color': resource.color,
				'value': planned_hours_mapped[resource.id],
				'max_value': work_hours.get(resource.id, 0.0),
				'employee_id': resource.employee_id.id,
				'employee_model': 'hr.employee' if self.env.user.has_group('hr.group_hr_user') else 'hr.employee.public',
			}
			for resource in resources
		}

	def _gantt_progress_bar(self, field, res_ids, start, stop):
		if field == 'resource_id':
			return dict(
				self._gantt_progress_bar_resource_id(res_ids, start, stop),
				warning=("Como no hay contrato vigente durante este período, no se espera que este recurso trabaje un turno. Horas previstas:")
			)
		raise NotImplementedError("Esta barra de progreso no está implementada.")

	@api.model
	def gantt_progress_bar(self, fields, res_ids, date_start_str, date_stop_str):
		if not self.user_has_groups("base.group_user"):
			return {field: {} for field in fields}
		start_utc, stop_utc = string_to_datetime(date_start_str), string_to_datetime(date_stop_str)
		progress_bars = {}
		for field in fields:
			progress_bars[field] = self._gantt_progress_bar(field, res_ids[field], start_utc, stop_utc)

		return progress_bars

	def _prepare_shift_vals(self):
		""" Generar valores del turno"""
		self.ensure_one()
		return {
			'resource_id': False,
			'end_datetime': self.end_datetime,
			'role_id': self.role_id.id,
			'company_id': self.company_id.id,
			'allocated_percentage': self.allocated_percentage,
			'name': self.name,
			'recurrency_id': self.recurrency_id.id,
			'repeat': self.repeat,
			'repeat_interval': self.repeat_interval,
			'repeat_unit': self.repeat_unit,
			'repeat_type': self.repeat_type,
			'repeat_until': self.repeat_until,
			'repeat_number': self.repeat_number,
			'template_id': self.template_id.id,
		}

class HrAssistancePlanningRecurrency(models.Model):
	_name = 'hr.assistance.planning.recurrency'
	_description = "Assistance Planning Recurrence"

	slot_ids = fields.One2many('hr.assistance.planning.line', 'recurrency_id', string="Entradas de planificación relacionadas")
	repeat_interval = fields.Integer("Repite cada", default=1, required=True)
	repeat_unit = fields.Selection([
		('day', 'Días'),
		('week', 'Semanas'),
		('month', 'Meses'),
		('year', 'Años'),
	], default='week', required=True)
	repeat_type = fields.Selection([('forever', 'Por Siempre'), ('until', 'Hasta'), ('x_times', 'Número de Repeticiones')], string='Semanas', default='until')
	repeat_until = fields.Datetime(string="Repetir Hasta", help="¿Hasta qué fecha se deben repetir las planificaciones?")
	repeat_number = fields.Integer(string="Repeticiones", help="N° de repeticiones de las planificaciones")
	last_generated_end_datetime = fields.Datetime("Fecha de finalización de la última generación", readonly=True)
	company_id = fields.Many2one('res.company', string="Compañia", readonly=True, required=True, default=lambda self: self.env.company)

	_sql_constraints = [
		('check_repeat_interval_positive', 'CHECK(repeat_interval >= 1)', 'La recurrencia debe ser mayor que 0.'),
		('check_until_limit', "CHECK((repeat_type = 'until' AND repeat_until IS NOT NULL) OR (repeat_type != 'until'))", 'Una recurrencia que se repite hasta una fecha determinada debe tener su límite establecido'),
	]

	@api.constrains('repeat_number', 'repeat_type')
	def _check_repeat_number(self):
		if self.filtered(lambda t: t.repeat_type == 'x_times' and t.repeat_number < 0):
			raise ValidationError('El número de repeticiones no puede ser negativo.')

	@api.constrains('company_id', 'slot_ids')
	def _check_multi_company(self):
		for recurrency in self:
			if any(recurrency.company_id != planning.company_id for planning in recurrency.slot_ids):
				raise ValidationError('Un turno debe ser en la misma compañia que su recurrencia.')

	@api.depends('repeat_type', 'repeat_interval', 'repeat_until')
	def _compute_display_name(self):
		for recurrency in self:
			if recurrency.repeat_type == 'forever':
				name = ('Para siempre, cada %s semana(s)', recurrency.repeat_interval)
			else:
				name = ('Cada %s semana(s) hasta %s', recurrency.repeat_interval, recurrency.repeat_until)
			recurrency.display_name = name

	def _repeat_slot(self, stop_datetime=False):
		PlanningSlot = self.env['hr.assistance.planning.line']
		for recurrency in self:
			slot = PlanningSlot.search([('recurrency_id', '=', recurrency.id)], limit=1, order='start_datetime DESC')

			if slot:
				# find the end of the recurrence
				recurrence_end_dt = False
				if recurrency.repeat_type == 'until':
					recurrence_end_dt = recurrency.repeat_until
				if recurrency.repeat_type == 'x_times':
					recurrence_end_dt = recurrency._get_recurrence_last_datetime()

				# find end of generation period (either the end of recurrence (if this one ends before the cron period), or the given `stop_datetime` (usually the cron period))
				recurrency_stop_datetime = stop_datetime or PlanningSlot._add_delta_with_dst(
					fields.Datetime.now(),
					get_timedelta(3, 'month')
				)
				range_limit = min([dt for dt in [recurrence_end_dt, recurrency_stop_datetime] if dt])
				slot_duration = slot.end_datetime - slot.start_datetime

				def get_all_next_starts():
					for i in range(1, 365 * 5): # 5 years if every day
						next_start = PlanningSlot._add_delta_with_dst(
							slot.start_datetime,
							get_timedelta(recurrency.repeat_interval * i, recurrency.repeat_unit)
						)
						if next_start >= range_limit:
							return
						yield next_start

				# generate recurring slots
				resource = recurrency.slot_ids.resource_id[-1:]
				occurring_slots = PlanningSlot.search_read([
					('resource_id', '=', resource.id),
					('company_id', '=', resource.company_id.id),
					('end_datetime', '>=', slot.start_datetime),
					('start_datetime', '<=', range_limit)
				], ['start_datetime', 'end_datetime'])

				slot_values_list = []
				for next_start in get_all_next_starts():
					next_end = next_start + slot_duration
					slot_values = slot.copy_data({
						'start_datetime': next_start,
						'end_datetime': next_end,
						'recurrency_id': recurrency.id,
						'company_id': recurrency.company_id.id,
						'repeat': True,
						'state': 'draft'
					})[0]
					if any(
							next_start <= occurring_slot['end_datetime'] and
							next_end >= occurring_slot['start_datetime']
							for occurring_slot in occurring_slots
					):
						slot_values['resource_id'] = False
					slot_values_list.append(slot_values)
				if slot_values_list:
					PlanningSlot.create(slot_values_list)
					recurrency.write({'last_generated_end_datetime': slot_values_list[-1]['start_datetime']})

			else:
				recurrency.unlink()

	def _delete_slot(self, start_datetime):
		slots = self.env['hr.assistance.planning.line'].search([
			('recurrency_id', 'in', self.ids),
			('start_datetime', '>=', start_datetime),
			('state', '=', 'draft'),
		])
		slots.unlink()

	def _get_recurrence_last_datetime(self):
		self.ensure_one()
		end_datetime = self.env['hr.assistance.planning.line'].search_read([('recurrency_id', '=', self.id)], ['end_datetime'], order='end_datetime', limit=1)
		timedelta = get_timedelta((self.repeat_number - 1) * self.repeat_interval, self.repeat_unit)
		if timedelta.days > 999:
			raise ValidationError('Los turnos recurrentes no se pueden planificar con más de 999 días de antelación. Si necesita programar más allá de este límite, configure la recurrencia para que se repita para siempre.')
		return end_datetime[0]['end_datetime'] + timedelta