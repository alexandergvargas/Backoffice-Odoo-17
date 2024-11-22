{
    'name': 'Reportería Clínica Zegarra',
    'summary': 'Modulo de reporteria Clínica Zegarra',
    'version': '1.0',
    'author': 'Alexander Gutierrez Vargas',
    'license': '',
    'category': 'Uncategorized',

    'depends': [
        'base',
        'sale',
        'sale_crm',

    ],
    'external_dependencies': {
        'python': [
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/security_user.xml',
        'views/ficha_informativa.xml',
        'views/reporte_corporal.xml',
        'views/reporte_quirurgico.xml',
        'views/sequencia.xml',

    ],
    'demo': [
    ],
    'js': [
    ],
    'css': [
    ],
    'qweb': [
    ],

    'test': [
    ],

    'installable': True,
    'application': True,
}
