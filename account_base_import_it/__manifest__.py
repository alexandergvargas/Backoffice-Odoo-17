# -*- encoding: utf-8 -*-
{
	'name': 'Menu Importadores',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','contacts'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		- Menu Importadores
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/security.xml',
		'views/account_import_menu.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}