# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    checkin_device_id = fields.Many2one('attendance.device', string='Dispositivo Checkin', readonly=True, index=True,
                                        help='El dispositivo con el que el usuario realizó la accion de check in')
    checkout_device_id = fields.Many2one('attendance.device', string='Dispositivo Checkout', readonly=True, index=True,
                                         help='El dispositivo con el que el usuario realizó la accion de check out')
    # activity_id = fields.Many2one('attendance.activity', string='Tipos de Asistencia',
    #                               help='Este campo es para agrupar la asistencia en múltiples actividades (por ejemplo, horas extras, trabajo normal, etc.)')

    # @api.depends('check_in', 'check_out')
    # def _compute_worked_hours(self):
    #     for attendance in self:
    #         if attendance.check_out:
    #             delta = attendance.check_out - attendance.check_in
    #             if attendance.activity_id.name in ('DESAYUNO','ALMUERZO'):
    #                 attendance.worked_hours = (delta.total_seconds() / 3600.0)*-1
    #             else:
    #                 attendance.worked_hours = delta.total_seconds() / 3600.0
    #         else:
    #             attendance.worked_hours = False

    # @api.constrains('check_in', 'check_out', 'employee_id')
    # def _check_validity(self):
    #     pass

