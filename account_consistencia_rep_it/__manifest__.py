# -*- encoding: utf-8 -*-
{
	'name': 'Reportes CONSISTENCIAS',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para :
        - CONSISTENCIA FLUJO EFECTIVO
        - ASIENTOS DESCUADRADOS
        - FACTURAS DE CLIENTES PDTES DE CONCILIAR
        - FACTURAS DE PROVEEDOR PDTES DE CONCILIAR
        - FACTURAS CON TC DIFERENTE
        - DIFERENCIAS DE CAMBIO NO EJECUTADAS
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/menu_items.xml',
		'views/account_con_efective_book.xml',
		'views/unbalanced_accounting_entries_view.xml',
		'views/invoices_pending_reconciliation_view.xml',
		'views/invoices_with_different_rate_view.xml',
		'views/account_exchange_document_currency_view.xml',
		'wizards/account_con_efective_rep.xml',
		'wizards/unbalanced_accounting_entries_wizard.xml',
		'wizards/customer_invoices_pending_reconciliation_wizard.xml',
		'wizards/supplier_invoices_pending_reconciliation_wizard.xml',
		'wizards/invoices_with_different_rate_wizard.xml',
		'wizards/account_exchange_document_currency_wizard.xml',
	],
	'installable': True,
	'license': 'LGPL-3'
}
