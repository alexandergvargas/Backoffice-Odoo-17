# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError, ValidationError

class account_payment(models.TransientModel):
	_inherit ='account.payment.register'

	manual_currency_rate = fields.Float('Rate', digits=(12, 6))
	check_active_currency = fields.Boolean('Check Active Currency')

	@api.onchange('payment_date','currency_id')
	def _get_currency_rate(self):
		if not self.is_personalized_change:
			currency_id = self.env.ref('base.USD') if self.currency_id == self.company_id.currency_id else self.currency_id
			cu_rate = self.env['res.currency.rate'].search([('name','=',self.payment_date),('currency_id','=',currency_id.id),('company_id','=',self.company_id.id)],limit=1)
			if cu_rate:
				self.type_change = cu_rate.sale_type

	@api.model
	def default_get(self, default_fields):
		rec = super(account_payment, self).default_get(default_fields)
		active_ids = self._context.get('active_ids') or self._context.get('active_id')
		active_model = self._context.get('active_model')

		# Check for selected invoices ids
		if not active_ids or active_model != 'account.move':
			return rec

		
		invoices = self.env['account.move'].browse(active_ids).filtered(
			lambda move: move.is_invoice(include_receipts=True))
		
		if (len(invoices) == 1):
			rec.update({
				'is_personalized_change': invoices.tc_per,
				'manual_currency_rate': invoices.manual_currency_rate
			})
		return rec


	@api.model
	def _create_payment_vals_from_batch(self, batch_result):
		rec = super(account_payment, self)._create_payment_vals_from_batch(batch_result)
		active_ids = self._context.get('active_ids') or self._context.get('active_id')
		active_model = self._context.get('active_model')

		# Check for selected invoices ids
		if not active_ids or active_model != 'account.move':
			return rec
			
		account_move = self.env['account.move'].search([('name','=',rec.get('ref'))]).ids
		for active_id in active_ids:
			if active_id in account_move:
				invoices = self.env['account.move'].browse(active_id).filtered(
					lambda move: move.is_invoice(include_receipts=True))
			
				for invoice in invoices:
					rec.update({
						'is_personalized_change': invoice.tc_per,
						'manual_currency_rate': invoice.manual_currency_rate
					})

				return rec
		return rec



	@api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date', 'manual_currency_rate')
	def _compute_amount(self):
		
		for wizard in self:
			if wizard.source_currency_id == wizard.currency_id:
				# Same currency.
				wizard.amount = wizard.source_amount_currency
			else:
				# Foreign currency on payment different than the one set on the journal entries.
				amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date)
				wizard.amount = amount_payment_currency
		rec = super(account_payment, self)._compute_amount()
	
	@api.depends('amount')
	def _compute_payment_difference(self):
		
		for wizard in self:
			if wizard.source_currency_id == wizard.currency_id:
				# Same currency.
				wizard.payment_difference = wizard.source_amount_currency - wizard.amount
			else:
				# Foreign currency on payment different than the one set on the journal entries.
				amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date)
				wizard.payment_difference = amount_payment_currency - wizard.amount
		rec = super(account_payment, self)._compute_payment_difference()


	def _create_payment_vals_from_wizard(self,batch_result):
		res = super(account_payment, self)._create_payment_vals_from_wizard(batch_result)
		if self.is_personalized_change:
			res.update({'is_personalized_change': self.is_personalized_change, 'manual_currency_rate': self.manual_currency_rate,'check_active_currency':True})
		else: 
			res.update({'is_personalized_change': False, 'manual_currency_rate': 0.0,'check_active_currency':False})
		return res


