# -*- encoding: utf-8 -*-
{
    'name': 'Hr Carta y Certificado de Trabajo',
    'category': 'Generic Modules/Human Resources',
    'author': 'ITGRUPO-HR',
    'depends': ['hr_social_benefits'],
    'version': '1.0',
    'description': 'Generacion de certificado de trabajo y Carta de retiro de CTS',
    'auto_install': False,
    'data': [
        'security/security.xml',
        'report/certificate.xml',
        'report/letter.xml',
        'views/certificate_wizard.xml',
        'views/letter_wizard.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
