# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'
	

	payment_special = fields.Boolean(
			string=u'Aplica Pago Especial', 
			default=False)
	