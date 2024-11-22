# -*- encoding: utf-8 -*-
{
	'name': 'Generacion de Secuencias para Diarios',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, SEBASTIAN MIGRACION',
	'depends': ['account_fields_it','account_voucher_name','account_menu_other_configurations'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Generacion de Secuencias para Diarios
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'views/account_journal.xml',
			'wizards/account_sequence_journal_wizard.xml'
			#'wizards/sequence_wizard.xml'
			],
	'installable': True,
	'license': 'LGPL-3'
}
