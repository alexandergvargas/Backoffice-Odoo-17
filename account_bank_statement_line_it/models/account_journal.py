# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountJournal(models.Model):
	_inherit = 'account.journal'
	

	def open_action_with_context(self):
		action_name = self.env.context.get('action_name', False)
		if not action_name:
			return False
		ctx = dict(self.env.context, default_journal_id=self.id)
		if ctx.get('search_default_journal', False):
			ctx.update(search_default_journal_id=self.id)
			ctx['search_default_journal'] = False  # otherwise it will do a useless groupby in bank statements
		ctx.pop('group_by', None)
		if action_name == 'action_bank_statement_tree':
			action = self.env['ir.actions.act_window']._for_xml_id(f"account_treasury_it.action_bank_statement_tree_it")
		else:
			action = self.env['ir.actions.act_window']._for_xml_id(f"account.{action_name}")
			action['context'] = ctx
			if ctx.get('use_domain', False):
				action['domain'] = isinstance(ctx['use_domain'], list) and ctx['use_domain'] or ['|', ('journal_id', '=', self.id), ('journal_id', '=', False)]
				action['name'] = _(
					"%(action)s for journal %(journal)s",
					action=action["name"],
					journal=self.name,
				)
		return action