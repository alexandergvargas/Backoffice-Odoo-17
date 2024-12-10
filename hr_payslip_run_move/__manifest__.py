# -*- encoding: utf-8 -*-
{
	'name': 'Hr Payslip Run Move',
	'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields', 'account','account_fields_it'],
	'version': '1.0',
	'description':"""
		Modulo para generar Asiento Contable de Nomina por Lotes
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'views/hr_main_parameter.xml',
			'views/hr_payslip_run.xml',
			'views/hr_payslip_run_move.xml',
			'views/hr_salary_rule.xml',
			'wizard/hr_payslip_run_move_wizard.xml',
			'hr_functions.sql'
		],
	'installable': True,
	'license': 'LGPL-3',
}
