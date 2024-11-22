# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
import base64
from io import BytesIO
import re
import uuid

class AccountBookLedgerWizard(models.TransientModel):
	_inherit = 'account.book.ledger.wizard'

	currency = fields.Selection([('pen','PEN'),('usd','USD')],string='Mostrar en base a',default='pen')


	def _get_sql(self):
		sql =  super(AccountBookLedgerWizard,self)._get_sql()
		if self.currency == 'usd':
			sql_accounts = "(select array_agg(id) from account_account where company_id = %d)"%(self.company_id.id)
			if self.content == 'pick':
				if not self.account_ids:
					raise UserError(u'Debe escoger por lo menos una Cuenta')
				sql_accounts = "array[%s] " % (','.join(str(i) for i in self.account_ids.ids))

			sql = """SELECT
				may.periodo::character varying,may.fecha,may.libro,may.voucher,
				may.cuenta,may.debe,may.haber,may.balance, may.saldo,
				may.moneda,may.tc,
				may.glosa,may.td_partner,may.doc_partner,may.partner,
				may.td_sunat,may.nro_comprobante,may.fecha_doc,may.fecha_ven
				FROM get_mayorg_usd('%s','%s',%d,%s) may
			""" % (self.date_from.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_from_id.date_start.strftime('%Y/%m/%d'),
				self.date_to.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_to_id.date_end.strftime('%Y/%m/%d'),
				self.company_id.id,
				sql_accounts)
		return sql