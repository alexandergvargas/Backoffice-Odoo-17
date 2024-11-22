# -*- coding: utf-8 -*-
from odoo import models, fields, api, Command
from odoo.exceptions import UserError, ValidationError
import re

class ResPartnerBank(models.Model):
	_inherit = 'res.partner.bank'

	@api.depends('acc_number', 'bank_id')
	def _compute_display_name(self):
		for acc in self:
			acc.display_name = f'{acc.acc_number} - {acc.bank_id.name}' if acc.bank_id else acc.acc_number