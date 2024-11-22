# -*- encoding: utf-8 -*-
{
	'name': 'Actualizador Datos Adicionales IT',
	'category': 'Accounting',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','account_base_import_it'],
	'version': '1.0',
	'description':"""
	- Se crea el menú Actualizar datos adicionales
	- Se crea el menú Añadir documentos relacionados 
	""",
    'summary': """- Obligatorio""",
	'auto_install': True,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'data/attachment_sample.xml',
		'wizard/update_journal_entry_it.xml',
		'wizard/add_doc_invoice_relac_wizard.xml'
		],
	'installable': True
}
