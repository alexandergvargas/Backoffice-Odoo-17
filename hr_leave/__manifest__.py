# -*- encoding: utf-8 -*-
{
	'name': 'Hr Ausencias',
	'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields','hr_vacations','hr_social_benefits','hr_payroll_holidays'],
	'version': '1.0',
	'description':"""
		Modulo para registro de asuencias/vacaciones
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/hr_leave_type_data.xml',
		'views/hr_main_parameter.xml',
		'views/hr_leave_type.xml',
		'views/hr_leave.xml',
		'views/hr_vacation.xml',
	],
	'installable': True,
	'license': 'LGPL-3',
}