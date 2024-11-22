# -*- encoding: utf-8 -*-
{
	'name': 'Reporte SITUACION FINANCIERA',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Reporte Situacion Financiera
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'wizards/financial_situation_wizard.xml'
			],
	'installable': True,
	'license': 'LGPL-3'
}