# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountExchangeLettersParameter(models.Model):
	_name = 'account.exchange.letters.parameter'
	_description = 'Account Exchange Letters Parameter'

	name = fields.Char(string='Nombre',default='Parametros de Canje de Letras')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	account_receivable_portfolio_mn = fields.Many2one('account.account', string='Cuenta de Letras en Cartera MN')
	account_receivable_portfolio_me = fields.Many2one('account.account', string='Cuenta de Letras en Cartera ME')
	account_receivable_collection_mn = fields.Many2one('account.account', string='Cuenta de Letras en Cobranza MN')
	account_receivable_collection_me = fields.Many2one('account.account', string='Cuenta de Letras en Cobranza ME')
	account_receivable_discount_mn = fields.Many2one('account.account', string='Cuenta de Letras en Descuento MN')
	account_receivable_discount_me = fields.Many2one('account.account', string='Cuenta de Letras en Descuento ME')
	account_payable_mn = fields.Many2one('account.account', string='Cuenta de Letras por Pagar MN')
	account_payable_me = fields.Many2one('account.account', string='Cuenta de Letras por Pagar ME')

	exchange_diary_receivable_letters = fields.Many2one('account.journal', string='Diario de Canje de Letras por Cobrar')
	exchange_diary_payable_letters = fields.Many2one('account.journal', string='Diario de Canje de Letras por Pagar')

	letter_document_type = fields.Many2one('l10n_latam.document.type',string=u'Tipo Documento Letras')
	serie_id = fields.Many2one('it.invoice.serie',string='Serie',copy=False)

	@api.constrains('company_id')
	def _check_unique_parameter(self):
		self.env.cr.execute("""select id from account_exchange_letters_parameter where company_id = %d""" % (self.company_id.id))
		res = self.env.cr.dictfetchall()
		if len(res) > 1:
			raise UserError(u"Ya existen Parametros Principales de Letras para esta Compañía")