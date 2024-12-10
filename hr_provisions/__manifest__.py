# -*- encoding: utf-8 -*-
{
	'name': 'Hr Provisions',
	'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_social_benefits','hr_payslip_run_move'],
	'version': '1.0',
	'description':"""
		Modulo para generar la Provision de beneficios sociales	
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/hr_main_parameter.xml',
		'views/hr_provisions.xml',
		'wizard/hr_provisions_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3',
}
