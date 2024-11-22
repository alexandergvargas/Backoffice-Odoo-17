# -*- encoding: utf-8 -*-
{
	'name': 'Diferencia Destinos VS Hoja de Trabajo',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_destinos_rep_it','account_htf1_report','account_consistencia_rep_it'],
	'version': '1.0',
	'description':"""
	- Exportacion de Diferencia Destinos VS Hoja de Trabajo
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_destino_ht_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
