# -*- coding: utf-8 -*-
{
    'name' : 'Hr Attendance Payslip',
    'category': 'Generic Modules/Human Resources',
    'author': 'ITGRUPO-HR',
    'depends' : ['hr_attendance','hr_assistance_planning','hr_leave'],
    'version': '1.0',
    'description':"""
        Modulo que permite integrar el registro de asistencias con la nomina del trabajador
        """,
    'auto_install': False,
    'demo': [],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_tareaje_manager.xml',
        'views/hr_contract.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}