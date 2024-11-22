# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
	_inherit = 'account.move'


	letters_id = fields.One2many('account.exchange.letters', 'move_id', string='Letra')
	
	def write(self, vals):
		res = super(AccountMove,self).write(vals)
		self.restrict_account_exchange_letters()
		return res
	
	def unlink(self):
		self.restrict_account_exchange_letters()
		return super(AccountMove, self).unlink()
	
	def restrict_account_exchange_letters(self):
		for record in self:
			if record.letters_id:
				raise UserError ("""IMPOSIBLE ELIMINAR O MODIFICAR UN ASIENTO CREADO DESDE LETRAS POR FAVOR HACER EL PROCESO DESDE LA LETRA %s """%(record.letters_id.name))