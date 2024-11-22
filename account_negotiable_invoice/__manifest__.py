# -*- coding: utf-8 -*-
{
    'name': 'Factura Negociable PM',
    'summary': """ FACTURA NEGOCIABLE EN LOS PAGOS MULTIPLES""",
    'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
    'category': 'accounting',
    'depends': ['account_multipayment_advance_it'],
    "data": [
        "security/ir.model.access.csv",
        "views/multipayment_advance_it.xml",
        "wizard/move_invoice_cash.xml",        
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
