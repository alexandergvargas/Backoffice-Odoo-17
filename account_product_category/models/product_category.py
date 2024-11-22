
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_repr, float_round, float_compare
from odoo.exceptions import ValidationError
from collections import defaultdict


class ProductCategory(models.Model):
	_inherit = 'product.category'
	
	def _check_valuation_accounts(self):		
		for category in self:
			if category.property_valuation == 'manual_periodic':
				continue  
		return super(ProductCategory, self)._check_valuation_accounts()
