# -*- coding: utf-8 -*-
{
    'name': 'Gastos Vinculados Contabilidad',
    'summary': """ Gasto Vinculado Contabilidad """,
    'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
    'category': 'accounting',
    'depends': ['landed_cost_it', ],
    "data": [
        "views/landed_cost_it_views.xml",
        "views/account_main_parameter_views.xml",
        "views/account_move_line_views.xml",
        "views/account_move_views.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
