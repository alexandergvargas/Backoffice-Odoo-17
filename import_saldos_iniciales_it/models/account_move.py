# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	@api.ondelete(at_uninstall=False)
	def _prevent_automatic_line_deletion(self):
		pass
	
	def _compute_partner_id(self):
		for line in self:
			if not  line.partner_id:
				line.partner_id = line.move_id.partner_id.commercial_partner_id
class AccountMove(models.Model):
	_inherit = 'account.move'

	apertura_id = fields.Many2one('import.move.apertura.it',string='Apertura ID',copy=False)


	
	@api.onchange('partner_id')
	def _inverse_partner_id(self):
		for invoice in self:
			if invoice.is_invoice(True):
				for line in invoice.line_ids + invoice.invoice_line_ids:
					if not  line.partner_id:
						if line.partner_id != invoice.commercial_partner_id:
							line.partner_id = invoice.commercial_partner_id
							line._inverse_partner_id()
	def _post(selfs, soft=True):
		to_post = super(AccountMove,selfs)._post(soft=soft)
		for move_id in to_post:
			if selfs.apertura_id:
				for line in move_id.line_ids.filtered(lambda l: l.account_id.id == (selfs.apertura_id.account_descargo_me.id if selfs.currency_id.name != 'PEN' else selfs.apertura_id.account_descargo_mn.id)):
					line.partner_id = selfs.apertura_id.partner_descargo.id
		return to_post	