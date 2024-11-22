# -*- coding: utf-8 -*-
{
    'name': "prm_crm",
    'summary': """Personalizaciones para CRM """,
    'description': """
        1. Ingreso de hoja de horas en la oportunidad/lead
    """,
    'author': "Jhonny Mack Merino Samillán. Chiclayo - Perú",
    'company': 'PGM',
    'website': "https://pggm.com/",
    'category': 'Custom',
    'version': '17.0.0.1',
    'depends': ['base', 'crm', 'hr_timesheet', 'timesheet_grid'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/crm_lead_views.xml',
        'views/hr_timesheet_views.xml',
        'wizard/crm_lead_create_timesheet_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
