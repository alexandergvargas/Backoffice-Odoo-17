import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AttendanceWizard(models.TransientModel):
    _name = 'attendance.wizard'
    _description = 'Attendance Wizard'

    @api.model
    def _get_all_device_ids(self):
        all_devices = self.env['attendance.device'].search([('state', '=', 'confirmed')])
        if all_devices:
            return all_devices.ids
        else:
            return []

    device_ids = fields.Many2many('attendance.device', string='Dispositivos', default=_get_all_device_ids, domain=[('state', '=', 'confirmed')])
    fix_attendance_valid_before_synch = fields.Boolean(string='Arreglar Asistencia Válido', help="Si está marcado, Odoo volverá a calcular todos los datos de asistencia para su validez"
                                                     " antes de sincronizarlos con Asistencia de Recursos Humanos (al presionar el botón 'Sincronizar asistencia')")

    def download_attendance_manually(self):
        # TODO: remove me after 12.0
        self.action_download_attendance()

    def _download_device_attendance(self, devices):
        for device in devices:
            try:
                 with self.pool.cursor() as cr:
                    device.with_env(self.env(cr=cr)).action_attendance_download()
            except Exception as e:
                _logger.error(e)

    def action_download_attendance(self):
        if not self.device_ids:
            raise UserError(_('¡Debes seleccionar al menos un dispositivo para continuar!'))
        self._download_device_attendance(self.device_ids)

    def cron_download_device_attendance(self):
        devices = self.env['attendance.device'].search([('state', '=', 'confirmed')])
        self._download_device_attendance(devices)

    def cron_sync_attendance(self):
        self.env['user.attendance']._cron_synch_hr_attendance()

    def sync_attendance(self):
        # TODO: rename me into `action_sync_attendance` in master/14+
        """
        Este método sincronizará todos los datos de asistencia descargados con los datos de asistencia de Odoo.
        No descarga datos de asistencia de los dispositivos.
        """
        self.env['user.attendance']._cron_synch_hr_attendance()

    def clear_attendance(self):
        # TODO: rename me into `action_clear_attendance` in master/14+
        if not self.device_ids:
            raise UserError(_('¡Debes seleccionar al menos un dispositivo para continuar!'))
        if not self.env.user.has_group('hr_attendance.group_hr_attendance_manager'):
            raise UserError(_('Solo los administradores de asistencia de recursos humanos pueden borrar manualmente los datos de asistencia del dispositivo'))

        for device in self.device_ids:
                device.clearAttendance()

    def action_fix_user_attendance_valid(self):
        self.env['user.attendance'].search([])._update_valid()
