# -*- encoding: utf-8 -*-
{
	'name': 'Account Credit Note',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Sebatian Moises Loraico Lopez',
	'depends': ['account_fields_it','l10n_latam_invoice_document_it','account_debit_note'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	Funcionalidades para Notas de Credito
	""",
	'auto_install': True,
	'demo': [],
	'data':	[
        	'views/account_move_reversal.xml',
			'views/account_move.xml'],
	'installable': True,
	'license': 'LGPL-3'
}