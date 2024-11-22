# -*- encoding: utf-8 -*-
{
	'name': 'Reporte Detallado de Estados Financieros',
	'version': '1.0',
	'description': 'Reporte detallado de Estados Financieros',
	'author': 'ITGRUPO, Sebastian Loraico Lopez',
	'license': 'LGPL-3',
	'category': 'Accounting',
    'summary': """- Obligatorio""",
	'depends': [
		'account_report_menu_it'
	],
	"data": [
        "security/ir.model.access.csv",
        "wizard/detailed_financial_statements_wizard.xml",
        "views/detailed_financial_statements_screen_views.xml"
    ],
	
	'auto_install': True,
	'application': False,
}