# -*- coding:utf-8 -*-

from odoo.tools import float_compare
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round

class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    @api.model
    def store_resource_calendar(self):
        for calendar in self.env['resource.calendar'].search([('name', 'in', ['Standard 38 hours/week', 'Standard 35 hours/week'])]):
            calendar.active = False

    def _get_hours_per_day(self, attendances):

        if not attendances:
            return 0

        hour_count = 0.0
        for attendance in attendances:
            hour_count += attendance.hour_to - attendance.hour_from - attendance.lunch_time

        if self.two_weeks_calendar:
            number_of_days = len(set(attendances.filtered(lambda cal: cal.week_type == '1').mapped('dayofweek')))
            number_of_days += len(set(attendances.filtered(lambda cal: cal.week_type == '0').mapped('dayofweek')))
        else:
            number_of_days = len(set(attendances.mapped('dayofweek')))

        if not number_of_days:
            return 0

        return float_round(hour_count / float(number_of_days), precision_digits=2)

    @api.depends('attendance_ids.hour_from', 'attendance_ids.hour_to', 'attendance_ids.work_entry_type_id.is_leave')
    def _compute_hours_per_week(self):
        for calendar in self:
            sum_hours = sum((a.hour_to - a.hour_from - a.lunch_time) for a in calendar.attendance_ids if a.day_period != 'lunch' and not a.work_entry_type_id.is_leave)
            calendar.hours_per_week = sum_hours / 2 if calendar.two_weeks_calendar else sum_hours

class ResourceCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'

    lunch_time = fields.Float('Refrigerio')
