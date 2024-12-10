# -*- encoding: utf-8 -*-
{
	'name': 'Hr Subsidios Maternidad y Enfermedad',
	'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields','hr_social_benefits','hr_leave'],
	'version': '1.0',
	'description':"""
		Modulo para Calculo de Subsidios de maternidad y enfermedad
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/hr_subsidies.xml',
		'views/hr_main_parameter.xml',
		'views/hr_payslip_run.xml',
		'views/hr_payslip.xml',
		'wizard/report_subsidios.xml',
	],
	'installable': True,
	'license': 'LGPL-3',
}
