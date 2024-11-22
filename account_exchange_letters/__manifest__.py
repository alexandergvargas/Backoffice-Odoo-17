# -*- encoding: utf-8 -*-
{
	'name': 'Canje de Letras It',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_treasury_it','account_multipayment_advance_it'],
	'version': '1.0',
	'description':"""
	- Sub-menu para Canje de Letras
	- Sub-menu para Parametros Canje de Letras
     - AGREGANDO RESTRICCION ASIENTOS QUE SOLO SE ELIMINE DESDE LETRAS (SEBASTIAN MOISES LORAICO LOPEZ)
	""",
	'auto_install': False,
	'demo': [],
	"data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/account_exchange_letters_parameter_views.xml",
        "views/account_exchange_letters_views.xml",
        "views/account_move_line.xml",
        "wizard/get_invoices_letters_wizard.xml"
    ],
	'installable': True,
	'license': 'LGPL-3'
}