# -*- encoding: utf-8 -*-
{
	'name': 'Eliminar de Asientos de Reversion para Tipo de Cambio',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_it','popup_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		- Eliminar de Asientos de Reversion para Tipo de Cambio
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizard/delete_reversed_move.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}