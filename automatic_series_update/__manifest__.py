# -*- encoding: utf-8 -*-
{
	'name': 'Automatic Series Update',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, SEBASTIAN MIGRACION',
	'depends': ['account_voucher_name'],
    'summary': """- Obligatorio""",
	'version': '1.0',
	'description':"""
	- Automatizacion de Referencias en Base a la Serie
    - Creación de Secuencias
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
        'views/it_invoice_serie.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
