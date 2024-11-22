# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	currency_id_book = fields.Many2one(related='move_id.currency_id', readonly=True, string='Currency Book')
	acc_number_partner_id_book = fields.Many2one(related='move_id.acc_number_partner_id', readonly=True)
	bank_id_book = fields.Many2one(related='move_id.acc_number_partner_id.bank_id', readonly=True)