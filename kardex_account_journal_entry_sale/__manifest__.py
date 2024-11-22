# -*- encoding: utf-8 -*-
{
	'name': 'Detalle de Analisis CV',
	'category': 'stock',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['kardex_account_journal_entry_advance'],
	'version': '1.0',
	'description':"""
	- Detalle de Movimientos en Costos de Ventas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/account_main_parameter.xml',
		'views/costs_sales_analysis_book.xml',
		'wizards/costs_sales_analysis_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
