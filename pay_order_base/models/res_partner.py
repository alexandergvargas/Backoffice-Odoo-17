# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class ResPartner(models.Model):
	_inherit = 'res.partner'

	payment_type_catalog_id = fields.Many2one('payment.type.catalog',string='Tipo abono')