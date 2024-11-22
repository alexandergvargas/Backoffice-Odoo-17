# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountJournalPeriod(models.Model):
	_inherit = 'account.journal.period'

	def close_period(self):
		for period in self:
			draft_move_ids = self.env['account.cta.cte'].search([('date','>=',period.period_id.date_start),('date','<=',period.period_id.date_end),('state','=','draft'),('company_id','=',period.company_id.id)])
			if draft_move_ids:
				raise UserError('Para cerrar un periodo, primero debe publicar entradas de saldos iniciales relacionadas con el periodo.')
		return super(AccountJournalPeriod, self).close_period()