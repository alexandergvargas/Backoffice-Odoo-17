# -*- encoding: utf-8 -*-
{
	'name': 'Query RUC and DNI',
	'category': 'Accounting',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['l10n_latam_base','l10n_pe','account_fields_it'],
	'version': '1.0',
    'summary': """- Obligatorio""",
	'description':"""
	-Parametros RUC/DNI
	Modulo para consultar RUC y DNI mediante el uso de una API
	Para instalar este modulo es necesario instalar la libreria suds-py3 con el comando 'python -m pip install suds-py3' 
	GRUPÒ : Mostrar direcciones Completas
	campos:
	     direccion_complete_it ,
	     direccion_complete_ubigeo_it (con ubigeo)
	     
	""",
	'auto_install': True,
	'demo': [],
	'data': [
			'data/res_country_state.xml',
			'views/res_country_state.xml',
			'views/res_partner.xml',
			'views/grupo.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
