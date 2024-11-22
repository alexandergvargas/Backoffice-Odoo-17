# -*- encoding: utf-8 -*-
{
	'name': 'Importar Rec x Hon de TXT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_base_import_it','bi_manual_currency_exchange_rate_invoice_payment'],
	'version': '1.0',
	'summary': """- Obligatorio""",
	'description':"""
	Importar Rec x Hon de TXT
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
        'security/security.xml',
		'security/ir.model.access.csv',
		'views/import_recxhon_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}