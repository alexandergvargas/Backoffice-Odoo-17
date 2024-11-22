# -*- encoding: utf-8 -*-
{
	'name': 'Vista Lista Facturas',
    'summary': """- Obligatorio""",
	'description': 'oculta campos de account',
	'author': 'ITGRUPO, Glenda Julia Merma Mayhua',
	'license': 'LGPL-3',
	'category': 'Accounting',
	'depends': ['account_fields_it'],
	'data': [
		'views/account_move.xml'
	],
	
	'auto_install': True,
	'application': False,
	
}