# -*- encoding: utf-8 -*-
{
	'name': 'Hr Fortnightly',
	'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields','hr_voucher','hr_vacations','hr_advances_and_loans'],
	'version': '1.0',
	'description':"""
		Modulo para Generar Adelantos quincenales
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/security.xml',
			 'security/ir.model.access.csv',
			 'data/hr_payroll_structure.xml',
			 'data/hr_payslip_input_type.xml',
			 'data/hr_work_entry_type.xml',
			 'data/hr_salary_rule.xml',
			 'wizard/hr_payroll_payslips_by_employees_views.xml',
			 'wizard/hr_employee_news_wizard.xml',
			 'wizard/hr_planilla_tabular_wizard.xml',
			 'views/hr_fortnightly.xml',
			 'views/hr_payslip.xml',
			 'views/hr_main_parameter.xml'
			],
	'installable': True,
	'license': 'LGPL-3',
}