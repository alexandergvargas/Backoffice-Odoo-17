# -*- encoding: utf-8 -*-
{
	'name': 'Detracciones',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Generar Detracciones en Facturas de Clientes y Proveedores
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'views/account_detractions_wizard.xml',
			'views/account_move.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
