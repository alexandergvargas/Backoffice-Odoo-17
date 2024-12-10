# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, Command

class hr_fotocheck_config(models.Model):
	_name='hr.fotocheck.config'
	_description='Configuraciones para fotocheck'
	_check_company_auto = True

	name=fields.Char('Configuracion',default='Configuraciones de fotocheck', check_company=True)
	company_id=fields.Many2one('res.company',u'Compañia',default=lambda self: self.env.company)

	logo_cert_1=fields.Binary('Logo certificado 1', check_company=True)
	logo_cert_2=fields.Binary('Logo certificado 2', check_company=True)
	logo_cert_3=fields.Binary('Logo certificado 3', check_company=True)
	logo_cert_4=fields.Binary('Logo certificado 4', check_company=True)
	logo_cert_5=fields.Binary('Logo certificado 5', check_company=True)

	backimg=fields.Binary('Imagen de Reverso', check_company=True)
	fondo_front=fields.Binary('Imagen de Fondo', check_company=True)

