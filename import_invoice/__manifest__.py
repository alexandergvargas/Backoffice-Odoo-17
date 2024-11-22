# -*- encoding: utf-8 -*-
{
	'name': 'Importar Facturas IT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Sebastian Moises Loraico Lopez',
	'depends': ['account_base_import_it','account_move_autofill','bi_manual_currency_exchange_rate_invoice_payment'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	-Sub-menu para importar Facturas Cliente/Proveedor
    - SE AGREGO LA FUNCIONALIDAD DE JS
	""",
	'auto_install': True,
	'demo': [],
	"data": [
        "data/attachment_sample.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/import_invoice_it.xml",
    ],
	'installable': True,
	'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'import_invoice/static/src/components/**/*',
        ]
    }
}