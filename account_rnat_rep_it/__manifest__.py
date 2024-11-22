# -*- encoding: utf-8 -*-
{
	'name': 'Reporte RESULTADO POR NATURALEZA',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Reporte Resultado por Naturaleza
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'wizards/nature_result_wizard.xml'
			],
	'installable': True,
	'license': 'LGPL-3'
}