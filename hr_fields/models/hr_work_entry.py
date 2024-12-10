# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import datetime, date, time
import pytz
import statistics

from odoo import fields, models, _
from odoo.exceptions import UserError

class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    cant_dias = fields.Float(string='N Dias')

    def _get_duration_batch(self):
        result = {}
        cached_periods = defaultdict(float)
        for work_entry in self:
            date_start = work_entry.date_start
            date_stop = work_entry.date_stop
            # print("date_start",date_start)
            # print("date_stop",date_stop)
            line_lunch = work_entry.employee_id.resource_calendar_id.attendance_ids.filtered(lambda linea: linea.dayofweek == str(date_start.weekday()))
            # print("line_lunch",line_lunch)
            if not date_start or not date_stop:
                result[work_entry.id] = 0.0
                continue
            if (date_start, date_stop) in cached_periods:
                result[work_entry.id] = cached_periods[(date_start, date_stop)]
            else:
                dt = date_stop - date_start
                duration = (dt.days * 24 + dt.seconds / 3600) - (line_lunch.lunch_time if len(line_lunch)==1 else 0)  # Number of hours
                # print("duration",duration)
                cached_periods[(date_start, date_stop)] = duration
                result[work_entry.id] = duration
            work_entry.cant_dias = (sum(line_lunch.mapped('duration_days'))/len(line_lunch)) if line_lunch else 0
            # print("result",result)
        return result

