# -*- coding: utf-8 -*-
{
    'name': "Volver invisible a grupo",
    'author': 'ITGRUPO, Alessandro Pelayo Mollocondo Medrano',
    'category': 'Account',
    'description': """Modulo que permite ocutlar un grupo de las facturas sin afectar lo demas""",
    'version': '1.0',
    'summary': 'Modificaciones personalizadas para account',
    'depends': ['account', 'account_fields_it'],
    'data': [
        'views/views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}