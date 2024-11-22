# -*- coding: utf-8 -*-
from odoo import models, fields, api, Command
from odoo.exceptions import UserError, ValidationError
import re

class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_register_payment(self):
		if len(self.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable','liability_payable'))) > 1 and self.move_type != 'entry':
			raise UserError(u'En el caso de tener una factura con diferentes Plazos de pago, los pagos se realizan en el menú: Tesoreria / Tesoreria / Pagos Múltiples')
		return super(AccountMove,self).action_register_payment()
	
class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'
	
	@api.depends('nro_comp')
	def _compute_display_name(self):
		for line in self:
			line.display_name = f"{line.nro_comp}"

	@api.model
	def create(self, vals):
		if 'date_maturity' in vals:
			vals['expected_pay_date'] = vals['date_maturity']
		return super(AccountMoveLine, self).create(vals)

	def write(self, vals):
		if 'date_maturity' in vals:
			vals['expected_pay_date'] = vals['date_maturity']
		return super(AccountMoveLine, self).write(vals)
	
	def remove_move_reconcile(self):
		matcheds = self.env['account.move.line']
		for m in self.matched_debit_ids:
			matcheds += m.debit_move_id
		for m in self.matched_credit_ids:
			matcheds += m.credit_move_id
		#raise UserError(str(matcheds))
		res = super(AccountMoveLine, self).remove_move_reconcile()
		for statement_line in matcheds.statement_line_id:
			statement_line.payment_ids.unlink()

			statement_line.with_context(force_delete=True).write({
				'to_check': False,
				'line_ids': [Command.clear()] + [
					Command.create(line_vals) for line_vals in statement_line._prepare_move_line_default_vals()],
			})
		return res