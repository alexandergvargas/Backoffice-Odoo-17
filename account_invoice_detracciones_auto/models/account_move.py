# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	def _post(self, soft=True):
		to_post = super(AccountMove,self)._post(soft=soft)
		for move in self:
			param = self.env['account.main.parameter'].search([('company_id','=',move.company_id.id)],limit=1)
			if param.auto_detrac and move.move_type in ('out_invoice','in_invoice') and move.payment_state != 'paid' and not move.move_detraccion_id:
				if not move.detraction_percent_id or move.detra_amount == 0:
					raise UserError(u'La provisión de detracciones se genera automáticamente. Por ello es necesario que los campos "Porcentaje de Detracción" y "Monto de Detracción" estén establecidos.')
				wizard = self.env['account.detractions.wizard'].create({
					'fecha':move.date,
					'monto':move.detra_amount
				})
				
				context = dict(self.env.context)
				context.update({'invoice_id': move.id,'default_move_type':'entry'})
				r = wizard.with_context(context).generar()
			
		return to_post