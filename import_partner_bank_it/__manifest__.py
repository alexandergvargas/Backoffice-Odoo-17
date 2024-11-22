# -*- coding: utf-8 -*-

{
	'name': 'Importar Cuentas Bancarias IT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Sebastian Moises Loraico Lopez',
	'depends': ['contacts','account_fields_it','popup_it','account_base_import_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Importar Cuentas Bancarias
    - Añade funcionalidad JS
	""",
	'auto_install': True,
	'demo': [],
	"data": [
        "data/attachment_sample.xml",
        "security/ir.model.access.csv",
        "views/import_partner_bank_it.xml",
        "views/res_partner_bank_views.xml"
    ],
	'installable': True,
	'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'import_partner_bank_it/static/src/components/**/*',
        ]
    }
}
