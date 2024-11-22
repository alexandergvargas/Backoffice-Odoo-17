# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'

	auto_detrac = fields.Boolean(string='Generar provisión de detracción automática',default=False)