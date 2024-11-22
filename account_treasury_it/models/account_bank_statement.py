# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


import re

from math import copysign
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
	
class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'
	#_sequence_index = "journal_id"

	def unlink(self):
		for i in self:			
			if i.line_ids:
				raise UserError(u"Primero se debe eliminar las lineas del Extracto " + str(i.name))
			return  super(AccountBankStatement, i).unlink()
	
	date_aux  = fields.Date('Fecha', required=True)
	aux_journal_id = fields.Many2one('account.journal', string='Diario', required=True, domain="[('id','in', journal_domain_ids)]",)
	journal_type = fields.Selection([
		('bank', 'Banco'),
		('cash', 'Caja'),
		('surrender', 'Rendiciones')
	],string="Tipo", help="Technical field used for usability purposes")
	journal_domain_ids = fields.Many2many(
		"account.journal",
		compute="get_diarios_domains",
	)

	#------------------------CAMPOS RENDICIONES----------------------#
	partner_id = fields.Many2one(
		string=_('Empleado'),
		comodel_name='res.partner',
	)
	#----------------------------------------------------------------#

	def reg_account_move_lines_it(self):
		for statement in self:
			if statement.journal_type != 'surrender':
				raise UserError(u'Solo se aplica en Rendiciones.')
			sql = """update account_move_line set partner_id = %s, type_document_id = (SELECT ID FROM l10n_latam_document_type where code = '00' LIMIT 1), nro_comp = '%s'
					where statement_id = %d and account_id = %d """%(str(statement.partner_id.id) if statement.partner_id else 'null',statement.name,statement.id,statement.aux_journal_id.default_account_id.id)
			self.env.cr.execute(sql)
			
		return self.env['popup.it'].get_message('Se regularizaron correctamente los registros seleccionados.')
	
	@api.onchange('journal_type')
	@api.depends('journal_type')
	def get_diarios_domains(self):
		for record in self:    
			diarios = self.env['account.journal']
			journals = []
			if record.journal_type=="bank":
						journals = self.env['account.journal'].search([('type','=',str(record.journal_type))])
			if record.journal_type=="cash" and not record.journal_check_surrender :
						journals = self.env['account.journal'].search([('type','=',str(record.journal_type))]).filtered(lambda l: not l.check_surrender)    
			if record.journal_type=="surrender":
						journals = self.env['account.journal'].search([('type','=',str('cash')),('check_surrender','=',True)])			
			for journal in journals:									
				diarios |= journal
			record.journal_domain_ids = [(6, 0, diarios.ids)]

	@api.depends('aux_journal_id')
	def _compute_journal_id(self):
		for statement in self:		
			if statement.aux_journal_id:	
				statement.journal_id  = statement.aux_journal_id.id
			else:
				statement.journal_id=False

	
	@api.onchange('balance_end')
	def _onchange_field(self):
		for i in self:
			i.balance_end_real = i.balance_end
	
	
	@api.depends('date_aux','line_ids','aux_journal_id')
	def _compute_balance_start(self):
		for stmt in self.sorted(lambda x: x.first_line_index or '0'):
			journal_id = stmt.aux_journal_id.id
			previous_line_with_statement = self.env['account.bank.statement'].search([
				('first_line_index', '<', stmt.first_line_index),
				('aux_journal_id', '=', journal_id),
			], limit=1)
			
			if previous_line_with_statement:
				balance_start = previous_line_with_statement.balance_end
			else:
				balance_start = stmt.balance_start
			#lines_in_between_domain = [
			#	('internal_index', '<', stmt.first_line_index),
			#	('journal_id', '=', journal_id),
			#	('state', '=', 'posted'),
			#]
			#if previous_line_with_statement:
			#	lines_in_between_domain.append(('internal_index', '>', previous_line_with_statement.internal_index))
				# remove lines from previous statement (when multi-editing a line already in another statement)
			#	previous_st_lines = previous_line_with_statement.statement_id.line_ids
			#	lines_in_common = previous_st_lines.filtered(lambda l: l.id in stmt.line_ids._origin.ids)
				#balance_start -= sum(lines_in_common.mapped('amount'))

			#lines_in_between = self.env['account.bank.statement.line'].search(lines_in_between_domain)
			#balance_start += sum(lines_in_between.mapped('amount'))

			stmt.balance_start = balance_start
			
	@api.model
	def create(self, vals):
		res = super(AccountBankStatement,self).create(vals)
		for i in res:
			i.lines_statement()
		return res

	def write(self, vals):
		res = super(AccountBankStatement,self).write(vals)
		for i in self:
			i.lines_statement()
		return res
	
	
	def lines_statement(self):
		for i in self:
			if not i.line_ids:					
				statement_lines = self.env['account.bank.statement.line']				
				statement_lines.sudo().create({
					'date': i.date_aux,
					'payment_ref':i.name,
					'journal_id': i.aux_journal_id.id,
					'statement_id':i.id})
			else:
				for line in i.line_ids:
					line.journal_id = i.aux_journal_id.id
			
	def view_account_move(self):
		return {
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'domain': [('id', 'in', self.line_ids.move_id.ids)],
		}
	
	def view_account_move_lines(self):     
		line = self.env['account.move.line'].search([('statement_id','=',self.id),('account_id','=',self.aux_journal_id.default_account_id.id)])
		return {
			'type': 'ir.actions.act_window',
			'view_mode': 'tree,form',
			'res_model': 'account.move.line',
			'domain': [('id', 'in', line.ids)],
		}
