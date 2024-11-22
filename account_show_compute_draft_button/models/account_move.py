# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import re

class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.depends('restrict_mode_hash_table', 'state')
	def _compute_show_reset_to_draft_button(self):
		for move in self:
			move.show_reset_to_draft_button = ((not move.restrict_mode_hash_table) and move.state in ['posted','cancel'])