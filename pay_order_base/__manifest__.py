# -*- encoding: utf-8 -*-
{
	'name': 'Pagos Proveedores TXT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Sebastian LL MIGRACIÓN',
	'depends': ['account_multipayment_advance_it'],
	'version': '1.0',
	'description':"""
	- Menu Pagos Proveedores TXT
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			 'security/ir.model.access.csv',
			 'views/res_bank.xml',
			 'views/res_partner_bank.xml',
			 'views/bank_parameter_it.xml',
			 'views/payment_type_catalog.xml',
			 'views/partner_bank_type_catalog.xml',
			 'views/res_partner.xml',
			 'views/account_journal.xml',
			 'views/multipayment_advance_it.xml',
			 'wizards/make_wizard_order_pay.xml'
			 ],
	'installable': True
}