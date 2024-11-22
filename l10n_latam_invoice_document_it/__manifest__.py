# -*- encoding: utf-8 -*-
{
	'name': 'Importar Tipos de Comprobante IT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['l10n_latam_invoice_document','account_fields_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Importar Tipos de Comprobante
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
        'security/ir.model.access.csv',
	],
	'installable': True,
    'post_init_hook': '_set_default_document_type',
	'license': 'LGPL-3'
}
