# -*- encoding: utf-8 -*-
{
	'name': 'COSTOS PRODUCCION',
	'category': 'Accounting',
	'author': 'ITGRUPO,Sebastian Moises Loraico Lopez, Glenda Julia Merma Mayhua',
	'depends': ['account_sunat_it'],
	'version': '1.0',
	'description':"""
		- Costos de Produccion
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
        'security/security.xml',
		'security/ir.model.access.csv',
        'views/annual_cost_of_sales.xml',        
		'views/annual_valued_cost_of_production.xml',   
		'views/cost_centers.xml',   
       	'views/production_costs_parameter.xml',   
		'views/monthly_cost_elements.xml',   
		'views/menu_item.xml',   
		'wizards/popup_it_production_cost.xml',
		'wizards/account_sunat_production_cost_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}