# -*- coding: utf-8 -*-
{
    'name': 'FIx del modulo account_edi_ubl_cii',
    'summary': """ Elimina sector de Facturación Electronica
     - Obligatorio 
     """,
    'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
    'category': 'Accounting',
    'depends': ['account_edi_ubl_cii',],
    'data': [
        'views/view_partner_property_form.xml'
    ],
    'application': True,
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
