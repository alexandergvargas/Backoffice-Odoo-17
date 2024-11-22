# -*- encoding: utf-8 -*-
{
	'name': 'Leasing IT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_treasury_it'],
	'version': '1.0',
	'description':"""
	Sub-menu para parámetros de Leasing
	Sub-menu para creacion de Leasing
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/attachment_sample.xml',
		'views/leasing_main_paramater.xml',
		'views/account_leasing_it.xml',
		'wizards/account_leasing_invoice_wizard.xml',
		'wizards/import_leasing_line_wizard.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
