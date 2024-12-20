# -*- encoding: utf-8 -*-
{
	'name': 'Hr Fields Payroll',
	'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_base','resource','hr_work_entry_contract'],
	'version': '1.0',
	'description':"""
	Modulo para agregar campos necesarios para la Localizacion Peruana de RRHH
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/hr_payroll_structure.xml',
		'data/hr_payroll_structure_type.xml',
		'data/hr_payslip_input_type.xml',
		'data/hr_work_entry_type.xml',
		'data/hr_salary_rule_category.xml',
		'data/hr_salary_rule.xml',
		'data/resource_data.xml',
		'data/hr_salary_attachment_type.xml',
		'wizard/hr_payroll_structure_wizard.xml',
		'wizard/hr_payroll_payslips_by_employees_views.xml',
		'wizard/hr_planilla_tabular_wizard.xml',
		'wizard/hr_employee_news_wizard.xml',
		'views/hr_employee.xml',
		'views/hr_contract.xml',
		'views/hr_salary_rule.xml',
		'views/hr_salary_rule_category.xml',
		'views/hr_payslip.xml',
		'views/hr_payslip_run.xml',
		'views/hr_payroll_structure.xml',
		'views/hr_payroll_structure_type.xml',
		'views/hr_payslip_input_type.xml',
		'views/hr_work_entry_type.xml',
		'views/hr_planilla_tabular.xml',
		'views/resource_calendar.xml',
		'report/hr_contract.xml',
		'report/hr_employee.xml'
	],
	'installable': True,
	'license': 'LGPL-3',
}
