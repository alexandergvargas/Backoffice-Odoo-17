# -*- encoding: utf-8 -*-
{
	'name': 'Cuenta personalizada',
	'category': 'Accounting',
	'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
	'depends': ['import_invoice','import_xml_invoice_it','query_ruc_dni'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Cuenta personalizada
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
        'security/ir.model.access.csv',
        'security/security.xml',
		'views/account_move.xml',
        'views/account_personalizadas.xml',
        'data/attachment_sample.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
