# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrContributions(models.Model):
	_name = 'hr.contributions'
	_description = 'Hr Contributions'

	name = fields.Char(string='Descripcion', required=True)
	code = fields.Char(string='Codigo', required=True)
	type = fields.Selection([('fixed','Importe Fijo'),('percentage','Porcentaje')],default='percentage',string='Tipo')
	tasa = fields.Float(string='Tasa')
	amount = fields.Float(string="Monto")

	# percent = fields.Float(string='%', digits=(12,2))
