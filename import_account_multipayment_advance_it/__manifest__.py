# -*- coding: utf-8 -*-
{
    'name': 'Importador Lineas Caja',
    'version': '1.0',
    'description': 'IMPORTADOR DE LINEAS DE CAJA DE PAGOS MULTIPLES',
    'summary': """- Obligatorio""",
    'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
    'license': 'LGPL-3',
    'category': '',
    'depends': [
        'account_multipayment_advance_it'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/attachment_sample.xml',
        'views/multipayment_advance_it.xml',
        'wizard/import_account_multipayment_advance_wizard.xml'
    ],   
    'auto_install': True,
    'application': False,   
}