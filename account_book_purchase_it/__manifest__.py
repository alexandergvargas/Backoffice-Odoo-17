# -*- encoding: utf-8 -*-
{
	'name': 'Reporte REGISTRO DE COMPRAS',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
    'auto_install': True,
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para REGISTRO DE COMPRAS
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_book_purchase_wizard.xml',
		'views/account_book_purchase_view.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
