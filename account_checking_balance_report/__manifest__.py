# -*- encoding: utf-8 -*-
{
	'name': 'Reporte BALANCE DE COMPROBACION',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Reporte BALANCE DE COMPROBACION
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/checking_balance.xml',
		'views/checking_register.xml',
		'wizards/checking_balance_wizard.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
