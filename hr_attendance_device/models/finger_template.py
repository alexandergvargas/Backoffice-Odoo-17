from odoo import models, fields, api

from ..pyzk.zk.finger import Finger


class FingerTemplate(models.Model):
    _name = 'finger.template'
    _description = 'Fingers Template'

    device_user_id = fields.Many2one('attendance.device.user', string='Usuario del Dispositivo',
                                     help='El usuario del dispositivo propietario de esta plantilla digital.')
    employee_id = fields.Many2one('hr.employee', string='Empleado',
                                  help='El empleado propietario de la huella Dactilar.', ondelete='cascade',
                                  compute='_compute_employee_id', inverse='_set_employee_id', store=True)
    uid = fields.Integer(string='Usuario Id', help='El ID (campo técnico) del usuario/empleado en el almacenamiento del dispositivo',
                         related='device_user_id.uid', store=True)
    device_id = fields.Many2one('attendance.device', string='Dispositivo de Asistencia', related='device_user_id.device_id', store=True)
    fid = fields.Integer(string='Huella Id', help='El ID de la huella dactilar en el dispositivo de asistencia.')
    valid = fields.Integer(string='Válido')
    # No queremos almacenar la plantilla como archivo adjunto ya que es posible que su formato no coincida con ningún tipo MIME y generará "binascii.Error: relleno incorrecto"
    template = fields.Binary(string='Template', attachment=False)

    @api.depends('device_user_id', 'device_user_id.employee_id')
    def _compute_employee_id(self):
        for r in self:
            if r.device_user_id and r.device_user_id.employee_id:
                r.employee_id = r.device_user_id.employee_id.id
            else:
                self._cr.execute('''SELECT employee_id FROM finger_template WHERE id = %s''', (r.id,))
                res = self._cr.fetchone()
                r.employee_id = res and res[0] or False

    def _set_employee_id(self):
        pass

    def upload_to_device(self, devices=None):
        devices = devices or self.mapped('device_id')
        device_users = self.mapped('device_user_id')
        for device in devices:
            for user in device_users.filtered(lambda u: u.device_id == device):
                fingers = []
                for template in self.filtered(lambda t: t.device_user_id == user and t.device_id == device):
                    fingers.append(Finger(template.uid, template.fid, template.valid, template.template))
                if fingers:
                    device.upload_finger_templates(user.uid, user.name, user.privilege, user.password, user.group_id, user.user_id, fingers)

