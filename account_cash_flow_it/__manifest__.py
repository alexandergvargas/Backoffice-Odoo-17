# -*- encoding: utf-8 -*-
{
	'name': 'Reporte Flujo de Caja Oficial',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_cash_flow_rep'],
	'version': '1.0',
	'description':"""
	- Nuevo Reporte para Flujo de Caja
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizard/account_cash_flow_wizard.xml'
	],
	'installable': True
}