# -*- coding: utf-8 -*-

{
	'name': 'Importar Productos IT',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Sebastian Moises Loraico Lopez',
	'depends': ['popup_it','account_base_it','account_base_import_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	- Importar producto
    - Se agrega la funcionalidad de JS
	""",
	'auto_install': True,
	'demo': [],
	"data": [
        "data/attachment_sample.xml",
        "security/ir.model.access.csv",
        "security/product_import_security.xml",
        "views/import_product.xml",
        "views/product_template_views.xml"
    ],
	'installable': True,
	'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'import_product_it/static/src/components/**/*',
        ]
    }
}