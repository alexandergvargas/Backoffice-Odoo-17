# -*- encoding: utf-8 -*-
{
	'name': 'PAGO ESPECIAL',
	'version': '1.0',
	'description': 'Pago especial',
	'summary': """- Obligatorio""",
	'author': 'ITGRUPO, Sebatian Loraico Lopez',
	'license': 'LGPL-3',
	'category': 'accounting',
	'depends': [
		'account_multipayment_advance_it'
	],
	'data': [
		'views/account_main_parameter.xml',
        'views/account_move.xml'
	],

	'auto_install': True,
	'application': False,
	
}