class AccountPayment(models.Model):
	_inherit = "account.payment"
	_description = "Payments"

	amount_currency = fields.Float('Amount Currency')
	check_active_currency = fields.Boolean('Check Active Currency')
	manual_currency_rate = fields.Float('Rate',compute='_compute_manual_currency_rate',store=True)

	@api.onchange('date','currency_id')
	def _get_currency_rate(self):
		if not self.is_personalized_change:
			currency_id = self.env.ref('base.USD') if self.currency_id == self.company_id.currency_id else self.currency_id
			cu_rate = self.env['res.currency.rate'].search([('name','=',self.date),('currency_id','=',currency_id.id),('company_id','=',self.company_id.id)],limit=1)
			if cu_rate:
				self.type_change = cu_rate.sale_type

	@api.depends('type_change')
	def _compute_manual_currency_rate(self):
		for i in self:
			i.manual_currency_rate = (1/i.type_change) if i.type_change != 0 else 0

	#@api.onchange('is_personalized_change', 'currency_id')
	#def check_currency_id(self):
	#	for payment in self:
	#		if payment.is_personalized_change:
	#			if payment.currency_id == payment.company_id.currency_id:
	#				payment.is_personalized_change = False
	#				raise UserError(_('Company currency and Payment currency same, You can not add manual Exchange rate for same currency.'))

	@api.model
	def default_get(self, default_fields):

		rec = super(AccountPayment, self).default_get(default_fields)
		active_ids = self._context.get('active_ids') or self._context.get('active_id')
		active_model = self._context.get('active_model')

		# Check for selected invoices ids
		if not active_ids or active_model != 'account.move':
			return rec

		invoices = self.env['account.move'].browse(active_ids).filtered(
			lambda move: move.is_invoice(include_receipts=True))


		if (len(invoices) == 1):
			rec.update({
				'is_personalized_change': invoices.tc_per,
				'manual_currency_rate': invoices.manual_currency_rate,
			})
		return rec

	@api.model
	def _compute_payment_amount(self, invoices, currency, journal, date):
		'''Compute the total amount for the payment wizard.
		:param invoices:    Invoices on which compute the total as an account.invoice recordset.
		:param currency:    The payment's currency as a res.currency record.
		:param journal:  The payment's journal as an account.journal record.
		:param date:        The payment's date as a datetime.date object.
		:return:            The total amount to pay the invoices.
		'''
		company = journal.company_id
		currency = currency or journal.currency_id or company.currency_id
		date = date or fields.Date.today()

		if not invoices:
			return 0.0

		self.env['account.move'].flush(['type', 'currency_id'])
		self.env['account.move.line'].flush(['amount_residual', 'amount_residual_currency', 'move_id', 'account_id'])
		self.env['account.account'].flush(['user_type_id'])
		self.env['account.account.type'].flush(['type'])
		self._cr.execute('''
				SELECT
					move.type AS type,
					move.currency_id AS currency_id,
					SUM(line.amount_residual) AS amount_residual,
					SUM(line.amount_residual_currency) AS residual_currency
				FROM account_move move
				LEFT JOIN account_move_line line ON line.move_id = move.id
				LEFT JOIN account_account account ON account.id = line.account_id
				LEFT JOIN account_account_type account_type ON account_type.id = account.user_type_id
				WHERE move.id IN %s
				AND account_type.type IN ('receivable', 'payable')
				GROUP BY _prepare_move_line_default_valsmove.id, move.type
			''', [tuple(invoices.ids)])
		query_res = self._cr.dictfetchall()

		total = 0.0
		for inv in invoices:
			for res in query_res:
				move_currency = self.env['res.currency'].browse(res['currency_id'])
				if move_currency == currency and move_currency != company.currency_id:
					total += res['residual_currency']
				else:
					if not inv.tc_per:
						total += company.currency_id._convert(res['amount_residual'], currency, company, date)
					else:
						total += res['residual_currency'] * inv.manual_currency_rate
		return total

	@api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id', 'payment_type', 'manual_currency_rate')
	def _compute_payment_difference(self):
		draft_payments = self.filtered(lambda p: p.invoice_ids and p.state == 'draft')
		for pay in draft_payments:
			payment_amount = -pay.amount if pay.payment_type == 'outbound' else pay.amount
			pay.payment_difference = pay._compute_payment_amount(pay.invoice_ids, pay.currency_id, pay.journal_id,
																 pay.payment_date) - payment_amount
		(self - draft_payments).payment_difference = 0

	def _prepare_move_line_default_vals(self, write_off_line_vals=None,force_balance=None):
		result = super()._prepare_move_line_default_vals(write_off_line_vals,force_balance)
		if self.is_personalized_change and self.manual_currency_rate > 0:
			for res in result:
				if self.company_id.currency_id.id == self.currency_id.id:
					amount_currency = res['amount_currency']
					if res.get('debit'):
						res['amount_currency'] = amount_currency / self.manual_currency_rate
						res['debit'] = abs(amount_currency) / self.manual_currency_rate
					if res.get('credit'):
						res['amount_currency'] = amount_currency / self.manual_currency_rate
						res['credit'] =  abs(amount_currency) / self.manual_currency_rate
				else:
					amount_currency = res['amount_currency']
					if res.get('debit') > 0:
						res['amount_currency'] = amount_currency 
						res['debit'] = abs(amount_currency) / self.manual_currency_rate
					if res.get('credit') > 0:
						res['amount_currency'] = amount_currency 
						res['credit'] = abs(amount_currency) / self.manual_currency_rate
		return result
	
	def write(self,vals):
		result = super().write(vals)
		if vals.get('amount') and vals.get('amount_currency'):
			for record in self:
				record.amount_currency = vals.get('amount')
		return result
	
	@api.model_create_multi
	def create(self, vals_list):
		for vals in vals_list:
			if vals.get('amount_currency'):
				vals.update({'amount':vals.get('amount_currency')})
			result = super().create(vals_list)
			if vals.get('amount'):
				vals.update({'amount_currency':vals.get('amount')})
				result.sync_amount()
		return result

	@api.onchange('amount_currency')
	def onchange_amount_currency(self):
		for record in self:
			record.amount = record.amount_currency

	def action_post(self):
		''' draft -> posted '''
		for p in self:
			if p.check_active_currency == False : 
				p.move_id.update({'tc_per': p.is_personalized_change,
					'manual_currency_rate':p.manual_currency_rate,})
				p.update({'amount':p.amount_currency})
		self.move_id._post(soft=False)

		self.filtered(
			lambda pay: pay.is_internal_transfer and not pay.paired_internal_transfer_payment_id
		)._create_paired_internal_transfer_payment()

	def action_draft(self):
		''' posted -> draft '''
		if self.check_active_currency == False : 
			self.update({'amount':self.amount_currency})
		self.move_id.button_draft()


	def sync_amount(self):
		for record in self:
			if record.is_personalized_change and record.manual_currency_rate:
				if record.company_id.currency_id.id == record.currency_id.id:
					if self.check_active_currency == True : 
						record.amount_currency = record.amount 
				else:
					record.amount_currency = record.amount
			else:
				record.amount_currency = record.amount
	
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