class AccountBankStatementLine(models.Model):
	_inherit = 'account.bank.statement.line'

	#@api.model
	#def _default_journal(self):
	#	journal_type = self.env.context.get('journal_type', False)
	#	journal_check_surrender = self.env.context.get('default_journal_check_surrender', False)
	#	company_id = self.env.company.id
	#	if journal_type:
	#		if journal_check_surrender:
	#			return self.env['account.journal'].search([
	#			('type', '=', journal_type),
	#			('check_surrender','=', journal_check_surrender),
	#			('company_id', '=', company_id)
	#		], limit=1)
	#		return self.env['account.journal'].search([
	#			('type', '=', journal_type),
	#			('company_id', '=', company_id)
	#		], limit=1)
	#	return self.env['account.journal']
	
	#journal_id = fields.Many2one('account.journal', string='Journal', required=True, states={'confirm': [('readonly', True)]}, default=_default_journal, check_company=True)
	catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago')
	type_document_id = fields.Many2one('l10n_latam.document.type',string='T.D.',copy=False)
	cash_flow_id = fields.Many2one('account.cash.flow',string='Tipo Flujo de Caja')

	def _prepare_move_line_default_vals(self, counterpart_account_id=None):
		line_vals_list = super(AccountBankStatementLine,self)._prepare_move_line_default_vals(counterpart_account_id = counterpart_account_id)
		for line in line_vals_list:
			line['cash_flow_id'] = self.cash_flow_id.id or None
			line['type_document_id'] = self.type_document_id.id or None
			line['nro_comp'] = self.ref or None
		return line_vals_list
	
	@api.model_create_multi
	def create(self, vals_list):
		st_lines = super().create(vals_list)
		for i in st_lines:		
			i.move_id.td_payment_id = i.catalog_payment_id.id
		return st_lines
	

	def reg_account_move_lines_it(self):
		for i in self:
			return i.statement_id.reg_account_move_lines_it()

		

	#def _synchronize_to_moves(self, changed_fields):
	#	res = super(AccountBankStatementLine,self)._synchronize_to_moves(changed_fields = changed_fields)
	#	for st_line in self.with_context(skip_account_move_synchronization=True):
	#		liquidity_lines, suspense_lines, other_lines = st_line._seek_for_lines()

class BankRecWidget(models.Model):
	_inherit = "bank.rec.widget"
