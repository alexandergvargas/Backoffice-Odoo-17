# -*- coding: utf-8 -*-
{
    'name': 'Hr Import Vacations Rest',
    'category': 'Generic Modules/Human Resources',
    'author': 'ITGRUPO-HR',
    'depends': ['hr_vacations'],
    'version': '1.0',
    'description': """
        Modulo para importar saldos iniciales de descansos vacacionales
     """,
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'data/attachment_sample.xml',
        'views/hr_vacation_rest_import_view.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
