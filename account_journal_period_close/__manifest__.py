# -*- encoding: utf-8 -*-
{
	'name': 'Cierre de Periodo',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Sub-menu con Tabla de Cierre de Periodo
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_journal_period.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
