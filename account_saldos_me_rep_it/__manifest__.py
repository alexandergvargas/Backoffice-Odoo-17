# -*- encoding: utf-8 -*-
{
	'name': 'Reporte Saldos Moneda Extranjera',
	'category': 'account',
	'author': 'ITGRUPO, Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Generar Reportes para Saldos Moneda Extranjera
        
        - SEBASTIAN MIGRACION
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_saldos_me_rep.xml',
		'views/account_saldos_me_book.xml',
		'SQL.sql'
	],
	'installable': True
}
