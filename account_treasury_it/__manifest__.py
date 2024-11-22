# -*- encoding: utf-8 -*-
{
	'name': 'Tesoreria IT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Sebastian Migracion',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	- Tesoreria IT
	""",
    'summary': """- Obligatorio""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
        'views/account_journal_bank_cash.xml',
		#'views/account_batch_payment.xml',
		'views/account_payment.xml',
		'views/account_bank_statement.xml',
		'views/account_treasury_menu.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
