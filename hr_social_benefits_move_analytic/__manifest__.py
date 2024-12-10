# -*- encoding: utf-8 -*-
{
	'name': 'Hr Social Benefits Move Analytic',
	'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_advances_and_loans', 'hr_payslip_run_move_analytic'],
	'version': '1.0',
	'description':"""
		Modulo para generar Asiento Contable de los Beneficios Sociales y hacer el ajuste automatico con las provisiones de BBSS
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'data/hr_salary_rule.xml',
			'views/hr_gratification.xml',
			'views/hr_cts.xml',
			'views/hr_liquidation.xml',
			'views/hr_report_asiento_planilla.xml',
			'wizard/hr_gratification_move_wizard.xml',
			'wizard/hr_cts_move_wizard.xml',
			'wizard/hr_liquidation_move_wizard.xml',
			'wizard/hr_report_asiento_planilla_wizard.xml'
			],
	'installable': True,
	'license': 'LGPL-3',
}