# -*- encoding: utf-8 -*-
{
    'name': "Hr Payslip Run Move Analytic",
    'category': 'Generic Modules/Human Resources',
    'author': "ITGRUPO-HR",
    'depends':['hr_payslip_run_move','hr_provisions'],
    'version': '0.1',
    'summary':
        """ Automatizacion de asientos de planillas, considerando el elemento 9 """,
    'description':
        """creacion de tablas para configurar mas de una cuenta de gasto en reglas salariales y 
        contabilizar el asiento mensual de planillas y provisiones de BBSS """,
    'data': [
        'security/ir.model.access.csv',
        'views/hr_analytic_salary_rule.xml',
        'views/hr_main_parameter.xml',
		'views/hr_provisions.xml',
        'wizards/hr_import_analytic_wizard.xml',
    ],
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3'
}