# -*- encoding: utf-8 -*-
{
	'name': 'Verificacion SUNAT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Migracion Sebastian Moises Loraico Lopez',
	'depends': ['account_fields_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Verificacion SUNAT
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_move.xml',
		'views/account_main_parameter.xml',
        'views/account_query_sunat.xml'
		],
	'installable': True
}
