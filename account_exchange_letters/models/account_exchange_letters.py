# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountExchangeLetters(models.Model):
	_name = 'account.exchange.letters'
	_description = 'Account Exchange Letters'
	_inherit = ['mail.thread']

	name = fields.Char(string='Nombre')
	currency_id = fields.Many2one('res.currency',string='Moneda',default=lambda self: self.env.company.currency_id)
	date = fields.Date(string='Fecha de canje')
	glosa = fields.Char(string='Glosa')
	tc = fields.Float(string='Tipo Cambio',digits=(12,3),default=1)
	payment_term_id = fields.Many2one(comodel_name='account.payment.term',string=u'Términos de Pago', required=True)
	partner_id = fields.Many2one('res.partner',string='Partner', required=True)

	invoice_ids = fields.One2many('account.exchange.letters.line','main_id',string='Facturas')
	lines_ids = fields.One2many('account.exchange.letters.line2','main_id',string='Letras')

	state = fields.Selection([('draft','Borrador'),('done','Finalizado')],string='Estado',default='draft')
	move_id = fields.Many2one('account.move',string='Asiento Contable')
	type = fields.Selection([('asset_receivable','Por Cobrar'),('liability_payable','Por Pagar')],string=u'Tipo')
	amount = fields.Float(string='Monto',compute='compute_amount_cash',store=True)

	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	@api.depends('company_id','move_id','move_id.line_ids','lines_ids.is_account_cash')
	def compute_amount_cash(self):
		for m in self:
			amount = 0
			if m.move_id:
				line_cash = m.lines_ids.filtered(lambda l: l.is_account_cash)
				for i in m.move_id.line_ids.filtered(lambda l: l.account_id.id in line_cash.account_id.ids):
					amount += (i.debit - i.credit)
			
			m.amount = amount

	@api.model
	def create(self, vals):
		id_seq = self.env['ir.sequence'].search([('name','=','Canje de Letra Por Cobrar'),('company_id','=',self.env.company.id)], limit=1)
		if self.env.context.get('default_type') == 'asset_receivable':
			id_seq = self.env['ir.sequence'].search([('name','=','Canje de Letra Por Cobrar'),('company_id','=',self.env.company.id)], limit=1)
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Canje de Letra Por Cobrar','company_id': self.env.company.id,'implementation':'no_gap','active':True,'prefix':'CLC-','padding':5,'number_increment':1,'number_next_actual' :1})
		
		if self.env.context.get('default_type') == 'liability_payable':
			id_seq = self.env['ir.sequence'].search([('name','=','Canje de Letra Por Pagar'),('company_id','=',self.env.company.id)], limit=1)
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Canje de Letra Por Pagar','company_id': self.env.company.id,'implementation':'no_gap','active':True,'prefix':'CLP-','padding':5,'number_increment':1,'number_next_actual' :1})

		vals['name'] = id_seq._next()
		t = super(AccountExchangeLetters, self).create(vals)
		return t
	def calculate_line_receivable_portfolio(self):
		param = self.env['account.exchange.letters.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if (self.currency_id == self.company_id.currency_id ) and not param.account_receivable_portfolio_mn:
			raise UserError(u'La moneda del canje es %s y no esta configurada la "Cuenta de Letras en Cartera MN" en los parámetros de Canje de Letras de la Compañía'%self.currency_id.name)
		if (self.currency_id != self.company_id.currency_id ) and not param.account_receivable_portfolio_me:
			raise UserError(u'La moneda del canje es %s y no esta configurada la "Cuenta de Letras en Cartera ME" en los parámetros de Canje de Letras de la Compañía'%self.currency_id.name)
		self.calculate_line(param.account_receivable_portfolio_mn if self.currency_id == self.company_id.currency_id else param.account_receivable_portfolio_me,'Canje de Letra', True)

	def calculate_line_receivable_collection(self):
		param = self.env['account.exchange.letters.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if (self.currency_id == self.company_id.currency_id ) and not param.account_receivable_collection_mn:
			raise UserError(u'La moneda del canje es %s y no esta configurada la "Cuenta de Letras en Cobranza MN" en los parámetros de Canje de Letras de la Compañía'%self.currency_id.name)
		if (self.currency_id != self.company_id.currency_id ) and not param.account_receivable_collection_me:
			raise UserError(u'La moneda del canje es %s y no esta configurada la "Cuenta de Letras en Cobranza ME" en los parámetros de Canje de Letras de la Compañía'%self.currency_id.name)
		self.calculate_line(param.account_receivable_collection_mn if self.currency_id == self.company_id.currency_id else param.account_receivable_collection_me,'Pase a cobranza')

	def calculate_line_receivable_discount(self):
		param = self.env['account.exchange.letters.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if (self.currency_id == self.company_id.currency_id ) and not param.account_receivable_discount_mn:
			raise UserError(u'La moneda del canje es %s y no esta configurada la "Cuenta de Letras en Descuento MN" en los parámetros de Canje de Letras de la Compañía'%self.currency_id.name)
		if (self.currency_id != self.company_id.currency_id ) and not param.account_receivable_discount_me:
			raise UserError(u'La moneda del canje es %s y no esta configurada la "Cuenta de Letras en Descuento ME" en los parámetros de Canje de Letras de la Compañía'%self.currency_id.name)
		self.calculate_line(param.account_receivable_discount_mn if self.currency_id == self.company_id.currency_id else param.account_receivable_discount_me, 'Pase a descuento')

	def calculate_line_payable(self):
		param = self.env['account.exchange.letters.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if (self.currency_id == self.company_id.currency_id ) and not param.account_payable_mn:
			raise UserError(u'La moneda del canje es %s y no esta configurada la "Cuenta de Letras por Pagar MN" en los parámetros de Canje de Letras de la Compañía'%self.currency_id.name)
		if (self.currency_id != self.company_id.currency_id ) and not param.account_payable_me:
			raise UserError(u'La moneda del canje es %s y no esta configurada la "Cuenta de Letras por Pagar ME" en los parámetros de Canje de Letras de la Compañía'%self.currency_id.name)
		self.calculate_line(param.account_payable_mn if self.currency_id == self.company_id.currency_id else param.account_payable_me,'Canje de letra',True)

	def calculate_line(self,account_id,label,use_terms=False):
		param = self.env['account.exchange.letters.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		self.lines_ids.unlink()
		amount = 0
		for line_i in self.invoice_ids:
			amount += line_i.debe
			amount -= line_i.haber
		
		for line_c in self.lines_ids:
			amount += line_c.debe
			amount -= line_c.haber
		amount_currency = (amount/self.tc) if self.currency_id != self.company_id.currency_id else amount
		vals = []
		if use_terms:
			terms = self.payment_term_id._compute_terms(
						date_ref=self.date or fields.Date.context_today(self),
						currency=self.currency_id,
						company=self.env.company,
						tax_amount=0,
						tax_amount_currency=0,
						untaxed_amount=amount*-1,
						untaxed_amount_currency=amount_currency*-1,
						sign=1)
			#raise UserError('Balance '+str(amount) +' Monto Moneda '+ str(amount_currency)+ '\n'+str(terms))
			
			for term in terms['line_ids']:
				val = {
					'main_id': self.id,
					'name': label,
					'account_id': account_id.id,
					'currency_id': self.currency_id.id if self.currency_id else self.company_id.currency_id.id,
					'importe_divisa': term['foreign_amount'],
					'debe':term['company_amount'] if term['company_amount']>0 else 0,
					'haber': 0 if term['company_amount']>0 else abs(term['company_amount']),
					'is_account_cash' : True,
					'type_document_id': param.letter_document_type.id,
					'fecha_vencimiento': term['date'],
					'cta_cte_origen': True
				}
				vals.append(val)
		else:
			for line in self.invoice_ids:						
				val = {
						'main_id': self.id,
						'name': label,
						'account_id': account_id.id,
						'type_document_id': line.tipo_documento.id,
						'currency_id': account_id.currency_id.id if account_id.currency_id else self.company_id.currency_id.id,
						'nro_comp':line.invoice_id.nro_comp,
						'importe_divisa': line.importe_divisa*-1,	
						'debe':line.haber,
						'haber': line.debe,
						'is_account_cash' : True,								
						'fecha_vencimiento':line.fecha_vencimiento,													
						'cta_cte_origen':True
						}
				vals.append(val)
		self.env['account.exchange.letters.line2'].create(vals)
	
	def autocomplete_amount(self):
		for line_i in self.invoice_ids:
			line_i.importe_divisa = line_i.saldo * -1
			line_i._update_debit_credit()

	def get_invoices_letters(self):
		wizard = self.env['get.invoices.letters.wizard'].create({
			'letters_id': self.id,
			'company_id':self.company_id.id,
			'type_selection': self.type
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_get_invoices_letters_wizard' % module)
		return {
			'name':u'Seleccionar Documentos',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'get.invoices.letters.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
	
	@api.onchange('date')
	def on_change_date(self):
		if self.date:
			usd = self.env.ref('base.USD')
			divisa_line = self.env['res.currency.rate'].search([('name','=',self.date),('currency_id','=',usd.id)],limit=1)
			if divisa_line:
				self.tc = divisa_line.sale_type

	@api.onchange('tc')
	def on_change_tc(self):
		if self.tc:
			for i in self.invoice_ids:
				i._update_debit_credit()
	
	def update_saldo(self):
		for inv in self.invoice_ids:
			inv.on_change_invoice_id()

	def crear_asiento(self):
		self.update_saldo()
		prob, problemas = self.validate_lines()
		if prob:
			return self.env['popup.it'].get_message(problemas)
		lineas = []

		for elemnt in self.invoice_ids:
			vals = (0,0,{
				'account_id': elemnt.account_id.id,
				'partner_id':self.partner_id.id,
				'type_document_id':elemnt.tipo_documento.id,
				'nro_comp': elemnt.invoice_id.nro_comp,
				'name': self.glosa,
				'currency_id': elemnt.currency_id.id,
				'amount_currency': elemnt.importe_divisa if elemnt.currency_id else 0,
				'debit': elemnt.debe,
				'credit': elemnt.haber,
				'date_maturity':elemnt.fecha_vencimiento,
				'company_id': self.company_id.id,
				'reconciled':False,
				'tc': self.tc
			})
			lineas.append(vals)

		param = self.env['account.exchange.letters.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if self.type == 'asset_receivable' and not param.serie_id:
			raise UserError(u'No esta configurado el parámetro "Serie para Cuentas por Cobrar."')

		for i in self.lines_ids:
			if not i.nro_comp:
				i.update({'nro_comp': param.serie_id.sequence_id._next()})
				i.update({'name': i.name + ' ' + i.nro_comp})
			vals = (0,0,{
					'account_id': i.account_id.id,
					'partner_id': self.partner_id.id,
					'type_document_id': i.type_document_id.id if i.type_document_id else None,
					'nro_comp': i.nro_comp,
					'name': i.name if i.name else self.glosa,
					'currency_id': i.currency_id.id,
					'amount_currency': i.importe_divisa if i.currency_id else 0,
					'debit': i.debe,
					'credit': i.haber,
					'date_maturity':i.fecha_vencimiento,
					'company_id': self.company_id.id,
					'reconciled':False,
					'tc': self.tc,
					'cta_cte_origen': i.cta_cte_origen,
					'invoice_date_it':self.date,
				})
			lineas.append(vals)
		
		if self.type == 'asset_receivable' and not param.exchange_diary_receivable_letters:
			raise UserError(u'No esta configurado el parámetro "Diario de Canje de Letras por Cobrar"')
		if self.type == 'liability_payable' and not param.exchange_diary_payable_letters:
			raise UserError(u'No esta configurado el parámetro "Diario de Canje de Letras por Pagar"')
		journal_id = param.exchange_diary_receivable_letters if self.type == 'asset_receivable' else param.exchange_diary_payable_letters
		data = {
			'company_id': self.company_id.id,
			'journal_id': journal_id.id,
			'date': self.date,
			'invoice_date': self.date,
			'line_ids':lineas,
			'ref': self.name,
			'glosa':self.glosa,
			'move_type':'entry',
			'currency_rate':self.tc
		}

		move_id = self.env['account.move'].create(data)
		move_id._post()
		self.move_id = move_id.id
		self.move_id._compute_amount()
		for c,elemnt in enumerate(self.invoice_ids):
			self.env['account.move.line'].browse([move_id.line_ids[c].id,self.invoice_ids[c].invoice_id.id]).reconcile()

		self.state = 'done'

	def cancelar(self):
		if self.move_id.id:
			account = self.move_id
			self.move_id.letters_id = False 
			if self.move_id.state =='draft':
				pass
			else:
				self.move_id=False
				for mm in account.line_ids:
					mm.remove_move_reconcile()
				account.button_cancel()
			account.line_ids.unlink()
			account.vou_number = "/"
			account.name = "/"
			account.unlink()
		self.state = 'draft'

	def unlink(self):
		for multi in self:
			if multi.state in ('done'):
				raise UserError("No puede eliminar un Canje de Letras que esta Finalizado")
		return super(AccountExchangeLetters, self).unlink()
	
	def validate_lines(self):
		self.env.cr.execute("""SELECT nro_comp FROM account_move_line WHERE id in (
								SELECT invoice_id FROM multipayment_advance_it_line WHERE main_id = %d
								GROUP BY invoice_id
								HAVING count(invoice_id)>1)"""%(self.id))

		res = self.env.cr.dictfetchall()
		prob = False
		problemas = ""
		if len(res)>0:
			prob = True
			problemas += "LOS SIGUIENTES COMPROBANTES ESTAN DUPLICADOS EN LAS LINEAS DE PAGOS MULTIPLES: \n"
			for line in res:
				problemas += "• " + line['nro_comp'] + '\n'

		self.env.cr.execute("""select aml.nro_comp from multipayment_advance_it_line l
								left join account_move_line aml on aml.id = l.invoice_id
								where ((l.saldo<0 and (l.saldo)*-1 < l.importe_divisa ) or (l.saldo>0 and l.saldo < (l.importe_divisa)*-1))
								and l.main_id = %d"""%(self.id))

		res2 = self.env.cr.dictfetchall()
		if len(res2)>0:
			prob = True
			problemas += "LOS SIGUIENTES COMPROBANTES EXCEDEN EN MONTO DIVISA AL SALDO: \n"
			for line in res2:
				problemas += "• " + line['nro_comp'] + '\n'
		return prob, problemas

class AccountExchangeLettersLine(models.Model):
	_name = 'account.exchange.letters.line'

	main_id = fields.Many2one('account.exchange.letters')
	tipo_documento = fields.Many2one('l10n_latam.document.type',string='Tipo de Documento')	
	invoice_id = fields.Many2one('account.move.line',string='Factura')
	account_id = fields.Many2one('account.account',string='Cuenta',related='invoice_id.account_id')
	currency_id = fields.Many2one('res.currency',string='Moneda',related='invoice_id.currency_id')
	fecha_vencimiento = fields.Date(string='Fecha Vencimiento',related='invoice_id.date_maturity')
	saldo = fields.Monetary(string='Saldo')
	importe_divisa = fields.Float(string='Importe Divisa',digits=(12,2))
	debe = fields.Float(string='Debe',digits=(12,2),default=0)
	haber = fields.Float(string='Haber',digits=(12,2),default=0)

	@api.onchange('invoice_id')
	def on_change_invoice_id(self):
		if self.invoice_id:
			residual_amount = 0
			if self.invoice_id.currency_id:
				residual_amount = self.invoice_id.amount_residual_currency
			else:
				residual_amount = self.invoice_id.amount_residual
			self.saldo = residual_amount

	@api.onchange('importe_divisa')
	def _update_debit_credit(self):
		if self.importe_divisa:
			if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
				self.debe = self.importe_divisa * self.main_id.tc if self.importe_divisa > 0 else 0
				self.haber = 0 if self.importe_divisa > 0 else abs(self.importe_divisa * self.main_id.tc)
			else:
				self.debe = self.importe_divisa if self.importe_divisa > 0 else 0
				self.haber = 0 if self.importe_divisa > 0 else abs(self.importe_divisa)

class AccountExchangeLettersLine2(models.Model):
	_name = 'account.exchange.letters.line2'

	main_id = fields.Many2one('account.exchange.letters')
	name = fields.Char(string=u'Descripción')
	account_id = fields.Many2one('account.account',string='Cuenta')
	currency_id = fields.Many2one('res.currency',string='Moneda',default=lambda self: self.env.company.currency_id)
	importe_divisa = fields.Float(string='Importe Divisa',digits=(12,2),default=0)
	type_document_id = fields.Many2one('l10n_latam.document.type',string='Tipo de Documento')
	nro_comp = fields.Char(string='Nro Comprobante')
	debe = fields.Float(string='Debe',digits=(12,2))
	haber = fields.Float(string='Haber',digits=(12,2))
	fecha_vencimiento = fields.Date(string='Fecha Vencimiento')
	cta_cte_origen = fields.Boolean(string=u'Es cta cte Origen',default=False)
	is_account_cash = fields.Boolean(string='Cuenta de Caja',default=False)

	@api.onchange('account_id')
	def change_account_id(self):
		for line in self:
			if line.account_id.currency_id:
				line.currency_id = line.account_id.currency_id.id

	@api.onchange('importe_divisa','currency_id')
	def _update_debit_credit(self):
		if self.importe_divisa:
			if self.currency_id and self.currency_id != self.main_id.company_id.currency_id:
				self.debe = self.importe_divisa * self.main_id.tc if self.importe_divisa > 0 else 0
				self.haber = 0 if self.importe_divisa > 0 else abs(self.importe_divisa * self.main_id.tc)
			else:
				self.debe = self.importe_divisa if self.importe_divisa > 0 else 0
				self.haber = 0 if self.importe_divisa > 0 else abs(self.importe_divisa)
