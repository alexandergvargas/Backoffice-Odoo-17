# -*- encoding: utf-8 -*-
{
	'name': 'Importar Activos IT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_base_import_it','om_account_asset'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Se crea el menú Importar Activos
	""",
	'auto_install': True,
	'demo': [],
	"data": [
        "data/attachment_sample.xml",
        "security/ir.model.access.csv",
        "wizard/import_asset_wizard.xml",
        "views/account_asset_asset_views.xml"
    ],
	'installable': True,
	'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'import_asset_it/static/src/components/**/*',
        ]
    }
}
