# -*- encoding: utf-8 -*-
{
	'name': 'Reporte ANEXOS',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Reporte ANEXOS
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'SQL.sql',
		'security/ir.model.access.csv',
		'wizards/account_anexo_wizard.xml'],
	'installable': True,
	'license': 'LGPL-3'
}
