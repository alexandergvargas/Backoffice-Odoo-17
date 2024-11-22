# -*- encoding: utf-8 -*-
{
	'name': 'Reporte LIBRO DIARIO USD',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_book_diary_it','l10n_pe_currency_rate'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para LIBRO DIARIO USD
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'SQL.sql',
		'views/account_book_diary_view.xml',
		'wizards/account_book_diary_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
