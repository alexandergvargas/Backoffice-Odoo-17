# -*- encoding: utf-8 -*-
{
	'name': 'Reporte LIBRO DIARIO',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para LIBRO DIARIO
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_book_diary_wizard.xml',
		'views/account_book_diary_view.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
