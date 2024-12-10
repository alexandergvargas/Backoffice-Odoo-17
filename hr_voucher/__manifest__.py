# -*- encoding: utf-8 -*-
{
	'name': 'Hr Voucher',
	'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields','hr_vacations'],
	'version': '1.0',
	'description':"""
		Modulo para Generar Boletas de pago en Nominas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		# 'data/template_boleta_email.xml',
		'views/hr_main_parameter.xml',
		'views/hr_payslip.xml',
		'views/hr_payslip_run.xml',
		'controllers/confirm_email.xml',
	],
	'installable': True,
	'license': 'LGPL-3',
}
