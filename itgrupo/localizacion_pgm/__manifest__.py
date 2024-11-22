# -*- encoding: utf-8 -*-
{
    'name': 'Localizacion PGM',
    'category': '',
    'author': 'Alexander Gutierrez Vargas',
    'depends': ['base', 'product', 'account','account_base_import_it','crm','utm'],
    'version': '1.0',
    'description': """Desarrollos y Parametrizaciones
	""",
    'auto_install': False,
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'security/security_user.xml',
        'data/attachment_sample.xml',
        'view/account_move.xml',
        'view/crm_lead_view.xml',
        'view/crm_stage.xml',
        'view/import_contactos.xml',
        'view/product_category.xml',
        'view/product_template.xml',
        'view/project_project.xml',
        'view/res_partner.xml',
        'view/utm_campaign.xml',


    ],
    'installable': True
}
