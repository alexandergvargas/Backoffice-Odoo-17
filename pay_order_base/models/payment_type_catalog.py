# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PaymentTypeCatalog(models.Model):
	_name = 'payment.type.catalog'

	name = fields.Char(string='Descripcion',required=True)