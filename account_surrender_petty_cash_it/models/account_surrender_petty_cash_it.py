# -*- coding: utf-8 -*-

from mimetypes import init
from string import digits
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError

class AccountSurrenderPettyCashIt(models.Model):
	_name = 'account.surrender.petty.cash.it'
	_inherit = ['mail.thread']

	name = fields.Char(string=u'Descripción',default=u'/')
	type_surrender = fields.Selection([('surrender','Entregas a rendir'),('petty_cash','Caja Chica')],string='Tipo')
	employee_id = fields.Many2one('res.partner',string='Empleado')
	journal_id = fields.Many2one('account.journal',string=u'Diario')
	currency_id = fields.Many2one('res.currency',string='Moneda', compute="_compute_currency_id", readonly=True)
	glosa = fields.Char(string="Motivo")

	total_income = fields.Float(string="Ingresos",compute="compute_total_income",store=True)
	total_outcome = fields.Float(string="Salidas",compute="compute_total_outcome",store=True)
	total_balance = fields.Float(string="Saldo",compute="compute_total_balance",store=True) 

	invoice_ids = fields.One2many('account.surrender.invoice.line','surrender_id',string='Facturas')
	delivery_ids = fields.One2many('account.surrender.line', 'surrender_id', string="Entregas", copy=False, domain=[('type', '=', 'delivery')])
	returns_ids = fields.One2many('account.surrender.line', 'surrender_id', string="Devoluciones", copy=False, domain=[('type', '=', 'returns')])

	state = fields.Selection([('draft', 'Borrador'), ('progress', 'Procesando'),('done', 'Validado')], string='Estado', default='draft')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

	@api.depends('journal_id','journal_id.currency_id')
	def _compute_currency_id(self):
		for record in self:
			record.currency_id = record.journal_id.currency_id.id if record.journal_id.currency_id else record.company_id.currency_id.id

	@api.depends('delivery_ids', 'currency_id','state')
	def compute_total_income(self):
		for record in self:
			if record.state != 'draft':
				debit_values = record.delivery_ids.filtered(lambda l: l.currency_id.id).mapped('amount_real')
				record.total_income = sum(debit_values)
			else:
				record.total_income = 0
	
	@api.depends('returns_ids', 'currency_id','invoice_ids','state')
	def compute_total_outcome(self):
		for record in self:
			if record.state != 'draft':
				credit_line = record.invoice_ids.filtered(lambda l: l.currency_id.id).mapped('amount_real')
				credit_return = record.returns_ids.filtered(lambda l: l.currency_id.id).mapped('amount_real')
				record.total_outcome = sum(credit_return) + sum(credit_line)
			else:
				record.total_outcome = 0

	@api.depends('total_income','total_outcome','state')
	def compute_total_balance(self):
		for record in self:
			if record.state != 'draft':
				record.total_balance = record.total_income - record.total_outcome
			else:
				record.total_balance = 0

	@api.model
	def create(self,vals):
		if vals['type_surrender'] == 'surrender':
			id_seq = self.env['ir.sequence'].search([('name','=','Entregas a Rendir Avanzadas'),('company_id','=',self.env.company.id)], limit=1)
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Entregas a Rendir Avanzadas',
				'implementation':'no_gap',
				'active':True,
				'prefix':'REN-',
				'padding':6,
				'number_increment':1,
				'number_next_actual' :1,
				'company_id':self.env.company.id})
		else:
			id_seq = self.env['ir.sequence'].search([('name','=','Cajas Chicas Avanzadas'),('company_id','=',self.env.company.id)], limit=1)
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Cajas Chicas Avanzadas',
				'implementation':'no_gap',
				'active':True,
				'prefix':'CCH-',
				'padding':6,
				'number_increment':1,
				'number_next_actual' :1,
				'company_id':self.env.company.id})

		vals['name'] = id_seq._next()
		t = super(AccountSurrenderPettyCashIt,self).create(vals)
		return t
	
	def action_post(self):
		wizard = self.env['post.surrender.petty.cash.wizard'].create({
			'spt_id': self.id,
			'company_id':self.company_id.id
		})
		view = self.env.ref('account_surrender_petty_cash_it.view_post_surrender_petty_cash_wizard')
		return {
			'name':u'Publicar',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'post.surrender.petty.cash.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
	
	def action_import_invoices(self):
		wizard = self.env['import.surrender.invoice.line.wizard'].create({
			'spt_id':self.id
			})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_import_surrender_invoice_line_wizard_form' % module)
		return {
			'name':u'Importar Facturas',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'import.surrender.invoice.line.wizard',
			'view_id': view.id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
	
	def action_import_deliverys(self):
		wizard = self.env['import.surrender.line.wizard'].create({
			'spt_id':self.id,
			'type':'delivery'
			})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_import_surrender_line_wizard_form' % module)
		return {
			'name':u'Importar Entregas',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'import.surrender.line.wizard',
			'view_id': view.id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
	
	def action_import_returns(self):
		wizard = self.env['import.surrender.line.wizard'].create({
			'spt_id':self.id,
			'type':'returns'
			})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_import_surrender_line_wizard_form' % module)
		return {
			'name':u'Importar Entregas',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'import.surrender.line.wizard',
			'view_id': view.id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def libray_account(self,lines):
		data = 	{
			'journal_id': lines.journal_id.id,
			'ref':(lines.nro_comp if lines.nro_comp else ''),
			'date': lines.date,
			'invoice_date': lines.date,
			'company_id': lines.surrender_id.company_id.id,
			'glosa': (lines.glosa if lines.glosa else ''),
			'currency_rate': lines.tc,
			'move_type':'entry',
		}
		return data
	
	def create_accounts(self,lines):
		for i in self:
			debit = 0
			credit = 0
			if not i.journal_id.account_multipayment_id:
				raise UserError(u'No esta configurada la Cuenta para PM en el Diario "%s"'%i.journal_id.name)
			id_account = i.journal_id.account_multipayment_id.id

			if lines.move_id:
				lines.move_id.button_draft()
				lines.move_id.name = '/'
				lines.move_id.posted_before = False
				lines.move_id.unlink()

			if lines.type == 'delivery':
				debit = 0
				credit = lines.amount*lines.tc if lines.currency_id.id != i.company_id.currency_id.id else lines.amount
				amount_currency = lines.amount*-1
			else:
				debit = lines.amount*lines.tc if lines.currency_id.id != i.company_id.currency_id.id else lines.amount
				credit = 0
				amount_currency = lines.amount
			

			data = i.libray_account(lines)
				
			move_lines = []
			doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)				
			line_cc = (0,0,{
						'account_id': i.company_id.account_journal_payment_credit_account_id.id if lines.type == 'delivery' else i.company_id.account_journal_payment_debit_account_id.id,
						'debit': debit,
						'credit':credit,
						'name':'ENTREGA %s'%i.name,
						'partner_id': i.employee_id.id,
						'company_id': i.company_id.id,		
						'nro_comp': lines.nro_comp,
						'type_document_id': doc.id,
						'currency_id': lines.currency_id.id,
						'amount_currency':amount_currency,
						'tc': lines.tc
						})
			move_lines.append(line_cc)
					#Lineas
			if lines.type == 'delivery':
				debit = lines.amount*lines.tc if lines.currency_id.id != i.company_id.currency_id.id else lines.amount
				credit = 0
				amount_currency = lines.amount
			else:
				debit = 0
				credit = lines.amount*lines.tc if lines.currency_id.id != i.company_id.currency_id.id else lines.amount
				amount_currency = lines.amount*-1

			line_cc = (0,0,{
						'account_id': id_account,
						'debit': debit,
						'credit':credit,
						'name':'ENTREGA %s'%i.name,
						'partner_id': i.employee_id.id,
						'nro_comp': i.name,
						'type_document_id': doc.id,
						'company_id': i.company_id.id,		
						'currency_id': lines.currency_id.id,
						'amount_currency':amount_currency,
						'tc': lines.tc
						})
			move_lines.append(line_cc)
			#cuentas 						

			data['line_ids'] = move_lines
			tt = self.env['account.move'].create(data)
			lines.move_id=tt.id
			tt._post()

	def apply_all(self):
		for i in self:
			i.create_invoices_and_payments()
			i.create_accounts_delivery()
			i.create_accounts_returns()

	def create_accounts_delivery(self):
		for i in self:
			nro = 0
			for deliverys in i.delivery_ids:
				nro+=1				
				i.validate_fields(nro,deliverys)
				i.create_accounts(deliverys)
	
	def create_accounts_returns(self):
		for i in self:
			nro = 0
			for returns in i.returns_ids:				
				nro+=1				
				i.validate_fields(nro,returns)
				i.create_accounts(returns)
	
	def validate_fields(self,nro,lines):
		if not lines.date:
			raise UserError(_('Por favor seleccione una fecha para la línea %d.')% (nro))
		if not lines.journal_id:
			raise UserError(_('Por favor seleccione un diario para la línea %d.')% (nro))
		if not lines.amount:
			raise UserError(_('El monto no puede ser cero en la linea %d.')%(nro))
		if not self.company_id.account_journal_payment_credit_account_id:
			raise UserError(_(u'No esta configurada la cuenta de pagos pendientes en los AJUSTES DE CONTABILIDAD'))
		if not self.company_id.account_journal_payment_debit_account_id:
			raise UserError(_(u'No esta configurada la cuenta de cobros pendientes en los AJUSTES DE CONTABILIDAD'))

	def create_accounts_payment(self):
		for elemnt in self:
			invoice_moves = []
			for invo in elemnt.invoice_ids.filtered(lambda l: l.invoice_id):
				if invo.invoice_id.id not in invoice_moves:
					invoice_moves.append(invo.invoice_id.id)
			for invoice in self.env['account.move'].search([('id','in',invoice_moves)]):
				lineas = []
				filtered_line = invoice.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable','liability_payable'))
				vals = (0,0,{
					'account_id': filtered_line.account_id.id,
					'partner_id':filtered_line.partner_id.id,
					'type_document_id':filtered_line.type_document_id.id,
					'nro_comp': filtered_line.nro_comp,
					'name': elemnt.glosa,
					'currency_id': filtered_line.currency_id.id,
					'amount_currency': filtered_line.amount_currency*-1,
					'debit': filtered_line.credit,
					'credit': filtered_line.debit,
					'date_maturity':filtered_line.date_maturity,
					'company_id': elemnt.company_id.id,
					'reconciled':False,
					'tc': filtered_line.tc
				})
				lineas.append(vals)
				doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)
				if not elemnt.journal_id.account_multipayment_id:
					raise UserError(u'No esta configurada la Cuenta para PM en el Diario "%s"'%elemnt.journal_id.name)
				vals = (0,0,{
						'account_id': elemnt.journal_id.account_multipayment_id.id,
						'partner_id': elemnt.employee_id.id,
						'type_document_id': doc.id,
						'nro_comp': elemnt.name,
						'name': elemnt.glosa,
						'currency_id': elemnt.company_id.currency_id.id,
						'amount_currency': filtered_line.credit*-1,
						'debit': 0,
						'credit': filtered_line.credit,
						'company_id': elemnt.company_id.id,
						'reconciled':False,
						'tc': filtered_line.tc,
						'invoice_date_it':fields.Date.today()
					})
				lineas.append(vals)
				#raise UserError(str(lineas))
				data = {
					'company_id': elemnt.company_id.id,
					'partner_id': elemnt.employee_id.id,
					'l10n_latam_document_type_id': doc.id,
					'journal_id': elemnt.journal_id.id,
					'date': invoice.date,
					'invoice_date': invoice.date,
					'line_ids':lineas,
					'ref': elemnt.name,
					'glosa':elemnt.glosa,
					'move_type':'entry',
					'currency_rate':filtered_line.tc
				}

				move_id = self.env['account.move'].create(data)
				
				move_id._post()

				#move_id._compute_amount()
				self.env['account.move.line'].browse([move_id.line_ids[0].id,filtered_line.id]).reconcile()

				lines = elemnt.invoice_ids.filtered(lambda l: l.invoice_id.id == invoice.id)
				lines.move_id = move_id.id

	def create_invoices_and_payments(self):
		for i in self:
			if not i.employee_id:
				raise UserError(u'Falta asignar Empleado')
			if not i.glosa:
				raise UserError(u'Falta asignar Motivo')
			i.create_invoices()
			i.create_accounts_payment()
	
	def unlink(self):
		for i in self:
			if i.state != 'draft':
				raise UserError(u"La Rendición no puede ser eliminada porque esta Validada")			
			return super(AccountSurrenderPettyCashIt,i).unlink()
		
	def action_return(self):
		if self.state == 'done':
			self.state = 'progress'
		elif self.state == 'progress':
			have_move = False
			for invoice in self.invoice_ids:
				if invoice.invoice_id or invoice.move_id:
					have_move = True
			for delivery in self.delivery_ids:
				if delivery.move_id:
					have_move = True
			for objreturn in self.returns_ids:
				if objreturn.move_id:
					have_move = True
			if have_move:
				raise UserError(u'Existen facturas/asientos relacionados a la Rendición/Caja Chica')
			self.state = 'draft'

	def action_progress(self):
		self.state = 'progress'
	
	def action_done(self):
		self.state = 'done'
	
	def create_invoices(self):
		m = self.env['render.main.parameter'].sudo().search([('company_id','=',self.company_id.id)],limit=1)
		if self.type_surrender  == 'surrender':
			if not m.invoice_surrender_journal_id:
				raise UserError('No esta configurado el Diario para compras pagadas con rendiciones y reembolsos en los parametros de rendiciones de la Compañía.')
			invoice_journal_id = m.invoice_surrender_journal_id
		
		else:
			if not m.invoice_petty_cash_journal_id:
				raise UserError('No esta configurado el Diario para compras pagadas con caja chica en los parametros de rendiciones de la Compañía.')
			invoice_journal_id = m.invoice_petty_cash_journal_id

		invoice_obj = self.env['account.move']
		for inv in self.invoice_ids:
			if not inv.invoice_id:
				if ((not inv.tc) or inv.tc in (0,1)) and inv.currency_id.id != self.company_id.currency_id.id:
					raise UserError(u'Si esta usando una moneda extranjera, es necesario establecer el Tipo de Cambio.')
				invoice = invoice_obj.search([
					('move_type', '=', 'in_invoice'),
					('partner_id','=',inv.partner_id.id),
					('l10n_latam_document_type_id','=',inv.type_document_id.id),
					('nro_comp','=',inv.nro_comp),
					('invoice_date','=',inv.invoice_date),
					('company_id','=',self.company_id.id)
				],limit=1)
				
				if not invoice:
					value_inv_arr = {
					'partner_id' : inv.partner_id.id,
					'currency_id' : inv.currency_id.id,
					'invoice_user_id':self.env.uid,
					'move_type' : 'in_invoice',
					'date':inv.date,
					'invoice_date':inv.invoice_date,
					'invoice_date_due': inv.invoice_date_due,
					'journal_id' : invoice_journal_id.id,
					'l10n_latam_document_type_id' : inv.type_document_id.id,
					'nro_comp' : inv.nro_comp,
					'glosa': inv.name,
					'company_id' : self.company_id.id,
					'currency_rate': inv.tc,
					}
					if inv.invoice_date != inv.invoice_date_due:
						value_inv_arr['invoice_payment_term_id'] = None
					invoice = invoice_obj.create(value_inv_arr)
					invoice._get_currency_rate()

				###Add invoice line
				if inv.product_id.property_account_expense_id:
					account = inv.product_id.property_account_expense_id
				elif inv.product_id.categ_id.property_account_expense_categ_id:
					account = inv.product_id.categ_id.property_account_expense_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id'),('company_id','=',self.company_id.id)],limit=1)
					account = account_search.value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(account)
				
				if not inv.account_id:
					raise UserError(u'La cuenta es obligatoria.')
				
				vals = {
					'product_id' : inv.product_id.id,
					'quantity' : 1,
					'price_unit' : inv.price,
					'name' : inv.name,
					'account_id' : inv.account_id.id,
					'product_uom_id' : inv.product_id.uom_po_id.id,
					'company_id' : self.company_id.id,
					'l10n_latam_document_type_id': inv.type_document_id.id,
				}
				if inv.tax_id:
					vals.update({'tax_ids':([(6,0,[inv.tax_id.id])])})

				invoice.write({'invoice_line_ids' :([(0,0,vals)]) })
				invoice._get_currency_rate()
				invoice._compute_amount()
				invoice.flush_model()
				#CAMBIO DE CUENTA
				#invoice.cuenta_p_p=True
				#invoice.personalizadas_id=self.env['account.personalizadas'].search([('p_type','=','liability_payable')],limit=1).id
				#invoice.actualizar_cuentas_personalizadas()
				#-------------##
				if inv.date != inv.invoice_date:
					invoice.write({'date': inv.date})
				#invoice._post()
				inv.invoice_id = invoice.id
	
		for invo in self.invoice_ids.filtered(lambda l: l.invoice_id):
			if invo.invoice_id.state == 'draft':
				invo.invoice_id._post()

	def open_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		move_ids = self.invoice_ids.move_id.ids + self.delivery_ids.move_id.ids + self.returns_ids.move_id.ids
		domain = [('id', 'in', move_ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)
	
	def open_invoice_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		move_ids = self.invoice_ids.invoice_id.ids
		domain = [('id', 'in', move_ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)

class AccountSurrenderInvoiceLine(models.Model):
	_name = 'account.surrender.invoice.line'

	surrender_id = fields.Many2one('account.surrender.petty.cash.it',string='Main')
	partner_id = fields.Many2one('res.partner',string='Proveedor', readonly=True)
	date = fields.Date(string='Fecha Contable')
	invoice_date = fields.Date(string=u'Fecha Emisión')
	invoice_date_due = fields.Date(string=u'Fecha Vencimiento')
	currency_id = fields.Many2one('res.currency',string='Moneda')
	type_document_id = fields.Many2one('l10n_latam.document.type',string='Tipo de Documento', required=True)
	nro_comp = fields.Char(string='Nro Comprobante')
	product_id = fields.Many2one('product.product',string='Producto')
	name = fields.Char(string=u'Descripción')
	price = fields.Float(string='Monto',digits=(64,2))
	tax_id = fields.Many2one('account.tax',string='Impuesto')
	tc = fields.Float(string='T.C.',digits=(12,4),default=1)
	invoice_id = fields.Many2one('account.move',string='Factura')
	move_id = fields.Many2one('account.move',string='Pago')
	account_id = fields.Many2one('account.account',string='Cuenta',readonly=True)
	
	amount_real = fields.Float(string="Monto Real",compute="_compute_amount_real")
	
	
	@api.depends('surrender_id','price','currency_id','tc')
	def _compute_amount_real(self):
		for i in self:      			
			surrender = i.surrender_id
			amount_real = i.price if surrender.currency_id.id == i.currency_id.id else ((i.price * i.tc) if surrender.currency_id.name=='PEN' else (i.price / i.tc))
			i.amount_real = amount_real	
   
	@api.onchange('invoice_date')
	def _onchange_invoice_date(self):
		for record in self:
			if record.invoice_date:
				type_now=self.env['res.currency.rate'].sudo().search([('name','=',str(record.invoice_date)),('currency_id','=',record.currency_id.id),('company_id','=',record.surrender_id.company_id.id)])			
				if type_now:
					record.tc = type_now.sale_type					
				else:
					record.tc = 1	
	
	@api.onchange('invoice_date')
	def onchange_invoice_date(self):
		for line in self:
			line.date = line.invoice_date
			line.invoice_date_due = line.invoice_date

	@api.onchange('product_id')
	def onchange_product_id(self):
		for line in self:
			if line.product_id:
				line.name = line._get_computed_name()
				line.account_id = line.compute_account()
				line.tax_id = line.product_id.supplier_taxes_id[0].id if line.product_id.supplier_taxes_id else None

	def _get_computed_name(self):
		self.ensure_one()

		if not self.product_id:
			return ''

		if self.partner_id.lang:
			product = self.product_id.with_context(lang=self.partner_id.lang)
		else:
			product = self.product_id

		values = []
		if product.partner_ref:
			values.append(product.partner_ref)
		if product.description_purchase:
			values.append(product.description_purchase)
		return '\n'.join(values)
	
	@api.depends('product_id')
	def compute_account(self):
		self.ensure_one()
		if self.product_id.property_account_expense_id:
			account = self.product_id.property_account_expense_id
		elif self.product_id.categ_id.property_account_expense_categ_id:
			account = self.product_id.categ_id.property_account_expense_categ_id
		else:
			account_search = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id'),('company_id','=',self.env.company.id)],limit=1)
			account = account_search.value_reference
			account = account.split(",")[1]
			account = self.env['account.account'].browse(account)
		
		return account.id
	
	@api.onchange('nro_comp','type_document_id')
	def _get_ref(self):
		for i in self:
			digits_serie = ('').join(i.type_document_id.digits_serie*['0'])
			digits_number = ('').join(i.type_document_id.digits_number*['0'])
			if i.nro_comp:
				if '-' in i.nro_comp:
					partition = i.nro_comp.split('-')
					if len(partition) == 2:
						serie = digits_serie[:-len(partition[0])] + partition[0]
						number = digits_number[:-len(partition[1])] + partition[1]
						i.nro_comp = serie + '-' + number
	

class AccountSurrenderLine(models.Model):
	_name = 'account.surrender.line'
	_description = 'Lineas de operaciones de Rendiciones'

	surrender_id = fields.Many2one('account.surrender.petty.cash.it', string=u'Rendición/Caja Chica')
	move_id = fields.Many2one('account.move',string='Asiento')
	date = fields.Date(string="Fecha")
	journal_id = fields.Many2one('account.journal',string='Caja')
	currency_id = fields.Many2one('res.currency',string='Moneda',compute='compute_currency_line')
	amount = fields.Monetary(string="Monto")
	glosa = fields.Char(string="Glosa",compute="_compute_glosa")
	nro_comp  = fields.Char(string=u"Número de Operación")
	payment_method_id = fields.Many2one(
		'einvoice.catalog.payment',
		string='Medio de Pago'
		)
	tc = fields.Float(string='T.C.',digits=(12,4),default=1)
	type = fields.Selection([('delivery', 'Entregas'),('returns', 'Devoluciones')],string=u"Tipo Operación")
	amount_real = fields.Float(string="Monto Real",compute="_compute_amount_real")
	
	@api.depends('surrender_id','amount','currency_id','tc')
	def _compute_amount_real(self):
		amount_real = 0
		for i in self:
			amount_real = i.amount if i.surrender_id.currency_id.id == i.currency_id.id else ((i.amount * i.tc) if i.surrender_id.currency_id.name=='PEN' else (i.amount / i.tc))
			i.amount_real = amount_real	


	@api.onchange('date')
	def _onchange_date(self):
		for record in self:
			if record.date:
				type_now=self.env['res.currency.rate'].sudo().search([('name','=',str(record.date)),('company_id','=',record.surrender_id.company_id.id)])			
				if type_now:
					record.tc = type_now.sale_type					
				else:
					record.tc = 1       

	@api.depends('surrender_id','surrender_id.glosa')
	def _compute_glosa(self):
		for i in self:
			if i.surrender_id:             
				i.glosa = i.surrender_id.glosa
			else:
				i.glosa = ''

	@api.depends('journal_id','journal_id.currency_id')
	def compute_currency_line(self):
		for i in self:
			i.currency_id = i.journal_id.currency_id.id if i.journal_id.currency_id else i.journal_id.company_id.currency_id.id

	def view_account_move(self):
		return {
			'name':u'Asiento Contable',
			'view_mode': 'form',
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': self.move_id.id,
		}