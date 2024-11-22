# -*- encoding: utf-8 -*-
{
	'name': 'Reporte PATRIMONIO NETO',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Reporte de Patrimonio Neto
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'views/account_patrimony_book.xml',
			'wizards/net_patrimony_wizard.xml'
			],
	'installable': True,
	'license': 'LGPL-3'
}