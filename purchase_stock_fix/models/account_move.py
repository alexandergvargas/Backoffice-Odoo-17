# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import re

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'
	
	def _prepare_pdiff_aml_vals(self, qty, unit_valuation_difference):
		return []