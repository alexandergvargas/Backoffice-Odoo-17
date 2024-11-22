# -*- encoding: utf-8 -*-
{
	'name': 'Reporte REGISTRO DE COMPRAS USD',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_book_purchase_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para REGISTRO DE COMPRAS USD
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
        'SQL.sql',
		'wizards/account_book_purchase_wizard.xml',
		'views/account_book_purchase_view.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
