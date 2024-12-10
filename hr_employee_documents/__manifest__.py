# -*- coding: utf-8 -*-
{
    'name': 'Hr Employee Documents',
    'category': 'Generic Modules/Human Resources',
    'author': 'ITGRUPO-HR',
    'depends': ['hr','hr_contract','hr_fields'],
    'version': '17.0.1.0.0',
    'summary': """Gestiona documentos de empleados con notificaciones de vencimiento.""",
    'description': """Este módulo administra documentos relacionados con los empleados con notificaciones de vencimiento. 
                    Los documentos de los empleados con la información necesaria deben guardarse y usarse en consecuencia. 
                    Este módulo ayuda a almacenar y administrar los documentos relacionados con los empleados, como certificados, 
                    informes de tasación, pasaporte, licencia, etc.""",
    'data': [
        'data/ir_cron_data.xml',
        'security/ir.model.access.csv',
        'data/hr_document_type.xml',
        'views/hr_document_type_views.xml',
        'views/hr_employee_document_views.xml',
        'views/hr_employee.xml',
        'views/hr_contract.xml',
        'views/hr_salary_history_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
