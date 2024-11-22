# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import re

class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_force_button_draft(self):
		for move in self:
				move.edi_show_cancel_button = False
		res = super().button_draft()
		return res