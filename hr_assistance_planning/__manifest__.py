# -*- coding: utf-8 -*-
{
    'name' : 'Hr Assistance Planning',
    'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
    'depends' : ['hr_attendance','barcodes','hr_fields','hr_leave','resource','web_gantt'],
    'version': '1.0',
    'description':"""
        Modulo que permite planificar los turnos de los trabajadores
        """,
    'auto_install': False,
    'demo': [],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/hr_attendance_activity.xml',
        'report/hr_employee_badge.xml',
        'views/hr_fotocheck_config.xml',
        'views/hr_attendance_activity.xml',
        'views/hr_assistance_planning.xml',
        'views/hr_assistance_planning_line.xml',
        'views/hr_attendance.xml',
        'views/hr_attendance_monitor.xml',
        'wizard/hr_employee_planning_wizard.xml',
        'wizard/hr_monthly_attendance_wizard.xml',
        'report/hr_monthly_attendance_report.xml',
        # 'views/hr_attendance_kiosk_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_assistance_planning/static/src/components/**/*',
            'hr_assistance_planning/static/src/views/**/*',
            'hr_assistance_planning/static/src/scss/planning_gantt.scss',
            'hr_assistance_planning/static/src/scss/planning_list.scss',
            'hr_assistance_planning/static/src/js/tours/planning.js',
        ],
        # 'web.assets_frontend': [
        #     'hr_assistance_planning/static/src/scss/planning_calendar_report.scss',
        #     'hr_assistance_planning/static/src/js/planning_calendar_front.js',
        # ],
    },
     # 'hr_attendance.assets_public_attendance': [
        #     "hr_assistance_planning/static/public_kiosk/**/*",
        # ]
    'installable': True,
    'license': 'LGPL-3',
}