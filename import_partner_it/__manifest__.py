# -*- coding: utf-8 -*-

{
	'name': 'Importar Partner IT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Sebastian Moises Loraico Lopez',
	'depends': ['contacts','account_fields_it','popup_it','account_base_import_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Importar Partner
    - Se añade la funcinalidad de JS
	""",
	'auto_install': True,
	'demo': [],
	"data": [
        "data/attachment_sample.xml",
        "security/ir.model.access.csv",
        "views/import_partner_it.xml",
        "views/res_partner_views.xml"
    ],
	'installable': True,
	'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'import_partner_it/static/src/components/**/*',
        ]
    }
}
