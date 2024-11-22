# -*- encoding: utf-8 -*-
{
	'name': 'Account Renumber',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_voucher_name'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Modulo para renumerar Asientos Contables
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'wizard/wizard_renumber_view.xml'],
	'installable': True,
	'license': 'LGPL-3'
}
