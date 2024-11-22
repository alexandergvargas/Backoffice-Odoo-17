# -*- encoding: utf-8 -*-
{
	'name': 'Anticipos en Lineas de Factura',
	'category': 'Accounting',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Aplicar Tipo y Nro de Dodumento a lineas de Anticipo
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/account_move.xml',
		'wizards/account_anticipos_wizard.xml'
	],
	'installable': True
}
