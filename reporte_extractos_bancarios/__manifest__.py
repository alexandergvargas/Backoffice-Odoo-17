# -*- encoding: utf-8 -*-
{
	'name': 'Reporte extractos bancarios',
	'category': 'Accounting',
	'author': 'ITGRUPO,Sebastian Moises Loraico Lopez',
	'depends': ['account_treasury_it','account_fields_it','popup_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	
    Reporte extractos bancarios
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
        'security/ir.model.access.csv',
		'wizard/report_extracto_bancarios.xml',
        'views/account_statement_view.xml',
        'report/account_statement_view_report.xml'
        ],
	'installable': True,
	'license': 'LGPL-3'
}
