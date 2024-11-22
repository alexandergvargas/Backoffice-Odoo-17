# -*- encoding: utf-8 -*-
{
	'name': 'Cuenta predeterminada por pagar y por cobrar',
	'category': 'Accounting',
	'author': 'ITGRUPO,Moises Loraico Lopez',
	'depends': ['account_base_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		- agrega cuenta personalizada por pagar y por cobrar
	""",
	'auto_install': True,
	'demo': [],
	'data':	[              
		'views/res_config_settings_views.xml',		
	],
	'installable': True,
	'license': 'LGPL-3'
}