# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	move_financial_expense_id = fields.Many2one('account.move',string=u'Asiento de Gastos Financieros',copy=False)

	def button_cancel(self):
		if self.move_financial_expense_id.id:
			if self.move_financial_expense_id.state != 'draft':
				for mm in self.move_financial_expense_id.line_ids:
					mm.remove_move_reconcile()
				self.move_financial_expense_id.button_cancel()
			self.move_financial_expense_id.line_ids.unlink()
			self.move_financial_expense_id.name = "/"
			self.move_financial_expense_id.unlink()
		return super(AccountMove,self).button_cancel()

	def button_draft(self):
		if self.move_financial_expense_id.id:
			if self.move_financial_expense_id.state != 'draft':
				for mm in self.move_financial_expense_id.line_ids:
					mm.remove_move_reconcile()
				self.move_financial_expense_id.button_cancel()
			self.move_financial_expense_id.line_ids.unlink()
			self.move_financial_expense_id.name = "/"
			self.move_financial_expense_id.unlink()
		return super(AccountMove,self).button_draft()

	def action_post(self):
		res = super(AccountMove,self).action_post()
		for move in self:
			if move.move_type == 'in_invoice':
				product_financial_expense_id = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).product_financial_expense_id
				if product_financial_expense_id:
					is_financial = False
					lines = []
					for line in move.invoice_line_ids:
						if product_financial_expense_id.id == line.product_id.id:
							lines.append(line)
							is_financial = True
					if is_financial:
						move.make_move_financial_expense(lines)
		return res


	def make_move_financial_expense(self,lines):
		m = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if not m.journal_financial_expense_id.id:
			raise UserError(u"No esta configurado el Diario de Reversiones de Compras en Parametros Principales de Contabilidad para su Compañía, es necesario si usa un producto de Gasto Financiero.")
		
		data = {
			'journal_id': m.journal_financial_expense_id.id,
			'nro_comp':(self.nro_comp if self.nro_comp else 'Borrador'),
			'ref':(self.ref if self.ref else 'Borrador'),
			'date': self.date,
			'invoice_date': self.invoice_date,
			'company_id': self.company_id.id,
			'glosa': 'EXTORNO POR GASTOS FINANCIEROS',
			'currency_rate': self.currency_rate,
			'move_type': 'entry'
		}

		move_lines = []
		debit = credit = amount_currency = 0

		for line in lines:
			values = (0,0,{
					'account_id': line.account_id.id,
					'debit': line.credit,
					'credit':line.debit,
					'name':'EXTORNO POR GASTOS FINANCIEROS',
					'partner_id': line.partner_id.id,
					'nro_comp': line.nro_comp,
					'type_document_id': line.type_document_id.id,
					'currency_id': line.currency_id.id if line.currency_id else None,
					'amount_currency': line.amount_currency*-1 if line.amount_currency else None,
					'tc': line.tc,
					'company_id': self.company_id.id,			
					})
			move_lines.append(values)
			debit += line.credit
			credit += line.debit
			amount_currency += line.amount_currency

		filtered_lines = self.line_ids.filtered(lambda l: l.account_id.account_type in ['liability_payable'])
		for filtered_line in filtered_lines:
			values = (0,0,{
						'account_id': filtered_line.account_id.id,
						'debit':filtered_line.credit,
						'credit':filtered_line.debit,
						'name':'EXTORNO POR GASTOS FINANCIEROS',
						'partner_id': filtered_line.partner_id.id,
						'nro_comp': filtered_line.nro_comp,
						'type_document_id': filtered_line.type_document_id.id,
						'currency_id': filtered_line.currency_id.id if filtered_line.currency_id else None,
						'amount_currency': filtered_line.amount_currency*-1 if filtered_line.currency_id else 0,
						'tc': filtered_line.tc,
						'company_id': self.company_id.id,
						})
			move_lines.append(values)

		data['line_ids'] = move_lines
		tt = self.env['account.move'].create(data)
		if tt.state =='draft':
			tt._post()

		for filtered_line in filtered_lines:
			ids_conciliation = []
			ids_conciliation.append(filtered_line.id)

			for line in tt.line_ids:
				if line.account_id == filtered_line.account_id and line.nro_comp == filtered_line.nro_comp and line.type_document_id == filtered_line.type_document_id and line.partner_id.id == filtered_line.partner_id.id and not line.reconciled:
					ids_conciliation.append(line.id)
		
			if len(ids_conciliation)>1:
				self.env['account.move.line'].browse(ids_conciliation).reconcile()

		self.move_financial_expense_id = tt.id