# -*- encoding: utf-8 -*-
{
	'name': 'Retenciones en pagos multiples para Proveedores',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Sebastian Migración',
	'depends': ['account_voucher_name','account_multipayment_advance_it','query_ruc_dni','account_treasury_it'],
	'version': '1.0',
	'description':"""
	Aplicacion de Retenciones en pagos multiples para Proveedores
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		#'views/menu_items.xml',
		'views/account_main_parameter.xml',
		#'views/account_move.xml',
		'views/account_retention_comp.xml',
		'views/account_retention_supplier_book.xml',
		'views/multipayment_advance_it.xml',
		'views/multipayment_advance_it_line.xml',
		'wizard/get_account_multipayment_line_wizard.xml',
		'wizard/account_report_retention_wizard.xml',
		'wizard/account_report_retention_txt_wizard.xml'
		],
	'installable': True
}
