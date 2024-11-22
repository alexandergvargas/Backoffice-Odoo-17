# -*- encoding: utf-8 -*-
{
	'name': 'Reporte LIBRO HONORARIOS USD',
	'category': 'Accounting',
	'author': 'ITGRUPO,Sebastian Moises Loraico Lopez',
	'depends': ['account_book_honorary_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para LIBRO HONORARIOS USD
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
        'SQL.sql',	
		'wizards/account_book_honorary_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
