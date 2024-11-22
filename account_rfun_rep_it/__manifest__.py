# -*- encoding: utf-8 -*-
{
	'name': 'Reporte RESULTADO POR FUNCION',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Reporte Resultado por Funcion
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'wizards/function_result_wizard.xml'
			],
	'installable': True,
	'license': 'LGPL-3'
}