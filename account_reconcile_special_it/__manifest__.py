# -*- encoding: utf-8 -*-
{
	'name': 'Account Reconcile Special',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','compute_payments_widget_to_reconcile_info'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Conciliaciones y Reconciliaciones especiales
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'views/account_move.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}