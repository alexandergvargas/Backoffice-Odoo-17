# -*- encoding: utf-8 -*-
{
	'name': 'Diferencia Analitica VS Contabilidad',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_destinos_rep_it','report_tools'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Exportacion de Diferencia Analitica VS Contabilidad
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/account_diff_destino_analitica_view.xml',
		'wizards/account_diff_destino_analitica_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
