# -*- encoding: utf-8 -*-
{
	'name': 'Reporte PLE SUNAT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Moises L',
	'depends': ['account_base_sunat_it','popup_it','report_tools','account_financial_situation_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		- Nuevo menu SUNAT para generar PLEs
	""",
	'auto_install': True,
	'demo': [],
	"data": [
        "security/ir.model.access.csv",
        "SQL.sql",
        "wizards/account_sunat_wizard.xml",
        "wizards/popup_it_balance_inventory.xml",
        "wizards/account_sunat_balance_inventory_rep.xml",
        "views/account_sunat_table_ri_views.xml",
        "views/account_sunat_table_cp_views.xml",
        "views/account_sunat_table_mi_views.xml",
        "views/menuitem.xml",
    ],
	'installable': True,
	'license': 'LGPL-3'
}