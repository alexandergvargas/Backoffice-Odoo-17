# -*- encoding: utf-8 -*-
{
	'name': 'Cuentas Corrientes It',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_journal_period_close'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Sub-menu para cuentas corrientes
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/attachment_sample.xml',
		'views/menu_items.xml',
		'views/account_cta_cte.xml',
		'wizards/account_cta_cte_report_wizard.xml',
		'wizards/import_cta_cte_line_wizard.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
