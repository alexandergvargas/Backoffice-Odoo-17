# -*- encoding: utf-8 -*-
{
	'name': 'Nombre Asiento/Factura Contable',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	- Nombre Asiento/Factura Contable
	""",
    'summary': """- Obligatorio""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_journal_sequence.xml',
		'views/account_move.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
