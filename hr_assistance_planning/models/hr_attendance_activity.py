# -*- coding: utf-8 -*-
import math
import pytz

from odoo import api, fields,http, models, _
from odoo.tools import format_time, float_round
from odoo.addons.resource.models.utils import float_to_time
from odoo.exceptions import ValidationError,UserError
from datetime import date, datetime, timedelta, time
from random import randint, shuffle

class AttendanceActivity(models.Model):
	_name = 'attendance.activity'
	_description = 'Attendance Activity'
	_order = 'sequence'
	_rec_name = 'name'

	def _get_default_color(self):
		return randint(1, 11)

	name = fields.Char(string='Nombre', required=True, help='El nombre del tipo de asistencia. ej. Turno Mañana, Turno Tarde, etc.')
	active = fields.Boolean('Activo', default=True)
	color = fields.Integer("Color", default=_get_default_color)
	sequence = fields.Integer()

	@api.returns('self', lambda value: value.id)
	def copy(self, default=None):
		self.ensure_one()
		if default is None:
			default = {}
		if not default.get('name'):
			default['name'] = _('%s (copy)', self.name)
		return super().copy(default=default)

	@api.model
	def get_attendance_activities(self):
		activities = self.search([])
		return [{'id': activity.id, 'name': activity.name} for activity in activities]

class HrShiftTemplate(models.Model):
	_name = 'hr.shift.template'
	_description = "Shift Template"
	_order = "sequence"

	@api.model
	def _default_start_time(self):
		company_interval = self.env.company.resource_calendar_id._work_intervals_batch(
			pytz.utc.localize(datetime.combine(datetime.today().date(), time.min)),
			pytz.utc.localize(datetime.combine(datetime.today().date(), time.max)),
		)[False]
		if not company_interval:
			return
		calendar_tz = pytz.timezone(self.env.company.resource_calendar_id.tz)
		user_tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc
		end_time = calendar_tz.localize(company_interval._items[0][0].replace(tzinfo=None)).astimezone(user_tz).replace(tzinfo=None).time()
		return float_round(end_time.hour + end_time.minute / 60 + end_time.second / 3600, precision_digits=2)

	active = fields.Boolean('Activo', default=True)
	name = fields.Char('Horas', compute="_compute_name")
	sequence = fields.Integer('Sequencia', index=True)
	role_id = fields.Many2one('attendance.activity', string="Tipo de Turno")
	start_time = fields.Float('Horas Planificadas', default=_default_start_time, group_operator=None, default_export_compatible=True)
	duration = fields.Float('Duracion', group_operator=None, default_export_compatible=True)
	end_time = fields.Float('Hora Final', compute='_compute_name', group_operator=None)

	_sql_constraints = [
		('check_start_time_lower_than_24', 'CHECK(start_time < 24)', 'La hora de inicio no puede ser mayor a las 24.'),
		('check_start_time_positive', 'CHECK(start_time >= 0)', 'La hora de inicio no puede ser negativa.'),
		('check_duration_positive', 'CHECK(duration >= 0)', 'La duración no puede ser negativa.')
	]

	@api.constrains('duration')
	def _validate_duration(self):
		try:
			for shift_template in self:
				datetime.today() + shift_template._get_duration()
		except OverflowError:
			raise ValidationError("La duración seleccionada crea una fecha demasiado lejana en el futuro.")

	@api.depends('start_time', 'duration')
	def _compute_name(self):
		for shift_template in self:
			if not 0 <= shift_template.start_time < 24:
				raise ValidationError('La hora de inicio debe ser mayor o igual a 0 y menor a 24.')
			start_time = time(hour=int(shift_template.start_time), minute=round(math.modf(shift_template.start_time)[0] / (1 / 60.0)))
			# start_datetime = user_tz.localize(datetime.combine(today, start_time))
			duration = shift_template.start_time + shift_template.duration
			if duration > 24:
				shift_template.end_time = duration-24
			else:
				shift_template.end_time = duration
			end_time = time(hour=int(shift_template.end_time), minute=round(math.modf(shift_template.end_time)[0] / (1 / 60.0)))
			# print("start_time",start_time)
			# print("end_time",end_time)
			shift_template.name = '%s - %s' % (
				format_time(shift_template.env, start_time, time_format='short').replace(':00 ', ' '),
				format_time(shift_template.env, end_time, time_format='short').replace(':00 ', ' ')
			)

	@api.depends('role_id')
	def _compute_display_name(self):
		for shift_template in self:
			name = '{} {}'.format(
				shift_template.name,
				shift_template.role_id.name if shift_template.role_id.name is not False else '',
			)
			shift_template.display_name = name

	@api.model
	def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
		res = []
		for data in super(HrShiftTemplate, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy):
			if 'start_time' in data:
				data['start_time'] = float_to_time(data['start_time']).strftime('%H:%M')
			res.append(data)
		return res

	def _get_duration(self):
		self.ensure_one()
		return timedelta(hours=int(self.duration), minutes=round(math.modf(self.duration)[0] / (1 / 60.0)))