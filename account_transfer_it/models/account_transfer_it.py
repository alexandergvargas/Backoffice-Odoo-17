# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountTransferIT(models.Model):
	_name = 'account.transfer.it'
	_description = 'Internal Account Transfer'

	name = fields.Char(string='Nombre')
	date = fields.Date(string='Fecha', required=True)
	journal_id_origin = fields.Many2one('account.journal', string='Diario Origen', required=True)
	journal_id_destination = fields.Many2one('account.journal', string='Diario Destino', required=True)
	glosa = fields.Char(string='Glosa')
	number_origin = fields.Char(string='Número de Operación Origen')
	number_dest = fields.Char(string='Número de Operación Destino')
	currency_id = fields.Many2one('res.currency', compute='compute_currency_id', readonly=True, store=True)
	tc = fields.Float(string='Tipo de cambio', required=True,digits=(12,3),default=1)
	amount = fields.Monetary(string='Monto', required=True, currency_field='currency_id')
	amount_dest = fields.Monetary(string='Monto Destino', required=True,default=0)
	state = fields.Selection([('draft', 'Borrador'),('done', 'Publicado')], string='Estado', default='draft', required=True)
	company_id = fields.Many2one('res.company', string=u'Compañía', required=True, default=lambda self: self.env.company)
	
	move_id = fields.Many2one('account.move',string='Asiento Origen')
	move_id_dest = fields.Many2one('account.move',string='Asiento Destino')

	@api.depends('journal_id_origin','company_id')
	def compute_currency_id(self):
		for t in self:
			t.currency_id = t.journal_id_origin.currency_id.id or t.company_id.currency_id.id

	@api.model
	def create(self, vals):
		id_seq = self.env['ir.sequence'].search([('name', '=', 'Transferencias Contabilidad IT'),('company_id','=',self.env.company.id)],limit=1)

		if not id_seq:
			id_seq = self.env['ir.sequence'].create({'name': 'Transferencias Contabilidad IT', 'company_id': self.env.company.id, 'implementation': 'no_gap','active': True, 'prefix': 'TF-', 'padding': 6, 'number_increment': 1, 'number_next_actual': 1})

		vals['name'] = id_seq._next()
		t = super(AccountTransferIT, self).create(vals)
		return t

	@api.onchange('date')
	def on_change_date(self):
		if self.date:
			usd = self.env.ref('base.USD')
			divisa_line = self.env['res.currency.rate'].search([('name','=',self.date),('currency_id','=',usd.id)],limit=1)
			if divisa_line:
				self.tc = divisa_line.sale_type

	def unlink(self):
		for transf in self:
			if transf.state in ('done'):
				raise UserError("No puede eliminar una Transferencias que esta Publicada.")
		return super(AccountTransferIT, self).unlink()

	def action_draft(self):
		if self.move_id:
			account = self.move_id
			if self.move_id.state =='draft':
				pass
			else:
				self.move_id=False
				for mm in account.line_ids:
					mm.remove_move_reconcile()
				account.button_cancel()
			account.line_ids.unlink()
			account.vou_number = "/"
			account.unlink()

		if self.move_id_dest:
			account = self.move_id_dest
			if self.move_id_dest.state =='draft':
				pass
			else:
				self.move_id_dest=False
				for mm in account.line_ids:
					mm.remove_move_reconcile()
				account.button_cancel()
			account.line_ids.unlink()
			account.vou_number = "/"
			account.unlink()
		self.state = 'draft'
	
	@api.onchange('journal_id_destination','currency_id','amount','tc')
	def onchange_amount_dest(self):
		for t in self:
			amount_dest = 0
			if t.currency_id == (t.journal_id_destination.currency_id or t.company_id.currency_id):
				amount_dest = t.amount
			else:
				if t.currency_id == t.company_id.currency_id:
					amount_dest = t.amount / t.tc
				else:
					amount_dest = t.amount * t.tc
			t.amount_dest = amount_dest
		
		
	def action_post(self):
		if self.currency_id == self.company_id.currency_id:
			amount_pen = self.amount
		else:
			amount_pen = self.amount * self.tc

		transfer_ext = False

		if self.currency_id != self.company_id.currency_id and ((self.journal_id_destination.currency_id or self.company_id.currency_id) != self.company_id.currency_id):
			transfer_ext = True
		lineas = []
		doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1).id
		vals = (0,0,{
			'account_id': self.company_id.transfer_account_id.id,
			'type_document_id': doc,
			'nro_comp': self.number_origin,
			'name': self.number_origin,
			'currency_id': self.journal_id_destination.currency_id.id or self.company_id.currency_id.id,
			'amount_currency': self.amount_dest,
			'debit': amount_pen,
			'credit':0,
			'company_id': self.company_id.id,
			'tc': self.tc
		})
		lineas.append(vals)

		vals = (0,0,{
			'account_id': self.company_id.account_journal_payment_credit_account_id.id,
			'type_document_id': doc,
			'nro_comp': self.number_origin,
			'name': self.number_origin,
			'currency_id': self.journal_id_origin.currency_id.id or self.company_id.currency_id.id if transfer_ext else self.company_id.currency_id.id,
			'amount_currency': self.amount*-1 if transfer_ext else -amount_pen,
			'debit': 0,
			'credit':amount_pen,
			'company_id': self.company_id.id,
			'tc': self.tc
		})
		lineas.append(vals)

		data = {
			'company_id': self.company_id.id,
			'journal_id': self.journal_id_origin.id,
			'date': self.date,
			'line_ids':lineas,
			'ref': self.number_origin,
			'glosa':self.glosa,
			'move_type':'entry',
			'currency_rate':self.tc
		}
		move_id = self.env['account.move'].create(data)
		move_id._post()
		self.move_id = move_id.id

		###########################################################################################

		lineas = []
		vals = (0,0,{
			'account_id': self.company_id.transfer_account_id.id,
			'type_document_id': doc,
			'nro_comp': self.number_dest,
			'name': self.number_dest,
			'currency_id': self.journal_id_destination.currency_id.id or self.company_id.currency_id.id,
			'amount_currency': self.amount_dest*-1,
			'debit': 0,
			'credit':amount_pen,
			'company_id': self.company_id.id,
			'tc': self.tc
		})
		lineas.append(vals)

		vals = (0,0,{
			'account_id': self.company_id.account_journal_payment_debit_account_id.id,
			'type_document_id': doc,
			'nro_comp': self.number_dest,
			'name': self.number_dest,
			'currency_id': self.journal_id_origin.currency_id.id or self.company_id.currency_id.id if transfer_ext else self.company_id.currency_id.id,
			'amount_currency': self.amount_dest if transfer_ext else amount_pen,
			'debit': amount_pen,
			'credit':0,
			'company_id': self.company_id.id,
			'tc': self.tc
		})
		lineas.append(vals)

		data = {
			'company_id': self.company_id.id,
			'journal_id': self.journal_id_destination.id,
			'date': self.date,
			'line_ids':lineas,
			'ref': self.number_dest,
			'glosa':self.glosa,
			'move_type':'entry',
			'currency_rate':self.tc
		}
		move_id = self.env['account.move'].create(data)
		move_id._post()
		self.move_id_dest = move_id.id

		self.state = 'done'

	def open_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		domain = [('id', 'in', [self.move_id.id,self.move_id_dest.id])]
		context = dict(self.env.context)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)