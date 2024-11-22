# -*- encoding: utf-8 -*-
{
	'name': 'Importar Plan Contable',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Sebastian Moises Loraico Lopez',
	'depends': [
     	'account_fields_it',
      	'account_base_import_it'
    ],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Importar Plan Contable
	""",
	'auto_install': True,
	"data": [
        "data/attachment_sample.xml",
        "security/ir.model.access.csv",
        "wizard/import_account_wizard.xml",
        "views/account_account_views.xml"
    ],
	'installable': True,
	'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'import_account_account_it/static/src/components/**/*',
        ]
    }
}
