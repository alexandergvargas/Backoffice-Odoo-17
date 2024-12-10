import logging
import pytz
from datetime import datetime

from odoo import models, fields, api, registry, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import format_datetime
from odoo.osv import expression
from odoo.addons.base.models.res_partner import _tz_get

from ..pyzk.zk import ZK
from ..pyzk.zk.user import User
from ..pyzk.zk.exception import ZKErrorResponse, ZKNetworkError, ZKConnectionUnauthorized

_logger = logging.getLogger(__name__)


class AttendanceDevice(models.Model):
    _name = 'attendance.device'
    _description = 'Attendance Device'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_default_attendance_states(self):
        att_state_ids = self.env['attendance.state']

        # Asistencia laboral normal
        attendance_device_state_code_0 = self.env.ref('hr_attendance_device.attendance_device_state_code_0')
        if attendance_device_state_code_0:
            att_state_ids += attendance_device_state_code_0
        attendance_device_state_code_1 = self.env.ref('hr_attendance_device.attendance_device_state_code_1')
        if attendance_device_state_code_1:
            att_state_ids += attendance_device_state_code_1

        # Asistencia al trabajo en horas extras
        attendance_device_state_code_4 = self.env.ref('hr_attendance_device.attendance_device_state_code_4')
        if attendance_device_state_code_4:
            att_state_ids += attendance_device_state_code_4
        attendance_device_state_code_5 = self.env.ref('hr_attendance_device.attendance_device_state_code_5')
        if attendance_device_state_code_5:
            att_state_ids += attendance_device_state_code_5
        return att_state_ids

    @api.model
    def _get_default_attendance_device_state_lines(self):
        attendance_device_state_line_data = []
        for state in self._get_default_attendance_states():
            attendance_device_state_line_data.append(
                (0, 0, {
                    'attendance_state_id': state.id,
                    'code': state.code,
                    'type': state.type,
                    'activity_id': state.activity_id.id
                    })
                )
        return attendance_device_state_line_data

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('cancelled', 'Cancelado')
        ], string='Estado', default='draft', index=True, copy=False, required=True, tracking=True)

    name = fields.Char(string="Nombre", required=True, help='El nombre del dispositivo de asistencia.', tracking=True, copy=True, default='/', readonly=False)

    firmware_version = fields.Char(string='Versión de Firmware', readonly=True,
                                   help="La versión de firmware del dispositivo que se completará automáticamente cuando presione el botón 'Obtener información del dispositivo'.")
    serialnumber = fields.Char(string='Número de Serie', readonly=True,
                               help="El número de serie del dispositivo que se completará automáticamente cuando presione el botón 'Obtener información del dispositivo'.")
    oem_vendor = fields.Char(string='Marca (Proveedor)', readonly=True,
                               help="El proveedor OEM del dispositivo que se completará automáticamente cuando presione el botón 'Obtener información del dispositivo'.")
    platform = fields.Char(string='Plataforma', readonly=True,
                               help="La plataforma del dispositivo que se completará automáticamente cuando presione el botón 'Obtener información del dispositivo'.")
    fingerprint_algorithm = fields.Char(string='Algoritmo de Huellas Dactilares', readonly=True,
                               help="El algoritmo de huellas dactilares (también conocido como ZKFPVersion) del dispositivo que se completará automáticamente cuando presione el botón 'Obtener información del dispositivo'.")
    device_name = fields.Char(string='Modelo', readonly=True,
                               help="El modelo del dispositivo que se completará automáticamente cuando presione el botón 'Obtener información del dispositivo'.")

    work_code = fields.Char(string='Código de trabajo', readonly=True,
                               help="El código de trabajo del dispositivo que se completará automáticamente cuando presione el botón 'Obtener información del dispositivo'.")

    ip = fields.Char(string="IP/Nombre de Dominio", required=True, tracking=True, copy=False, readonly=False, default='0.0.0.0',
                     help='La IP accesible o el nombre de dominio del dispositivo para obtener los datos de asistencia del dispositivo')
    port = fields.Integer(string="Puerto", required=True, default=4370, tracking=True, readonly=False)
    timeout = fields.Integer(string='Timeout', default=20, required=True, help='Tiempo de espera de conexión en segundos', tracking=True, readonly=False)
    description = fields.Text(string="Descripción")
    user_id = fields.Many2one('res.users', string="Técnico", tracking=True, default=lambda self: self.env.user)
    device_user_ids = fields.One2many('attendance.device.user', 'device_id', string='Usuarios del Dispositivo',
                                      help='Lista de Usuarios almacenados en el dispositivo de asistencia')
    device_users_count = fields.Integer(string='Cantidad de usuarios', compute='_compute_device_users_count', store=True)

    mapped_employee_ids = fields.Many2many('hr.employee', 'mapped_device_employee_rel', string='Empleados mapeados',
                                           compute='_compute_employees', store=True,
                                           help="Lista de empleados que han sido asignados con los usuarios de este dispositivo")

    mapped_employees_count = fields.Integer(string='Cantidad de empleados mapeados', compute='_compute_mapped_employees_count', store=True)

    umapped_device_user_ids = fields.One2many('attendance.device.user', 'device_id', string='Usuarios no mapeados del dispositivo',
                                              domain=[('employee_id', '=', False)],
                                              help='Lista de usuarios de dispositivos que no han sido asignados a un empleado')
    umapped_device_user_count = fields.Integer(string='Cant usuarios no mapeados', compute='_compute_umapped_device_user_count', store=True)

    unmapped_employee_ids = fields.Many2many('hr.employee', 'device_employee_rel', 'device_id', 'employee_id',
                                             compute='_compute_employees', store=True, string='Empleados no mapeados',
                                             help="Los empleados que no hayan sido mapeados con ningún usuario de este dispositivo")

    attendance_device_state_line_ids = fields.One2many('attendance.device.state.line', 'device_id', string='State Codes', copy=False,
                                                       default=_get_default_attendance_device_state_lines, readonly=False)
    location_id = fields.Many2one('attendance.device.location', string='Ubicación', tracking=True, required=True, readonly=False,
                                  help='La ubicación donde se encuentra el dispositivo.')

    ignore_unknown_code = fields.Boolean(string='Ignorar Código Desconocido', default=False, tracking=True, readonly=False,
                                         help='A veces no deseas cargar datos de asistencia con el estado '
                                         'codifica aquellos no declarados en la siguiente tabla. En tal caso, marque este campo.')

    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company, readonly=False)

    auto_clear_attendance = fields.Boolean(string='Borrar datos de asistencia automáticamente', default=False, tracking=True, readonly=False,
                                            help='Marque esto para borrar todos los datos de asistencia del dispositivo después de descargarlos en Odoo.')

    auto_clear_attendance_schedule = fields.Selection([
        ('on_download_complete', 'Al finalizar la descarga'),
        ('time_scheduled', 'Hora programada')], string='Horario de Borrado Automático', required=True, default='on_download_complete', tracking=True,
        help="Al finalizar la descarga: elimine los datos de asistencia tan pronto como finalice la descarga\n"
        "Hora programada: elimine los datos de asistencia en la hora especificada a continuación")
    auto_clear_attendance_hour = fields.Float(string='Borrado automático en', tracking=True, required=True, default=0.0,
                                               help="La hora (en la zona horaria del dispositivo de asistencia) para borrar los datos de asistencia después de la descarga.")

    auto_clear_attendance_dow = fields.Selection([
        ('-1', 'Cada día'),
        ('0', 'Lunes'),
        ('1', 'Martes'),
        ('2', 'Miércoles'),
        ('3', 'Jueves'),
        ('4', 'Viernes'),
        ('5', 'Sábado'),
        ('6', 'Domingo'), ], string='Borrado automático activado', default='-1', required=True, tracking=True)

    auto_clear_attendance_error_notif = fields.Boolean(string='Notificación de Asistencia de Borrado Automático.', default=True, tracking=True,
                                                        help='Notificar si no se encuentra ninguna caja fuerte para borrar los datos de asistencia')

    tz = fields.Selection(_tz_get, string='Zona Horaria', compute='_compute_tz', store=True,
                          help="La zona horaria del dispositivo, utilizada para generar valores de fecha y hora adecuados dentro de los informes de asistencia.")

    active = fields.Boolean(string='Activo', default=True, tracking=True, readonly=True)
    unique_uid = fields.Boolean(string='Unico UID', default=True, required=True, tracking=True, readonly=False,
                                help='Algunos dispositivos defectuosos permiten la duplicación de uid. En este caso, desmarque este campo. Pero se recomienda cambiar su dispositivo.')
    last_attendance_download = fields.Datetime(string='Última sincronización.', readonly=True,
                                               help='La última vez que los datos de asistencia se descargaron del dispositivo a Odoo.')

    map_before_dl = fields.Boolean(string='Mapeo del empleado antes de descargar', default=True,
                                   help='Intente siempre mapear a los usuarios y empleados (si se encuentran nuevos) antes de descargar los datos de asistencia.')
    create_employee_during_mapping = fields.Boolean(string='Generar empleados durante el mapeo', default=False,
                                                    help="Si está marcado, durante la asignación entre los usuarios del dispositivo y los empleados de la empresa, los usuarios de dispositivos no asignados intentarán "
                                                    " crear un nuevo empleado y luego asignarán en consecuencia.")

    download_error_notification = fields.Boolean(string='Descargar notificación de error', default=True, readonly=False,
                                                 help='Habilite esto para recibir notificaciones cuando se produzca un error de descarga de datos.')
    debug_message = fields.Boolean(string='Mensaje de depuración', default=False, help="Si está marcado, los mensajes de depuración se publicarán en"
                                   " OpenChatter con fines de depuración.")

    user_attendance_ids = fields.One2many('user.attendance', 'device_id', string='Datos de Asistencia', readonly=True)
    total_att_records = fields.Integer(string='Registros de Asistencia', compute='_compute_total_attendance_records')
    finger_template_ids = fields.One2many('finger.template', 'device_id', string='Huella Dactilar', readonly=True)
    total_finger_template_records = fields.Integer(string='Huellas Dactilares', compute='_compute_total_finger_template_records')
    protocol = fields.Selection([('udp', 'UDP'), ('tcp', 'TCP')], string='Protocolo', required=True, default='tcp', tracking=True,
                                help="Algunos dispositivos antiguos no admiten TCP. En tal caso, intente cambiar a UDP.")
    omit_ping = fields.Boolean(string='Omitir Ping', default=True, readonly=False, help='Omita la dirección IP de ping al conectarse al dispositivo.')
    password = fields.Char(string='Password', readonly=False, help="La contraseña para autenticar el dispositivo, si es necesario.")

    unaccent_user_name = fields.Boolean(string='Usuario sin acento', default=True, tracking=True,
                                        help="Algunos dispositivos admiten nombres Unicode como ZKTeco K50, otros no. Además de esto,"
                                        " el campo de nombre en los dispositivos suele estar limitado a unos 24 caracteres latinos o menos"
                                        " caracteres Unicode. A veces, la falta de acento es una solución para los nombres Unicode largos.")
    # 65472 (0xFFc0) is the max size of TCP in the original pyzk (use in the method base.read_with_buffer as MAX_CHUNK)
    max_size_TCP = fields.Selection([('65472', '65472 bytes'),
                                     ('32768', '32768 bytes'),
                                     ('16384', '16384 bytes'),
                                     ('8192', '8192 bytes'),
                                     ('4096', '4096 bytes'),
                                     ('2048', '2048 bytes'),
                                     ('1024', '1024 bytes'),
                                     ], string='TCP Max-Size', default='65472', required=True,
                                     help="El valor predeterminado (65472) funciona bien para casi dispositivos de asistencia. Sin embargo, en algunos casos excepcionales,"
                                     " puede aparecer el error [Errno 32] al obtener datos de los dispositivos. En tal caso, puede intentar"
                                     " disminuir este valor para ver si ayuda.\n"
                                     "Nota: cuanto menor sea este valor, más lenta será la obtención de datos")
    # 16384 is the max size of UDP in the original pyzk (use in the method base.read_with_buffer)
    max_size_UDP = fields.Selection([('65472', '65472 bytes'),
                                     ('32768', '32768 bytes'),
                                     ('16384', '16384 bytes'),
                                     ('8192', '8192 bytes'),
                                     ('4096', '4096 bytes'),
                                     ('2048', '2048 bytes'),
                                     ('1024', '1024 bytes'),
                                     ], string='UDP Max-Size', default='16384', required=True,
                                     help="The default value (16384) works well for almost attendance devices. However, in some rare cases,"
                                     " the error 'timed out' may occur while getting data from devices. In such situation, you may try on decreasing this value to see if it would help\n."
                                     "Note: the smaller this value is, the slower data getting will be.")

    zk_cache = {}

    _sql_constraints = [
        ('ip_and_port_unique', 'UNIQUE(ip, port, location_id)',
         "¡No puedes tener más de un dispositivo con la misma ip y puerto en la misma ubicación!"),
    ]

    @property
    def zk(self):
        """
        This method return a ZK object.
        Si se creó un objeto correspondiente al parámetro de conexión y está disponible en
        self.zk_cache, se devolverá. Para evitarlo, llámalo con .with_context(no_zk_cache=True)
        """
        self.ensure_one()
        force_udp = self.protocol == 'udp'
        password = self.password or 0
        cached_key = (self.protocol, self.omit_ping, self.timeout, password, self.max_size_TCP, self.max_size_UDP, self.ip, self.port)

        if not cached_key in self.zk_cache.keys() or self.env.context.get('no_zk_cache', False):
            self.zk_cache[cached_key] = ZK(self.ip, self.port, self.timeout, password=password, force_udp=force_udp, ommit_ping=self.omit_ping,
                                           max_size_TCP=int(self.max_size_TCP), max_size_UDP=int(self.max_size_UDP))
        return self.zk_cache[cached_key]

    @api.depends('location_id.tz')
    def _compute_tz(self):
        default_tz = self.env.context.get('tz') or self.env.user.tz
        for r in self:
            if r.location_id and r.location_id.tz:
                r.tz = r.location_id.tz
            else:
                r.tz = default_tz

    def name_get(self):
        """name_get que admite mostrar el nombre de la ubicación y el modelo como prefijo"""
        result = []
        for r in self:
            name = r.name
            if r.oem_vendor:
                if r.device_name:
                    name = "[%s %s] %s" % (r.oem_vendor, r.device_name, name)
                else:
                    name = "[%s] %s" % (r.oem_vendor, name)
            if r.location_id:
                name = "[%s] %s" % (r.location_id.name, name)
            result.append((r.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """búsqueda de nombres que admite la búsqueda por código de etiqueta"""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('location_id.name', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&'] + domain
        state = self.search(domain + args, limit=limit)
        return state.name_get()

    @api.depends('device_user_ids', 'device_user_ids.active')
    def _compute_device_users_count(self):
        total_att_data = self.env['attendance.device.user'].read_group([('device_id', 'in', self.ids)], ['device_id'], ['device_id'])
        mapped_data = dict([(dict_data['device_id'][0], dict_data['device_id_count']) for dict_data in total_att_data])
        for r in self:
            r.device_users_count = mapped_data.get(r.id, 0)

    def _compute_total_finger_template_records(self):
        total_att_data = self.env['finger.template'].read_group([('device_id', 'in', self.ids)], ['device_id'], ['device_id'])
        mapped_data = dict([(dict_data['device_id'][0], dict_data['device_id_count']) for dict_data in total_att_data])
        for r in self:
            r.total_finger_template_records = mapped_data.get(r.id, 0)

    def _compute_total_attendance_records(self):
        total_att_data = self.env['user.attendance'].read_group([('device_id', 'in', self.ids)], ['device_id'], ['device_id'])
        mapped_data = dict([(dict_data['device_id'][0], dict_data['device_id_count']) for dict_data in total_att_data])
        for r in self:
            r.total_att_records = mapped_data.get(r.id, 0)

    @api.depends('device_user_ids', 'device_user_ids.active', 'device_user_ids.employee_id', 'device_user_ids.employee_id.active')
    def _compute_employees(self):
        HrEmployee = self.env['hr.employee']
        for r in self:
            r.update({
                'unmapped_employee_ids':[(6, 0, HrEmployee.search([('id', 'not in', r.device_user_ids.mapped('employee_id').ids),('company_id', '=', self.env.company.id)]).ids)],
                'mapped_employee_ids': [(6, 0, r.device_user_ids.mapped('employee_id').filtered(lambda employee: employee.active == True).ids)],
                })

    @api.depends('mapped_employee_ids')
    def _compute_mapped_employees_count(self):
        for r in self:
            r.mapped_employees_count = len(r.mapped_employee_ids)

    @api.depends('umapped_device_user_ids')
    def _compute_umapped_device_user_count(self):
        for r in self:
            r.umapped_device_user_count = len(r.umapped_device_user_ids)

    @api.onchange('unique_uid')
    def onchange_unique_uid(self):
        if not self.unique_uid:
            message = _('Esto es para experimentar y verificar si el dispositivo contiene datos incorrectos con non-unique user\'s uid.'
                        ' Desactivar esta opción permitirá mapear el user_id del usuario del dispositivo con el user_id del usuario en Odoo.\n'
                        'NOTA:\n'
                        '- Los ID de usuario no latinos no son compatibles.\n'
                        '- No desactive esta opción en producción.')
            return {
                'warning': {
                    'title': "Warning!",
                    'message': message,
                },
            }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'ip' in vals:
                vals['ip'] = vals['ip'].strip()
        return super(AttendanceDevice, self).create(vals_list)

    def write(self, vals):
        if 'ip' in vals:
            vals['ip'] = vals['ip'].strip()
        return super(AttendanceDevice, self).write(vals)

    def delUser(self, uid, user_id):
        '''eliminar usuario específico por uid'''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.delete_user(uid, user_id)
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('No se pudo eliminar el usuario con uid "%s", user_id "%s" del dispositivo %s\n%s')
                                  % (uid, user_id, self.display_name, e))
        finally:
            self.enableDevice()
            self.disconnect()

    def upload_finger_templates(self, uid, name, privilege, password, group_id, user_id, fingers):
        user = User(uid, name, privilege, password, group_id, user_id, card=0)
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.save_user_template(user, fingers)
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("No se pudo configurar la huella dactilar en el dispositivo %s. Aqui esta la informacion:\n"
                                    "user_id: %s\n"
                                    "Información de depuración:\n%s")
                                  % (self.display_name, user_id, e))
        finally:
            self.enableDevice()
            self.disconnect()

    def delFingerTemplate(self, uid, fid, user_id):
        '''eliminar plantilla de dedo por uid y fid'''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.delete_user_template(uid, fid, user_id)
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('No se pudo eliminar la huella dactilar con fid "%s" of uid "%s" desde el dispositivo %s') % (fid, uid, self.display_name,))
        finally:
            self.enableDevice()
            self.disconnect()

    def get_next_uid(self):
        '''devolver el uid máximo de usuarios en el dispositivo de asistencia'''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.get_next_uid()
        except Exception as e:
            _logger.error(str(e))
            raise ValidationError(_('No se pudo obtener el máximo uid del dispositivo %s\n'
                                    'Si se había conectado a su dispositivo, quizás su dispositivo tuvo un problema.\n'
                                    'Aquí está el mensaje de error de depuración:\n%s') % (self.display_name, str(e)))
        finally:
            self.enableDevice()
            self.disconnect()


    # CONEXION AL DISPOSITIVO
    def action_check_connection(self):
        self.ensure_one()
        if self.connect():
            self.disconnect()
            raise UserError(_('La conexion al Dispositivo %s fue Satisfactorio') % (self.display_name,))

    def connect(self):
        self.ensure_one()

        def post_message():
            email_template_id = self.env.ref('hr_attendance_device.email_template_attendance_device')
            cr = registry(self._cr.dbname).cursor()
            self.with_env(self.env(cr=cr)).post_message(email_template_id)
            cr.commit()
            cr.close()

        error_msg = False
        try:
            return self.zk.connect()
        except ZKNetworkError as e:
            error_msg = _("No se puede Conectar al dispositivo %s (ping %s)") % (self.display_name, self.ip)
        except ZKConnectionUnauthorized as e:
            error_msg = _("¡Conexión no autorizada! El dispositivo %s puede requerir contraseña") % self.display_name
        except ZKErrorResponse as e:
            error_msg = _("No se pudo conectar al dispositivo %s. Esto generalmente se debe a un error de red o a una selección de"
                    " protocolo incorrecta o a que se requiere autenticación de contraseña.\n"
                    "Debugging info:\n%s") % (self.display_name, e)
        except Exception as e:
            error_msg = _("No se pudo conectar con el dispositivo '%s'. Verifique la configuración de su red"
                          " y la contraseña del dispositivo y/o reinicie su dispositivo") % (self.display_name,)

        if error_msg:
            post_message()
            raise ValidationError(error_msg)

    def disconnect(self):
        try:
            return self.zk.disconnect()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("No se pudo desconectar el dispositivo %s. Aquí está la información de depuración:\n%s")
                                  % (self.display_name, e))

    @api.model
    def post_message(self, email_template):
        if self.user_id:
            self.message_subscribe([self.user_id.partner_id.id])
        if email_template:
            self.message_post_with_source(email_template)

    # OBTENER INFORMACION DEL DISPOSITIVO
    def action_device_information(self):
        dbname = self._cr.dbname
        for r in self:
            try:
                cr = registry(dbname).cursor()
                r = r.with_env(r.env(cr=cr))
                r.connect()
                r.firmware_version = r.zk.get_firmware_version()
                r.serialnumber = r.zk.get_serialnumber()
                r.platform = r.zk.get_platform()
                r.fingerprint_algorithm = r.zk.get_fp_version()
                r.device_name = r.zk.get_device_name()
                r.work_code = r.zk.get_workcode()
                r.oem_vendor = r.zk.get_oem_vendor()
            except Exception as e:
                _logger.error(e)
            finally:
                r.state='confirmed'
                cr.commit()
                cr.close()

    def getFirmwareVersion(self):
        '''
        devolver la versión del firmware
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_firmware_version()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("No se pudo obtener la versión de firmware del dispositivo %s. Aquí está la información de depuración:\n%s")
                                  % (self.display_name, e))
        finally:
            self.disconnect()

    def getSerialNumber(self):
        '''
        devolver el número de serie
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_serialnumber()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("No se pudo obtener el número de serie del dispositivo %s. Aquí está la información de depuración.:\n%s")
                                  % (self.display_name, e))
        finally:
            self.disconnect()

    def getPlatform(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_platform()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('No se pudo obtener la plataforma del dispositivo %s. Aquí está la información de depuración:\n%s')
                                  % (self.display_name, e))
        finally:
            self.disconnect()

    def getFingerprintAlgorithm(self):
        '''
        devolver el algoritmo de huellas dactilares
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_fp_version()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('No se pudo obtener el algoritmo de huellas digitales del dispositivo %s. Aquí está la información de depuración:\n%s')
                                  % (self.display_name, e))
        finally:
            self.disconnect()

    def getDeviceName(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_device_name()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('No se pudo obtener el nombre del dispositivo %s. Aquí está la información de depuración:\n%s')
                                  % (self.display_name, e))
        finally:
            self.disconnect()

    def getWorkCode(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_workcode()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('No se pudo obtener el Work Code del dispositivo %s. Aquí está la información de depuración.:\n%s')
                                  % (self.display_name, e))
        finally:
            self.disconnect()

    def getOEMVendor(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_oem_vendor()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('No se pudo obtener el proveedor OEM del dispositivo %s. Aquí está la información de depuración:\n%s')
                                  % (self.display_name, e))
        finally:
            self.disconnect()

    # DESCARGAR ASISTENCIA DEL DISPOSITIVO
    def action_attendance_download(self):
        DeviceUserAttendance = self.env['user.attendance']
        AttendanceUser = self.env['attendance.device.user']

        for r in self:
            error_msg = ""
            if r.map_before_dl:
                r.action_finger_template_download()

            attendance_states = {}
            for state_line in r.attendance_device_state_line_ids:
                attendance_states[state_line.attendance_state_id.code] = state_line.attendance_state_id.id

            attendance_data = r.getAttendance()
            for attendance in attendance_data:
                if attendance.punch not in attendance_states.keys():
                    if not r.ignore_unknown_code:
                        raise UserError('Encontramos el código de estado de asistencia "%s" en su dispositivo %s '
                                      'pero no se encontró dicho código en la configuración del dispositivo en Odoo. '
                                      'Por favor vaya al dispositivo %s y agregue este código de asistencia.\n'
                                      'En caso de que desee ignorar la carga de datos de asistencia con este código, '
                                      ' vaya a la configuración del dispositivo en Odoo y marque "Ignorar código Desconocido".'
                                    % (attendance.punch, r.display_name, r.display_name))
                    else:
                        continue

                user_id = AttendanceUser.with_context(active_test=False).search([
                    ('user_id', '=', attendance.user_id),
                    ('device_id', '=', r.id)], limit=1)
                if user_id:
                    utc_timestamp = r.convert_time_to_utc(attendance.timestamp, r.tz)
                    str_utc_timestamp = fields.Datetime.to_string(utc_timestamp)
                    duplicate_attend = DeviceUserAttendance.search([
                        ('device_id', '=', r.id),
                        ('user_id', '=', user_id.id),
                        ('timestamp', '=', str_utc_timestamp)], limit=1)

                    if not duplicate_attend:
                        try:
                            vals = {
                                'device_id': r.id,
                                'user_id': user_id.id,
                                'timestamp': str_utc_timestamp,
                                'status': attendance.punch,
                                'attendance_state_id': attendance_states[attendance.punch]
                                }

                            DeviceUserAttendance.create(vals)
                        except Exception as e:
                            error_msg += str(e) + "<br />"
                            error_msg += _("Error create DeviceUserAttendance record: device_id %s; user_id %s; timestamp %s; attendance_state_id %s.<br />") % (
                                r.id,
                                user_id.id,
                                format_datetime(r.env, attendance.timestamp, r.tz),
                                attendance_states[attendance.punch]
                                )
                            _logger.error(error_msg)
                            pass
            r.last_attendance_download = fields.Datetime.now()
            if error_msg and r.debug_message:
                r.message_post(body=error_msg)

            if not r.auto_clear_attendance:
                continue

            if r.auto_clear_attendance_schedule == 'on_download_complete':
                r.action_attendance_clear()
            elif r.auto_clear_attendance_schedule == 'time_scheduled':
                # datetime in the timezone of the device
                dt_now = self.convert_utc_time_to_tz(datetime.utcnow(), r.tz)
                float_dt_now = self.time_to_float_hour(dt_now)

                if int(r.auto_clear_attendance_dow) == -1 or dt_now.weekday() == int(r.auto_clear_attendance_dow):
                    delta = r.auto_clear_attendance_hour - float_dt_now
                    if abs(delta) <= 0.5 or abs(delta) >= 23.5:
                        r.action_attendance_clear()

    def getAttendance(self):
        post_err_msg = False
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.get_attendance()

        except Exception as e:
            _logger.error(str(e))
            post_err_msg = True
            raise ValidationError(_('No se pudieron obtener datos de asistencia del dispositivo %s') % (self.display_name,))

        finally:
            if post_err_msg and self.download_error_notification:
                email_template_id = self.env.ref('hr_attendance_device.email_template_error_get_attendance')
                self.post_message(email_template_id)
            self.enableDevice()
            self.disconnect()

    def enableDevice(self):
        """volver a habilitar el dispositivo conectado"""
        try:
            return self.zk.enable_device()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('No se pudo habilitar el dispositivo %s. Aquí está la información de depuración:\n%s')
                                  % (self.display_name, e))

    def disableDevice(self):
        """deshabilite (lock) el dispositivo, asegúrese de que no haya actividad cuando se ejecute el proceso"""
        try:
            return self.zk.disable_device()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("No se pudo desactivar el dispositivo %s. Aquí está la información de depuración:\n%s")
                                  % (self.display_name, e))

    def action_attendance_clear(self):
        """Método para borrar todos los datos de asistencia del dispositivo"""
        for r in self:
            error_msg = ""
            attendance_clear_safe, att = r.is_attendance_clear_safe()
            if attendance_clear_safe:
                r.clearAttendance()
            else:
                error_msg += _("No era seguro borrar los datos de asistencia del dispositivo %s.<br />") % (r.name,)
                error_msg += _("Los siguientes datos de asistencia aún no se han almacenado en Odoo:<br />")
                error_msg += _("user_id: %s<br />timestamp: %s<br />status: %s<br />") % (att.user_id, att.timestamp, att.punch)
                _logger.warning("No era seguro borrar los datos de asistencia del dispositivo %s" % r.name)
                if r.auto_clear_attendance_error_notif:
                    email_template_id = self.env.ref('hr_attendance_device.email_template_not_safe_to_clear_attendance')
                    r.post_message(email_template_id)
            if error_msg and r.debug_message:
                r.message_post(body=error_msg)

    def is_attendance_clear_safe(self):
        """Si los datos de los dispositivos no se han descargado en Odoo, este método devolverá falso"""
        UserAttendance = self.env['user.attendance']
        User = self.env['attendance.device.user']

        check_statuses = self.attendance_device_state_line_ids.mapped('code')

        attendances = self.getAttendance()  # Attendance(user_id, timestamp, status)
        for att in attendances:
            if att.punch not in check_statuses:
                continue
            user = User.with_context(active_test=False).search([('user_id', '=', att.user_id), ('device_id', '=', self.id)], limit=1)
            utc_dt = self.convert_time_to_utc(att.timestamp, self.tz)
            str_utc_dt = fields.Datetime.to_string(utc_dt)
            match = UserAttendance.search([('device_id', '=', self.id),
                                           ('user_id', '=', user.id),
                                           ('status', '=', att.punch),
                                           ('timestamp', '=', str_utc_dt)], limit=1)
            if not match:
                return False, att
        return True, False

    def clearAttendance(self):
        '''borrar todos los registros de asistencia del dispositivo'''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.clear_attendance()
        except Exception:
            raise ValidationError(_('No se pudieron borrar los datos de asistencia del dispositivo %s') % (self.display_name,))
        finally:
            self.enableDevice()
            self.disconnect()

    # DESCARGAR USUARIOS DEL DISPOSITIVO
    def action_user_download(self):
        """Este método descarga y actualiza todos los usuarios de dispositivos en el modelo attendance.device.user"""
        for r in self:
            if r.unique_uid:
                r._download_users_by_uid()
            else:
                r._download_users_by_user_id()

    def _download_users_by_uid(self):
        """Este método descarga y actualiza todos los usuarios de dispositivos en el modelo attendance.device.user usando uid como clave"""
        DeviceUser = self.env['attendance.device.user']
        for r in self:
            error_msg = ""
            # device_users = User(uid, name, privilege, password, group_id, user_id)
            device_users = r.getUser()

            uids = []
            for device_user in device_users:
                uids.append(device_user.uid)

            existing_user_ids = []

            device_user_ids = DeviceUser.with_context(active_test=False).search([('device_id', '=', r.id)])
            for user in device_user_ids.filtered(lambda user: user.uid in uids):
                existing_user_ids.append(user.uid)

            users_not_in_device = device_user_ids.filtered(lambda user: user.uid not in existing_user_ids)
            users_not_in_device.write({'not_in_device': True})

            for device_user in device_users:
                uid = device_user.uid
                vals = {
                    'uid': uid,
                    'name': device_user.name,
                    'privilege': device_user.privilege,
                    'password': device_user.password,
                    'user_id': device_user.user_id,
                    'device_id': r.id,
                    }
                if device_user.group_id.isdigit():
                    vals['group_id'] = device_user.group_id
                if uid not in existing_user_ids:
                    try:
                        DeviceUser.create(vals)
                    except Exception as e:
                        _logger.info(e)
                        _logger.info(vals)
                        error_msg += str(e)
                        error_msg += _("\nDatos que causaron el error: %s") % str(vals)
                else:
                    existing = DeviceUser.with_context(active_test=False).search([('uid', '=', uid), ('device_id', '=', r.id)], limit=1)
                    if existing:
                        update_data = {}
                        if existing.name != vals['name']:
                            update_data['name'] = vals['name']
                        if existing.privilege != vals['privilege']:
                            update_data['privilege'] = vals['privilege']
                        if existing.password != vals['password']:
                            update_data['password'] = vals['password']
                        if 'group_id' in vals and existing.group_id != vals['group_id']:
                            update_data['group_id'] = vals['group_id']
                        if existing.user_id != vals['user_id']:
                            update_data['user_id'] = vals['user_id']
                        if existing.device_id.id != vals['device_id']:
                            update_data['device_id'] = vals['device_id']
                        if bool(update_data):
                            try:
                                existing.write(update_data)
                            except Exception as e:
                                _logger.info(e)
                                _logger.info(vals)
                                error_msg += str(e) + "<br />"
                                error_msg += _("\nDatos que causaron el error: %s") % str(update_data)
            if error_msg and r.debug_message:
                r.message_post(body=error_msg)

    def getUser(self):
        '''devolver una lista Python de usuarios de dispositivos en User(uid, name, privilege, password, group_id, user_id)'''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.get_users()
        except Exception as e:
            _logger.error(str(e))
            raise ValidationError(_('No se pudieron obtener usuarios del dispositivo %s\n'
                                    'Si se había conectado a su dispositivo, quizás su dispositivo tuvo un problema. '
                                    'Algunos dispositivos defectuosos que permiten uid duplicados pueden causar este problema. En tal caso, '
                                    'Si aún desea cargar usuarios desde ese dispositivo defectuoso, desmarque Datos '
                                    'Campo de reconocimiento.\n'
                                    'Aquí está el mensaje de error de depuración.:\n%s') % (self.display_name, str(e)))
        finally:
            self.enableDevice()
            self.disconnect()

    def _download_users_by_user_id(self):
        """Este método descarga y actualiza todos los usuarios de dispositivos en el modelo attendance.device.user usando user_id como clave
        NOTA: This method is experimental as it failed on comparing user_id in unicode type from devices (unicode: string) with user_id in unicode string from Odoo (u'string')"""
        DeviceUser = self.env['attendance.device.user']
        for r in self:
            # device_users = User(uid, name, privilege, password, group_id, user_id)
            device_users = r.getUser()

            user_ids = []
            for device_user in device_users:
                user_ids.append(str(device_user.user_id))

            existing_user_ids = []
            device_user_ids = DeviceUser.with_context(active_test=False).search([('device_id', '=', r.id)])
            for user in device_user_ids.filtered(lambda user: user.user_id in user_ids):
                existing_user_ids.append(str(user.user_id))

            for device_user in device_users:
                user_id = str(device_user.user_id)
                vals = {
                    'uid': device_user.uid,
                    'name': device_user.name,
                    'privilege': device_user.privilege,
                    'password': device_user.password,
                    'user_id': device_user.user_id,
                    'device_id': r.id,
                    }
                if device_user.group_id.isdigit():
                    vals['group_id'] = device_user.group_id
                if user_id not in existing_user_ids:
                    DeviceUser.create(vals)
                else:
                    existing = DeviceUser.with_context(active_test=False).search([
                        ('user_id', '=', user_id),
                        ('device_id', '=', r.id)], limit=1)
                    if existing:
                        existing.write(vals)

    # SUBIR USUARIOS AL DISPOSITIVO
    def action_user_upload(self):
        """
        This method will
        1. Download users from device
        2. Map the users with emloyee
        3. Upload users from model attendance.device.user into the device
        """
        ignored_employees_dict = {}
        for r in self:
            # Then we download and map all employees with users
            r.action_employee_map()
            # Then we create users from unmapped employee
            ignored_employees = []
            for employee in r.unmapped_employee_ids:
                if not employee.barcode:
                    ignored_employees.append(employee)
                    continue
                employee.upload_to_attendance_device(r)
            # we download and map all employees with users again
            r.action_employee_map()

            if len(ignored_employees) > 0:
                ignored_employees_dict[r] = ignored_employees

        if bool(ignored_employees_dict):
            message = _('Los siguientes empleados, que no tienen ningún ID Credencial definido, no se han cargado en el dispositivo correspondiente:\n')
            for device in ignored_employees_dict.keys():
                for employee in ignored_employees_dict[device]:
                    message += device.name + ': ' + employee.name + '\n'

            return {
                'warning': {
                    'title': "Algunos empleados no pudieron ser cargados!",
                    'message': message,
                },
            }

    # MAPEAR EMPLEADOS
    def action_employee_map(self):
        self.action_user_download()

        for r in self:
            for user in r.device_user_ids.filtered(lambda user: not user.employee_id):
                employee = user.smart_find_employee()
                if employee:
                    user.write({
                        'employee_id': employee.id,
                        })
            # upload users that are available in Odoo but not available in device
            for user in r.device_user_ids.filtered(lambda user: user.not_in_device):
                user.setUser()

            # upload users that are available in Odoo but not available in device
            for user in r.device_user_ids.filtered(lambda user: user.not_in_device):
                user.setUser()
                user.write({'not_in_device': False})

            if r.create_employee_during_mapping:
                users = r.device_user_ids.filtered(lambda user: not user.employee_id)
                if users:
                    users.generate_employees()

    def setUser(self, uid=None, name='', privilege=0, password='', group_id='', user_id='', card=0):
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.set_user(uid, name, privilege, password, group_id, user_id, card)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_('No se pudo configurar el usuario en el dispositivo %s. Aquí está la información del usuario:\n'
                                    'uid: %s\n'
                                    'name: %s\n'
                                    'privilege: %s\n'
                                    'password: %s\n'
                                    'group_id: %s\n'
                                    'user_id: %s\n'
                                    'Aquí está la información de depuración:\n%s')
                                  % (self.display_name, uid, name, privilege, password, group_id, user_id, e))
        finally:
            self.enableDevice()
            self.disconnect()

    # DESCARGAR HUELLAS DACTILARES
    def action_finger_template_download(self):
        FingerTemplate = self.env['finger.template']
        for r in self:
            r.action_employee_map()
            device_users = self.env['attendance.device.user'].search([('device_id', '=', r.id)])

            # if there is still no device users, just ignore downloading finger templates
            if not device_users:
                continue

            template_data = r.getFingerTemplate()
            template_datas = []
            for template in template_data:
                template_datas.append(str(template.uid) + '_' + str(template.fid))

            existing_finger_template_ids = []
            finger_template_ids = FingerTemplate.search([('device_id', '=', r.id)])
            for template in finger_template_ids.filtered(lambda tmp: (str(tmp.uid) + '_' + str(tmp.fid)) in template_datas):
                existing_finger_template_ids.append(str(template.uid) + '_' + str(template.fid))

            for template in template_data:
                uid = template.uid
                fid = template.fid
                valid = template.valid
                tmp = template.template
                device_user_id = self.env['attendance.device.user'].search([('uid', '=', uid), ('device_id', '=', r.id)], limit=1)
                device_user_id = device_users.filtered(lambda u: u.uid == uid)
                if not device_user_id:
                    continue
                else:
                    device_user_id = device_user_id[0]
                vals = {
                    'device_user_id': device_user_id.id,
                    'fid': fid,
                    'valid': valid,
                    'template': tmp,
                    }
                if device_user_id.employee_id:
                    vals['employee_id'] = device_user_id.employee_id.id

                if (str(template.uid) + '_' + str(template.fid)) not in existing_finger_template_ids:
                    FingerTemplate.create(vals)
                else:
                    existing = FingerTemplate.search([
                        ('uid', '=', uid),
                        ('fid', '=', fid),
                        ('device_id', '=', r.id),
                        ], limit=1)
                    if existing:
                        existing.write(vals)
        return

    def getFingerTemplate(self):
        '''return a Python List of fingers template in Finger(uid, fid, valid, template)'''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.get_templates()
        except Exception as e:
            _logger.error(str(e))
            raise ValidationError(_('No se pudieron obtener Huellas Dactilares del dispositivo %s\n'
                                    'Si se había conectado a su dispositivo, quizás su dispositivo tuvo un problema. '
                                    'Algunos dispositivos defectuosos que permiten uid duplicados pueden causar este problema. En tal caso, '
                                    'Si aún desea cargar usuarios desde ese dispositivo defectuoso, desmarque el campo '
                                    'Reconocimiento de datos.\n'
                                    'Aquí está el mensaje de error de depuración.:\n%s') % (self.display_name, str(e)))
        finally:
            self.enableDevice()
            self.disconnect()

    # LIMPIAR DATOS
    def action_clear_data(self):
        '''borrar todos los datos (incluye: usuario, informe de asistencia, base de datos de dedos)'''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.clear_data()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('No se pudieron borrar los datos del dispositivo %s. Aquí está la información de depuración:\n%s')
                                  % (self.display_name, e))
        finally:
            self.enableDevice()
            self.disconnect()

    def clearData(self):
        '''clear all data (include: user, attendance report, finger database ) '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.clear_data()
        except Exception:
            raise ValidationError(_('No se pudieron borrar todos los datos del dispositivo %s') % (self.display_name,))
        finally:
            self.enableDevice()
            self.disconnect()

    # REINICIAR DISPOSITIVO
    def action_restart(self):
        self.ensure_one()
        self.restartDevice()

    def restartDevice(self):
        '''reinicia el dispositivo'''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.restart()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('No se pudo obtener el número de serie del dispositivo %s. Aquí está la información de depuración.:\n%s')
                                  % (self.display_name, e))

    # MOSTRAR LA HORA
    def action_show_time(self):
        """Mostrar la hora en la máquina."""
        self.ensure_one()
        raise ValidationError(_("El tiempo de la máquina es %s") % self.getMachineTime())

    def getMachineTime(self):
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_time()
        except Exception as e:
            _logger.error(str(e))
            raise ValidationError(_("No se pudo obtener la hora del dispositivo %s\n"
                                    "Aquí está el mensaje de error de depuración:\n%s") % (self.display_name, str(e)))
        finally:
            self.disconnect()

    # CANCELAR EL DISPOSITIVO
    def set_cancel(self):
        self.state = 'cancelled'

    # VOLVER A BORRADOR
    def set_draft(self):
        self.state = 'draft'

    # VER USUARIOS DEL DISPOSITIVO
    def action_view_users(self):
        action = self.env.ref('hr_attendance_device.device_user_list_action')
        result = action.read()[0]

        # reset context
        result['context'] = {}

        # choose the view_mode accordingly
        if self.device_users_count != 1:
            result['domain'] = "[('id', 'in', %s)]" % self.with_context(active_test=False).device_user_ids.ids
        elif self.device_users_count == 1:
            res = self.env.ref('hr_attendance_device.attendance_device_user_form_view', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.device_user_ids.id
        return result

    # VER EMPLEADOS MAPEADOS DE ODOO
    def action_view_mapped_employees(self):
        action = self.env.ref('hr.open_view_employee_list_my')
        result = action.read()[0]

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        if self.mapped_employees_count != 1:
            result['domain'] = "[('id', 'in', " + str(self.mapped_employee_ids.ids) + ")]"
        elif self.mapped_employees_count == 1:
            res = self.env.ref('hr_attendance_device.view_employee_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.mapped_employee_ids.id
        return result

    # VER HUELLAS DACTILARES
    def action_view_finger_template(self):
        self.ensure_one()
        action = self.env.ref('hr_attendance_device.action_finger_template')
        result = action.read()[0]

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        total_finger_template_records = self.total_finger_template_records
        if total_finger_template_records != 1:
            result['domain'] = "[('device_id', 'in', " + str(self.ids) + ")]"
        elif total_finger_template_records == 1:
            res = self.env.ref('hr_attendance_device.view_finger_template_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.finger_template_ids.id
        return result

    # VER DATA DE ASISTENCIAS
    def action_view_attendance_data(self):
        self.ensure_one()
        action = self.env.ref('hr_attendance_device.action_user_attendance_data')
        result = action.read()[0]

        # reset context
        # result['context'] = {}
        # choose the view_mode accordingly
        total_att_records = self.total_att_records
        if total_att_records != 1:
            result['domain'] = "[('device_id', 'in', " + str(self.ids) + ")]"
        elif total_att_records == 1:
            res = self.env.ref('hr_attendance_device.view_attendance_data_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.user_attendance_ids.id
        return result

    def unlink(self):
        force_delete = self.env.context.get('force_delete', False)
        for r in self:
            if r.state != 'draft':
                raise UserError(_("No puede eliminar el dispositivo '%s' mientras su estado no sea Borrador.")
                                % (r.display_name,))
            if r.device_user_ids and not force_delete:
                raise UserError(_("Es posible que no puedas eliminar el dispositivo '%s' mientras sus datos estén almacenados en Odoo."
                                  " Elimine todos los datos relacionados de este dispositivo antes de eliminarlo de Odoo."
                                  " También puedes considerar desactivar este dispositivo para no tener que eliminarlo"
                                  " it.") % (r.display_name,))
        return super(AttendanceDevice, self).unlink()

    # FUNCIONES DE TO_BASE
    def convert_time_to_utc(self, dt, tz_name=None, is_dst=None, naive=False):
        """
        :param dt: an instance of datetime object to convert to UTC
        :param tz_name: the name of the timezone to convert. In case of no tz_name passed, this method will try to find the timezone in context or the login user record
        :param is_dst: respecting daylight saving time or not

        :return: an instance of datetime object in UTC (with or without timezone notation depending on the given naive value)
        :rtype: datetime
        """
        tz_name = tz_name or self._context.get('tz') or self.env.user.tz
        if not tz_name:
            raise ValidationError(_("La zona horaria local no está definida. Es posible que necesites establecer una zona horaria en las Preferencias de tu usuario."))
        local = pytz.timezone(tz_name)
        local_dt = local.localize(dt, is_dst=is_dst)
        if naive:
            return local_dt.astimezone(pytz.utc).replace(tzinfo=None)
        else:
            return local_dt.astimezone(pytz.utc)

    def convert_utc_time_to_tz(self, utc_dt, tz_name=None, is_dst=None):
        """
        Method to convert UTC time to local time
        :param utc_dt: datetime in UTC
        :param tz_name: the name of the timezone to convert. In case of no tz_name passed, this method will try to find the timezone in context or the login user record
        :param is_dst: respecting daylight saving time or not

        :return: datetime object presents local time
        """
        tz_name = tz_name or self._context.get('tz') or self.env.user.tz
        if not tz_name:
            raise ValidationError(_("La zona horaria local no está definida. Es posible que necesites establecer una zona horaria en las Preferencias de tu usuario."))
        tz = pytz.timezone(tz_name)
        return pytz.utc.localize(utc_dt, is_dst=is_dst).astimezone(tz)

    def time_to_float_hour(self, dt):
        """
        This method will convert a datetime object to a float that present the corresponding time without date. For example,
            datetime.datetime(2019, 3, 24, 12, 44, 0, 307664) will become 12.733418795555554
        :param dt: datetime object
        :param type: datetime

        :return: The extracted time in float. For example, 12.733418795555554 for datetime.time(12, 44, 0, 307664)
        :rtype: float
        """
        return dt.hour + dt.minute / 60.0 + dt.second / (60.0 * 60.0) + dt.microsecond / (60.0 * 60.0 * 1000000.0)

class AttendanceDeviceStateLine(models.Model):
    _name = 'attendance.device.state.line'
    _description = 'Attendance Device State'

    attendance_state_id = fields.Many2one('attendance.state', string='Nombre', required=True, index=True,)
    device_id = fields.Many2one('attendance.device', string='Dispositivo', required=True, ondelete='cascade', index=True, copy=False)
    code = fields.Integer(string='Codigo', related='attendance_state_id.code', store=True, readonly=True)
    type = fields.Selection(related='attendance_state_id.type', string='Tipo de Marcacion', store=True)
    activity_id = fields.Many2one('attendance.activity', string='Tipo de Asistencia', related='attendance_state_id.activity_id',
                                  help='Actividad de asistencia, Ej. Trabajo normal, horas extras, etc.', readonly=True, store=True, index=True)

    _sql_constraints = [
        ('attendance_state_id_device_id_unique',
         'UNIQUE(attendance_state_id, device_id)',
         "El Código debe ser único por Dispositivo"),
    ]

