from odoo import models, fields, api


class AttendanceState(models.Model):
    _name = 'attendance.state'
    _inherit = 'mail.thread'
    _description = 'Attendance State'

    name = fields.Char(string='Nombre', help='El nombre del tipo de marcacion. ej. Entrada, Salida, etc.', required=True, tracking=True)
    activity_id = fields.Many2one('attendance.activity', string='Tipo de Asistencia', required=True,
                                  help='Tipo de asistencia, ej. Trabajo normal, horas extras, etc.', tracking=True)
    code = fields.Integer(string='Código', help='Un número entero para expresar el código de la marcacion.', required=True, tracking=True)
    type = fields.Selection([('checkin', 'Check-in'),
                            ('checkout', 'Check-out')], string='Tipo de Actividad', required=True, tracking=True)

    _sql_constraints = [
        ('code_unique',
         'UNIQUE(code)',
         "¡El Código debe ser único!"),
        ('name_activity_id_unique',
         'UNIQUE(name, activity_id)',
         "¡El nombre debe ser único dentro de los tipos de marcacion!"),
        ('name_activity_id_unique',
         'UNIQUE(type, activity_id)',
         "¡El tipo de asistencia y la actividad deben ser únicos! Vuelva a verificar si ha definido previamente un tipo de marcacion con el mismo tipo de asistencia y actividad."),
    ]

    def name_get(self):
        """name_get que admite la visualización de etiquetas con su código como prefijo"""
        result = []
        for r in self:
            result.append((r.id, '[' + r.activity_id.name + '] ' + r.name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """name_search que admite la búsqueda por código de etiqueta"""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('activity_id.name', '=ilike', name + '%'), ('name', operator, name)]
        state = self.search(domain + args, limit=limit)
        return state.name_get()

