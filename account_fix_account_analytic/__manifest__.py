# -*- coding: utf-8 -*-
{
    'name': 'FIX Distribución Analitica',
    'summary': """ Restricción Distribucion analtica 
    - Obligatorio
    """,
    'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
    'category': 'accounting',
    'depends': ['account_fields_it', ],
    "data": [
        "views/account_analytic_plan_views.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
