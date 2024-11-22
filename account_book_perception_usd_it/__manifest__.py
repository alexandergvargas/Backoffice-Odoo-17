# -*- encoding: utf-8 -*-
{
	'name': 'Reporte PERCEPCIONES USD',
	'category': 'Accounting',
	'author': 'ITGRUPO,Sebastian Loraico Lopez',
	'depends': ['account_book_perception_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para PERCEPCIONES USD
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
        'SQL.sql',			
		'wizards/account_book_perception_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
