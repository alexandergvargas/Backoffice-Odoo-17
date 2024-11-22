# -*- encoding: utf-8 -*-
{
    'name': 'Developments pgm',
    'category': '',
    'author': 'Alexander Gutierrez Vargas',
    'depends': ['base', 'sale','account','product','sale_subscription','project'],
    'version': '1.0',
    'description': """Desarrollos y Parametrizaciones de PGM
	""",
    'auto_install': False,
    'demo': [],
    'data': [
        'report/sale_order_report.xml',
        'report/sale_order_template.xml',
        'security/ir.model.access.csv',
        'security/rules_security.xml',
        'view/plantilla_reporte.xml',
        'view/sale_order.xml',
        'view/menu.xml',
    ],
    'installable': True
}
