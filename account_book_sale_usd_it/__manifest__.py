# -*- encoding: utf-8 -*-
{
	'name': 'Reporte REGISTRO DE VENTAS USD',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_book_sale_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para REGISTRO DE VENTAS USD
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
        'SQL.sql',
		'wizards/account_book_sale_wizard.xml',
		'views/account_book_sale_view.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
