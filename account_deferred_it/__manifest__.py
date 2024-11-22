# -*- encoding: utf-8 -*-

{
	'name': 'Modelos de diferidos',
	'version': '1.0',
	'description': 'Modelos de ingresos y gastos diferidos',
	'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
	'license': 'LGPL-3',
	'category': 'Accounting',
	'depends': [
		'account','account_fields_it'
	],
	'data': [
		'security/security.xml',
        'security/ir.model.access.csv',
        'views/account_deferred.xml',
        'views/account_account.xml',
        'views/account_move.xml',
        'views/account_deferred_line.xml',
        'wizard/account_deferred_wizard.xml',
	],	
	'auto_install': False,
	'application': False,
	
}