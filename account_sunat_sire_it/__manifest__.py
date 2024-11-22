# -*- encoding: utf-8 -*-
{
	'name': 'ACCOUNT SUNAT SIRE',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua - moises',
	'depends': ['account_sunat_it','popup_it','account_report_menu_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- ACCOUNT SUNAT SIRE
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
        'SQL.sql',
        'security/security.xml',
        'security/ir.model.access.csv',
		'views/account_main_parameter.xml',
		'views/account_sunat_sire_sale_data.xml',
		'wizards/account_sunat_rep.xml'
	],
	'installable': True,
	'license': 'LGPL-3'

}