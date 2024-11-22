# -*- encoding: utf-8 -*-
{
    'name': 'Developments cai',
    'category': '',
    'author': 'Alexander Gutierrez Vargas',
    'depends': ['base', 'crm', 'sale', 'sale_subscription', 'purchase','sale_crm','account','account_edi'],
    'version': '1.0',
    'description': """Desarrollos y Parametrizaciones de CAI
	""",
    'auto_install': False,
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'security/rules_security.xml',
        'views/crm_lead.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/account_move.xml',
        'views/grupo_partner.xml',
        'views/menu.xml',
    ],
    'installable': True
}
