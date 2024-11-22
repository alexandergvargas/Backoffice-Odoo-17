# -*- encoding: utf-8 -*-
{
	'name': 'Reportes DESTINOS',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_consistencia_rep_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para CONSISTENCIA DE DESTINOS, DETALLE DESTINOS, RESUMEN DESTINOS, GENERAR ASIENTOS
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_destinos_rep.xml',
		'views/account_des_detail_book.xml',
		'views/account_des_consistency_book.xml',
		'views/account_des_summary_book.xml',
		'views/account_des_generate_book.xml',
		'views/account_move.xml',
		'views/account_des_move.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
