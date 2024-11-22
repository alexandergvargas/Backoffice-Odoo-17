# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountBankStatementLine(models.Model):
	_inherit = 'account.bank.statement.line'
	
	@api.model
	def _prepare_move_line_default_vals(self, counterpart_account_id=None):
		data = super(AccountBankStatementLine,self)._prepare_move_line_default_vals(counterpart_account_id=counterpart_account_id)
		tc = 1
		if self.statement_id.journal_id.currency_id:
			tc = self.env['res.currency.rate'].search([('name','=',self.date),('currency_id','=',self.statement_id.journal_id.currency_id.id)],limit=1).sale_type
		data[0]['nro_comp'] = self.ref
		data[0]['type_document_id'] = self.type_document_id.id
		data[0]['cash_flow_id'] = self.cash_flow_id.id
		data[0]['tc'] = tc

		data[1]['tc'] = tc
		return data
		
	
	@api.model_create_multi
	def create(self, vals_list):
		st_lines = super(AccountBankStatementLine,self).create(vals_list)
		for st_line in st_lines:
			st_line.move_id.write({'glosa':st_line.payment_ref})
			st_line.move_id.write({'td_payment_id':st_line.catalog_payment_id.id})
		return st_lines
	
	def _synchronize_to_moves(self, changed_fields):
		res = super(AccountBankStatementLine,self)._synchronize_to_moves(changed_fields = changed_fields)
		if self._context.get('skip_account_move_synchronization'):
			return
		if not any(field_name in changed_fields for field_name in (
			 'payment_ref','catalog_payment_id','type_document_id'
		)):
			return
		for st_line in self.with_context(skip_account_move_synchronization=True):
			st_line.move_id.write({
				'td_payment_id': st_line.catalog_payment_id.id or None,
				'glosa': st_line.payment_ref,
				'l10n_latam_document_type_id': st_line.type_document_id.id or None
			})
		return res