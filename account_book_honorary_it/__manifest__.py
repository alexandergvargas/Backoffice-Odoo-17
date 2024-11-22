# -*- encoding: utf-8 -*-
{
	'name': 'Reporte LIBRO HONORARIOS',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para LIBRO HONORARIOS
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_book_honorary_wizard.xml',
		'views/account_book_honorary_view.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
