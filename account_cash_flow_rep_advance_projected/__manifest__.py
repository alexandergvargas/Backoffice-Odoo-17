# -*- encoding: utf-8 -*-
{
	'name': 'Reporte Flujo de Caja Proyectado',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_cash_flow_rep_advance','account_reports'],
	'version': '1.0',
	'description':"""
	- Nuevo Reporte para Flujo de Caja Proyectado
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_cash_flow_book_advance_projected.xml',
		'wizard/account_cash_flow_rep_advance_projected.xml'
	],
	'installable': True
}