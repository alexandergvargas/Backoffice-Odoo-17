from odoo import models, fields

from odoo.addons.base.models.res_partner import _tz_get


class AttendanceDeviceLocation(models.Model):
    _name = 'attendance.device.location'
    _description = 'Device Location'

    name = fields.Char(string='Nombre', required=True)
    tz = fields.Selection(_tz_get, string='Zona Horaria', default=lambda self: self.env.context.get('tz') or self.env.user.tz,
                          help="La zona horaria del dispositivo, utilizada para generar valores de fecha y hora adecuados dentro de los informes de asistencia. "
                               "Es importante establecer un valor para este campo.")

