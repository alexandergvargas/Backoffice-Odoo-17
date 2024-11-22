# -*- encoding: utf-8 -*-
{
	'name': 'Importacion Actualizar Analiticos IT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Sebastian Loraico',
	'depends': ['account_base_import_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
		Importacion Inforest IT, actualizar diario analitico
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizard/importacion_view.xml'
		],
	'installable': True
}
