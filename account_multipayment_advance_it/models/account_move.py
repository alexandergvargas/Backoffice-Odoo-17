# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
	_inherit = 'account.move'
	
	multipayment_advance_id = fields.One2many('multipayment.advance.it', 'asiento_id', string='Multipayment Advance')
	
	def write(self, vals):
		res = super(AccountMove,self).write(vals)
		self.restrict_account_multipayment_advance()
		return res
	
	def unlink(self):
		self.restrict_account_multipayment_advance()
		return super(AccountMove, self).unlink()
	
	def restrict_account_multipayment_advance(self):
		for record in self:
			if record.multipayment_advance_id:
				raise UserError ("""IMPOSIBLE ELIMINAR O MODIFICAR UN ASIENTO CREADO DESDE PAGO MULTIPLE POR FAVOR HACER EL PROCESO DESDE EL %s """%(record.multipayment_advance_id.name))