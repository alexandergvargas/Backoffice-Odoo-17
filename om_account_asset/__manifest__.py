# -*- encoding: utf-8 -*-
{
	'name': 'Activos Fijos',
	'category': 'Accounting',
	'author': 'Odoo Mates, Odoo SA, ITGRUPO,Glenda Julia Merma Mayhua, SEBASTIAN MIGRACION',
	'depends': ['account','account_fields_it','popup_it','report_tools'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Modulo de Activos Fijos.
    - Menu Principal
    - Reporte Activos Fijos
	""",
	'auto_install': True,
	'demo': [],
	'data':	['security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        #'wizard/asset_modify_views.xml',
        'views/account_asset_views.xml',
        'views/account_invoice_views.xml',
        #'views/account_asset_templates.xml',
        'views/product_views.xml',
        'views/account_asset_book.xml',
        'views/account_asset_71_book.xml',
        'views/account_asset_74_book.xml',
        'views/account_asset_category.xml',
        'report/account_asset_report_views.xml',
        'data/account_asset_data.xml',
        'wizard/asset_depreciation_confirmation_wizard_views.xml',
        'wizard/account_asset_rep.xml',
        'wizard/account_asset_71_rep.xml',
        'wizard/account_asset_73_rep.xml',
        'wizard/account_asset_74_rep.xml',       
        'wizard/asset_unsubscribe_wizard.xml',       
        'activos.sql'],
    'qweb': [
        #"static/src/xml/account_asset_template.xml",
    ],
	'installable': True,
	'license': 'LGPL-3'
}
