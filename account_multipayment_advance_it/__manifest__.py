# -*- encoding: utf-8 -*-
{
	'name': 'Account Multipayment IT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_treasury_it'],
	'version': '1.0',
	'summary': """- Obligatorio""",
	'description':"""
	- Modulo para permitir el multipago de facturas
    - AGREGANDO RESTRICCION ASIENTOS QUE SOLO SE ELIMINE DESDE PM (SEBASTIAN MOISES LORAICO LOPEZ)
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/attachment_sample.xml',
		'views/account_template_multipayment.xml',
		'views/multipayment_advance_it.xml',
		'views/account_move_line.xml',
		'wizard/get_invoices_multipayment_wizard.xml',
		'wizard/get_template_multipayment_wizard.xml',
		'wizard/import_multipayment_invoice_line_wizard.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
