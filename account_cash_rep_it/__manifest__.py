# -*- encoding: utf-8 -*-
{
	'name': 'Reporte LIBRO CAJA Y BANCOS',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it','account_treasury_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para LIBRO CAJA Y BANCOS
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_cash_rep.xml',
		'views/account_cash_book.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
