{
    'name': 'Account Transfer IT',
    'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
    'depends': ['account_treasury_it'],
    'version': '1.0',
    'summary': 'Internal transfers for accounting',
    'description': """
        Module for managing internal accounting transfers between journals.
    """,
    'summary': """- Obligatorio""",
	'auto_install': True,
    'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
        'views/account_transfer_it_views.xml',
    ],
    'installable': True,
	'license': 'LGPL-3'
}
