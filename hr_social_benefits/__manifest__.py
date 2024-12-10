# -*- encoding: utf-8 -*-
{
	'name': 'Hr Social Benefits',
	'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields'],
	'version': '1.0',
	'description':"""
		Modulo para gestion y calculo de Beneficios Sociales
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/attachment_sample.xml',
		'views/hr_employee.xml',
		'views/hr_gratification.xml',
		'views/hr_cts.xml',
		'views/hr_liquidation.xml',
		'views/hr_menus.xml',
		'views/hr_main_parameter.xml',
		'controllers/confirm_email.xml',
		'wizard/import_template_bbss.xml',
	],
	'installable': True,
	'license': 'LGPL-3',
}
