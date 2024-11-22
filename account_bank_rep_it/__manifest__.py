# -*- encoding: utf-8 -*-
{
	'name': 'Reporte AUXILIAR DE BANCOS',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it','account_treasury_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para AUXILIAR DE BANCOS
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_bank_rep.xml',
		'views/account_bank_book.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
