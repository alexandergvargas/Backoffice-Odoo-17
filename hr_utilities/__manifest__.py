# -*- encoding: utf-8 -*-
{
	'name': 'Hr Utilities',
	'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields'],
	'version': '1.0',
	'description':"""
		Modulo para calculo de Utilidades
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/security.xml',
			 'security/ir.model.access.csv',
			 'views/hr_utilities.xml',
			 'views/hr_main_parameter.xml'
			],
	'installable': True,
	'license': 'LGPL-3',
}
