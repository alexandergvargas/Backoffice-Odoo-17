# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
periods = {'00':'opening',
		   '01':'january',
		   '02':'february',
		   '03':'march',
		   '04':'april',
		   '05':'may',
		   '06':'june',
		   '07':'july',
		   '08':'august',
		   '09':'september',
		   '10':'october',
		   '11':'november',
		   '12':'december',
		   '13':'closing'}
def get_period(account_date,is_opening_close):
		if is_opening_close and account_date.strftime('%m%d') == '0101':
			return '00'
		elif is_opening_close and account_date.strftime('%m%d') == '1231':
			return '13'
		else:
			return account_date.strftime('%m')
		
def lpad(s, length, char=' '):
		padding = char * (length - len(s))
		return padding + s

class AccountMove(models.Model):
	_inherit = 'account.move'

	def _post(self, soft=True):
		for move in self:
			if move.vou_number == '/':
				reg = self.env['account.journal.sequence'].search([('journal_id','=',move.journal_id.id),('fiscal_year_id','=',self.env['account.fiscal.year'].search([('name','=',str(move.date.year))],limit=1).id)],limit=1)
				if not reg:					
					raise UserError(u'No existe una secuencia para el diario y la fecha seleccionada.')
				seq = reg[periods[get_period(move.date,move.is_opening_close)]]
				move.vou_number = str(move.date.month)+"-"+str(lpad(str(seq), 6, '0'))
				reg.write({periods[get_period(move.date,move.is_opening_close)]: seq + 1})
			move.name = move.nro_comp if move.move_type != 'entry' else (move.date.strftime('%Y-%m-') or '') + move.vou_number
		res = super(AccountMove,self)._post(soft=soft)
		return res
	
	@api.depends('nro_comp','vou_number','state','date')
	def _compute_name(self):
		for move in self:
			move_name = '/'
			if move.state == 'posted':
				if move.move_type == 'entry':
					move_name = (move.date.strftime('%Y-') or '') + move.vou_number
				else:
					move_name = move.nro_comp
			move.name = move_name