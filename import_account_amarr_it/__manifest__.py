# -*- encoding: utf-8 -*-
{
	'name': 'Importar Plan Contable',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_destinos_rep_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Importar Plan Contable
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'security/ir.model.access.csv',
		'wizard/import_account_amarr_wizard.xml',
	],
	'installable': True,
	'license': 'LGPL-3'
}
