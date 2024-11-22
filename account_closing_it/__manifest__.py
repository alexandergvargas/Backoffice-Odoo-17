# -*- encoding: utf-8 -*-
{
	'name': 'Cierre Contable It',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, SEBASTIAN MIGRACION',
	'depends': ['account_fields_it'],
    'summary': """- Obligatorio""",
	'version': '1.0',
	'description':"""
	Sub-menu para creacion de Cierres Contables
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_closing_it.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
