from odoo import models, fields, api


class AttendanceActivity(models.Model):
    _inherit = 'attendance.activity'

    # name = fields.Char(string='Nombre', required=True, help='El nombre del tipo de asistencia. ej. Asistencia, Horas extras, etc.')
    attendance_status_ids = fields.One2many('attendance.state', 'activity_id', string='Tipos de Marcacion', help='Los estados de check-in y check-out de esta marcacion')
    status_count = fields.Integer(string='Recuento', compute='_compute_status_count')

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', "¡El nombre del tipo de asistencia debe ser único!"),
    ]

    @api.depends('attendance_status_ids')
    def _compute_status_count(self):
        for r in self:
            r.status_count = len(r.attendance_status_ids)

    def getAttendance(self, device_id=None, user_id=None):
        domain = [('attendance_state_id', 'in', self.mapped('attendance_status_ids').ids)]
        if device_id:
            domain += [('device_id', '=', device_id.id)]

        if user_id:
            domain += [('user_id', '=', user_id.id)]

        return self.env['user.attendance'].search(domain)
