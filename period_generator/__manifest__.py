# -*- encoding: utf-8 -*-
{
	'name': 'Period Generator',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account','account_base_it','account_menu_other_configurations'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Generador de Periodos Automatico en base a un Año Fiscal
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizard/wizard_period_generator.xml',
		'views/account_fiscal_year.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
