# -*- coding: utf-8 -*-
{
    'name': "Hr Biometric Attendance Device",
    'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
    'summary': """Integra todo tipo de dispositivos de asistencia basados en ZKTeco con Odoo""",
    'description': """
Características Clave
=====================

* Admite UDP y TCP para datos de asistencia grandes (probado con una máquina real que almacena más de 20 mil registros de asistencia)
* Admite conexión con nombre de dominio o IP
* Autenticar dispositivos con contraseña.
* Múltiples dispositivos para múltiples ubicaciones
* Múltiples zonas horarias del dispositivo en múltiples ubicaciones
* Compatibilidad con múltiples estados de asistencia (por ejemplo, registro de entrada, salida, inicio de horas extra, finalización de horas extra, etc.)
* Almacene plantillas de huellas digitales en los perfiles de los empleados para configurar rápidamente un nuevo dispositivo
* Eliminar usuarios del dispositivo de Odoo
* Cargue nuevos usuarios en los dispositivos desde la base de datos de empleados de Odoo
* Usuarios de dispositivos de mapeo automático con base de empleados de Odoo en el mapeo de ID de insignia, o mapeo de búsqueda de nombre si no se encontró ninguna coincidencia de ID de insignia
* Almacene los datos de asistencia del dispositivo de forma permanente
* Descarga manual/automática de datos de asistencia desde todos tus dispositivos a Odoo (usando acciones programadas)
* Sincroniza manual/automáticamente los datos de asistencia del dispositivo con HR Attendance para que pueda acceder a ellos en sus reglas salariales para el cálculo de recibos de nómina
* Borre automáticamente los datos de asistencia del dispositivo periódicamente, lo cual es configurable.
* Diseñado para funcionar con todos los dispositivos de asistencia basados en la plataforma ZKTeco.

  * Totalmente PROBADO con los siguientes dispositivos:

    * ZKTeco UA760/ID
    * ZKTeco MB460/ID
    * ZKTeco MB20-VL-ID

  * Los clientes informaron que el módulo ha funcionado muy bien con los siguientes dispositivos
    
    * RONALD JACK B3-C
    * ZKTeco K50
    * ZKTeco MA300
    * ZKTeco U580
    * ZKTeco T4C
    * ZKTeco G3
    * RONALD JACK iClock260
    * ZKTeco K40
    * ZKTeco U580
    * iFace402/ID
    * ZKTeco MB20
    * ZKteco IN0A-1
    * Uface 800

Crédito
======
Muchas gracias a fananimi por su biblioteca pyzk @ https://github.com/fananimi/pyzk

Nos inspiramos en eso y lo personalizamos para obtener más funciones (información del dispositivo, compatibilidad con Python 3,
Soporte TCP/IP, etc.) luego lo integramos en Odoo mediante esta excelente aplicación de dispositivo de asistencia
    """,

    'version': '1.1.2',
    'depends': ['hr_attendance','hr_assistance_planning'],
    'data': [
        'data/scheduler_data.xml',
        'data/attendance_state_data.xml',
        'data/mail_template_data.xml',
        'security/module_security.xml',
        'security/ir.model.access.csv',
        'views/menu_view.xml',
        'views/attendance_device_views.xml',
        'views/attendance_state_views.xml',
        'views/device_user_views.xml',
        'views/hr_attendance_views.xml',
        'views/hr_employee_views.xml',
        'views/user_attendance_views.xml',
        'views/attendance_activity_views.xml',
        'views/finger_template_views.xml',
        'wizard/attendance_wizard.xml',
        'wizard/employee_upload_wizard.xml',
    ],
    'images' : ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
