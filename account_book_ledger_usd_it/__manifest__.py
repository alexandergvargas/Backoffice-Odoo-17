# -*- encoding: utf-8 -*-
{
	'name': 'Reporte LIBRO MAYOR USD',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_book_ledger_it','l10n_pe_currency_rate'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para LIBRO MAYOR USD
	""",
    'summary': """- Obligatorio""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'SQL.sql',
		'wizards/account_book_ledger_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
