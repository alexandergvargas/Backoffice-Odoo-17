# -*- encoding: utf-8 -*-
{
	'name': 'Importador de Lineas de Extractos Bancarios',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Sebastian Moises Loraico Lopez',
	'depends': ['account_fields_it','account_online_synchronization'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Modulo para importar Lineas de Extractos Bancarios
    - funcionalidad de js
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'security/ir.model.access.csv',
        'wizard/import_statement_line_wizard.xml',
		],
	'installable': True,
    'assets': {
        'web.assets_backend': [
            'account_bank_statement_import_it/static/src/components/**/*',
        ]
    }
}
