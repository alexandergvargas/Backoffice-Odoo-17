# -*- encoding: utf-8 -*-
{
	'name': 'Account Not Filter in Invoices',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account','account_fields_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- No filtra Rectificativas en Facturas
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'views/account_move.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
