from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import remove_accents, date_utils, relativedelta

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    unamapped_attendance_device_ids = fields.Many2many('attendance.device', 'device_employee_rel', 'employee_id', 'device_id',
                                                       string='Dispositivos no asignados',
                                                       help='Los dispositivos que aún no han almacenado a este empleado como usuario.'
                                                       ' Cuando asigna un empleado a un usuario de un dispositivo, el dispositivo desaparecerá de esta lista.')
    created_from_attendance_device = fields.Boolean(string='Creado desde el dispositivo', readonly=True, groups="hr.group_hr_user",
                                                    help='Este campo indica que el empleado fue creado a partir de los datos de un dispositivo de asistencia.')
    finger_templates_ids = fields.One2many('finger.template', 'employee_id', string='Huella Dactilar', readonly=True)
    total_finger_template_records = fields.Integer(string='Huellas Dactilares', compute='_compute_total_finger_template_records')
    device_user_ids = fields.One2many('attendance.device.user', 'employee_id', string='Usuarios de dispositivos asignados')

    def _compute_total_finger_template_records(self):
        for r in self:
            r.total_finger_template_records = len(r.finger_templates_ids)

    @api.model_create_multi
    def create(self, vals_list):
        employees = super(HrEmployee, self).create(vals_list)
        attendance_device_ids = self.env['attendance.device'].sudo().with_context(active_test=False).search([])
        if attendance_device_ids:
            employees.write({'unamapped_attendance_device_ids': [(6, 0, attendance_device_ids.ids)]})
        return employees

    def write(self, vals):
        if 'barcode' in vals:
            DeviceUser = self.env['attendance.device.user'].sudo()
            for r in self.filtered(lambda emp: emp.barcode):
                if DeviceUser.search([('employee_id', '=', r.id)], limit=1):
                    raise ValidationError(_("El empleado '%s' actualmente es referido por un usuario de dispositivo de asistencia."
                                            " Por lo tanto, no puede cambiar el Badge ID del empleado.") % (r.name,))
        return super(HrEmployee, self).write(vals)

    def _get_unaccent_name(self):
        return remove_accents(self.name)

    def _prepare_device_user_data(self, device):
        return {
            'uid': device.get_next_uid(),
            'name': self._get_unaccent_name() if device.unaccent_user_name else self.name,
            'password': '',
            'privilege': 0,
            'group_id': '0',
            'user_id': self.barcode,
            'employee_id': self.id,
            'device_id': device.id,
            }

    def create_device_user_if_not_exist(self, device):
        data = self._prepare_device_user_data(device)
        domain = [('device_id', '=', device.id)]
        if device.unique_uid:
            domain += [('uid', '=', int(data['uid']))]
        else:
            domain += [('user_id', '=', str(data['user_id']))]
        user = self.env['attendance.device.user'].search(domain, limit=1)
        if not user:
            user = self.env['attendance.device.user'].create(data)
        else:
            update_vals = {
                'employee_id': self.id,
                }
            if device.unique_uid:
                update_vals.update({
                    'user_id': self.barcode
                    })
            else:
                update_vals.update({
                    'uid': int(data['uid'])
                    })
            user.write(update_vals)
        return user

    def upload_to_attendance_device(self, device):
        self.ensure_one()
        if not self.barcode:
            raise ValidationError(_("Empleado '%s' no tiene un Badge ID especificado!"))
        device_user = self.create_device_user_if_not_exist(device)
        device_user.setUser()

    def action_view_finger_template(self):
        action = self.env.ref('hr_attendance_device.action_finger_template')
        result = action.read()[0]

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        total_finger_template_records = self.total_finger_template_records
        if total_finger_template_records != 1:
            result['domain'] = "[('employee_id', 'in', " + str(self.ids) + ")]"
        elif total_finger_template_records == 1:
            res = self.env.ref('hr_attendance_device.view_finger_template_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.finger_templates_ids.id
        return result
