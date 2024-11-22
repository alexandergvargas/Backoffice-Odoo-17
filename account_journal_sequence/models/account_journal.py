# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountJournal(models.Model):
	_inherit = 'account.journal'
	
	def view_sequence_journal_ids(self):
		self.ensure_one()
		action = self.env.ref('account_voucher_name.action_account_journal_sequence_form').read()[0]
		domain = [('journal_id', '=', self.id)] 
		views = [(self.env.ref('account_voucher_name.view_account_journal_sequence_list').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=None, views=views)
	
	def generate_sequence_journal(self):
		journal_ids = [record.id for record in self]
		sequence = self.env['account.sequence.journal.wizard'].create({'journal_ids': [(6, 0, journal_ids)]})
		return {
			'name':u'Aplicar Secuencia',
			'res_id':sequence.id,
			'view_mode': 'form',
			'res_model': 'account.sequence.journal.wizard',
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
		#return sequence.do_rebuild()
		
	
