# -*- encoding: utf-8 -*-
{
	'name': 'Apertura Contable It',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, SEBASTIAN MIGRACION',
	'depends': ['account_fields_it','account_report_menu_it','account_reconcile_special_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Sub-menu para creacion de Aperturas Contables
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_opening_it.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
