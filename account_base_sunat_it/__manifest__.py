# -*- encoding: utf-8 -*-
{
	'name': 'Base PLE SUNAT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it','l10n_pe_currency_rate'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		- Nuevo menu SUNAT para generar PLEs
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'SQL.sql',
		'views/account_type_it.xml',
		'views/account_main_parameter.xml',
		'views/account_sunat_menu.xml',
		'views/sunat_table_data.xml',
        'views/account_sunat_checking_balance.xml',
        'views/account_sunat_shareholding.xml',
        'views/account_sunat_capital.xml',
        'views/account_sunat_state_patrimony.xml',
        'views/account_sunat_integrated_results.xml',
        'views/account_sunat_efective_flow.xml',
		'views/account_register_values_it.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}