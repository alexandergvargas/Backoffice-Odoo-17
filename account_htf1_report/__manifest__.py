# -*- encoding: utf-8 -*-
{
	'name': 'Reporte HOJA DE TRABAJO F1',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'summary': """- Obligatorio""",
	'description':"""
	Reporte HOJA DE TRABAJO F1
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/f1_balance.xml',
		'views/f1_register.xml',
		'wizards/worksheet_f1_wizard.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
