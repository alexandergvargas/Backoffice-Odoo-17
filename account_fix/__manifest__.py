# -*- encoding: utf-8 -*-
{
	'name': 'Account Fix',
	'description': 'oculta campos de account',
	'author': 'ITGRUPO, Glenda Julia Merma Mayhua, Sebastian LL',
	'license': 'LGPL-3',
	'category': 'Accounting',
    'summary': """- Obligatorio""",
	'depends': ['account_reports','account_asset','account_fields_it'],
	'data': [
		'views/view.xml'
	],
	
	'auto_install': True,
	'application': False,
	
}