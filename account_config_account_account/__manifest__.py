# -*- coding: utf-8 -*-
{
    'name': 'Configuración Plan contable',
    'summary': """ Configuraciones para el plan contable
    - Obligatorio
    """,
    'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
    'category': 'accounting',
    'depends': ['account_fields_it','account_menu_other_configurations' ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/account_account_config_views.xml",
       
    ],
    'application': True,
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
