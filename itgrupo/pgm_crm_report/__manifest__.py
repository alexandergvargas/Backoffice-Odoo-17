# -*- coding: utf-8 -*-
{
    'name': "pgm_crm_report",
    'summary': """Personalizaciones para CRM REPORTE""",
    'description': """
        1. Añadir oportunidad a reporte de hoja de vida
    """,
    'author': "Jhonny Mack Merino Samillán. Chiclayo - Perú",
    'company': 'PGM',
    'website': "https://pggm.com/",
    'category': 'Custom',
    'version': '17.0.0.1',
    'depends': ['base', 'crm', 'hr_timesheet', ],
    'data': [
        'views/hr_timesheet_report_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
