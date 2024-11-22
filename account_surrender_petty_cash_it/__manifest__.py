# -*- encoding: utf-8 -*-
{
	'name': 'Rendiciones/Caja Chica IT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_treasury_it','account_type_operation','account_multipayment_advance_it'],
	'version': '1.0',
	'description':"""
	- Rendiciones 2.0
    - Caja Chica 2.0
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/attachment_sample.xml',
		'views/product_product.xml',
		'views/account_journal.xml',
		'views/render_main_parameter.xml',
		'views/account_surrender_petty_cash_it.xml',
		'views/hr_employee.xml',
		'views/menu_views.xml',
        'wizard/post_surrender_petty_cash_wizard.xml',
        'wizard/import_surrender_line_wizard.xml',
        'wizard/import_surrender_invoice_line_wizard.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}