# -*- encoding: utf-8 -*-
{
	'name': 'Pago Masivo de Detracciones',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_multipayment_advance_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Generar Pago Masivo de Detracciones en Base a Pagos Multiples
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/multipayment_advance_it.xml',
		'wizards/massive_payment_detractions_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}