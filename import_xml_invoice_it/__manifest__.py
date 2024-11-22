# -*- encoding: utf-8 -*-
{
	'name': 'Import XML Invoice',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_move_autofill','account_base_import_it','account_constraint_invoices_it','bi_manual_currency_exchange_rate_invoice_payment'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Modulo para importar Facturas desde XML
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
        'security/security.xml',
		'security/ir.model.access.csv',
		'views/import_xml_invoice_it.xml',
		'views/account_tax.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}