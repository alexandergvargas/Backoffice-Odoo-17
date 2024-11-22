# -*- encoding: utf-8 -*-
{
	'name': 'Importador de Apuntes Contables',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, SEBASTIAN MIGRACION',
	'depends': ['account_fields_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Modulo para importar Apuntes Contables
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'data/attachment_sample.xml',
		'views/account_move.xml',
        'wizard/import_move_line_wizard.xml',
		],
	'installable': True,
	'license': 'LGPL-3'
}
