# -*- coding: utf-8 -*-
{
    'name' : 'Hr Contratos Personalizados',
    'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
    'depends': ['hr','hr_fields'],
    'version': '1.0',
    'description':"""
        Módulo para la impresión de modelos de contratos de empleados
    """,
    'auto_install': False,
    'data': [
        'data/hr_contract_type_data.xml',
        'views/hr_contract.xml',
        'views/hr_contract_history.xml',
        'report/contract_employee.xml',
    ],
    'installable': True,
	'license': 'LGPL-3',
}
