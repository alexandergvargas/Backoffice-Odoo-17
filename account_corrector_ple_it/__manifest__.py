# -- encoding: utf-8 --
{
	'name': 'CORRECTOR PLE IT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_sunat_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Corrector de PLE de Compras y PLE de Ventas
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/account_ple_purchase_book.xml',
		'views/account_ple_sale_book.xml',
		'wizard/account_ple_purchase_wizard.xml',
		'wizard/account_ple_sale_wizard.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
} 
