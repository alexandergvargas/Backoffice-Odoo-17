# -*- encoding: utf-8 -*-
{
	'name': 'Hr Payroll Night Time',
	'category': 'Generic Modules/Human Resources',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields'],
	'version': '1.0',
	'description':"""
		Modulo para calcular nominas en horario nocturno
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/hr_work_entry_type.xml',
		'data/hr_salary_rule.xml',
		'data/resource_data.xml',
		# 'views/hr_main_parameter.xml',
			],
	'installable': True,
	'license': 'LGPL-3',
}