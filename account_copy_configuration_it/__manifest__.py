# -*- encoding: utf-8 -*-
{
	'name': 'Copiar configuracion PC',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_menu_other_configurations'],
	'version': '1.0',
	'description':"""
		Copiar :
        - Cuentas Contables
        - Diarios
        - Impuestos
        - Cuentas Analíticas
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizard/account_copy_configuration_it.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
