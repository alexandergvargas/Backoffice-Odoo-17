# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO
import uuid

class AccountLeasingIt(models.Model):
	_name = 'account.leasing.it'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = 'Account Leasing IT'

	name = fields.Char(string=u'N° de contrato',required=True)
	value = fields.Float(string='Valor Activo Leasing')
	interest_value = fields.Float(string=u'Monto de Interés')
	insurance_value = fields.Float(string=u'Monto de Seguro')
	partner_id = fields.Many2one('res.partner',string=u'Proveedor',required=True)
	date = fields.Date(string='Fecha',required=True)
	total_quotes = fields.Integer(string=u'N° de Cuotas')
	currency_id = fields.Many2one('res.currency',string=u'Moneda',required=True)
	tc = fields.Float(string='TC',digits=(12,3))
	state = fields.Selection([('draft','Borrador'),
							('posted','Validado')],string='Estado',default='draft')
	move_id = fields.Many2one('account.move',string='Asiento',copy=False)
	line_ids = fields.One2many('account.leasing.it.line','main_id',string='Detalles', copy=True)
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	#CONTABILIDAD

	def get_default_asset_account_id(self):
		MainParameter = self.env['leasing.main.parameter'].get_main_parameter()
		return MainParameter.asset_account_id
	
	asset_account_id = fields.Many2one('account.account',string='Cuenta de Activo Fijo',default=get_default_asset_account_id)

	def get_default_deferred_interest_account_id(self):
		MainParameter = self.env['leasing.main.parameter'].get_main_parameter()
		return MainParameter.deferred_interest_account_id
	
	deferred_interest_account_id = fields.Many2one('account.account',string='Cuenta de Intereses Diferidos',default=get_default_deferred_interest_account_id)

	def get_default_deferred_insurance_account_id(self):
		MainParameter = self.env['leasing.main.parameter'].get_main_parameter()
		return MainParameter.deferred_insurance_account_id
	
	deferred_insurance_account_id = fields.Many2one('account.account',string='Cuenta de Seguros Diferidos',default=get_default_deferred_insurance_account_id)

	def get_default_leasing_payable_account_id(self):
		MainParameter = self.env['leasing.main.parameter'].get_main_parameter()
		return MainParameter.leasing_payable_account_id
	
	leasing_payable_account_id = fields.Many2one('account.account',string='Cuenta por Pagar Leasing',default=get_default_leasing_payable_account_id)

	def get_default_interest_payable_account_id(self):
		MainParameter = self.env['leasing.main.parameter'].get_main_parameter()
		return MainParameter.interest_payable_account_id
	
	interest_payable_account_id = fields.Many2one('account.account',string=u'Cuenta por Pagar Intereses',default=get_default_interest_payable_account_id)

	def get_default_insurance_payable_account_id(self):
		MainParameter = self.env['leasing.main.parameter'].get_main_parameter()
		return MainParameter.insurance_payable_account_id
	
	insurance_payable_account_id = fields.Many2one('account.account',string='Cuenta por Pagar Seguros',default=get_default_insurance_payable_account_id)

	def get_default_purchase_tax_id(self):
		MainParameter = self.env['leasing.main.parameter'].get_main_parameter()
		return MainParameter.purchase_tax_id

	purchase_tax_id = fields.Many2one('account.tax',string='Impuesto de Compra',default=get_default_purchase_tax_id)

	def get_default_interest_expense_account_id(self):
		MainParameter = self.env['leasing.main.parameter'].get_main_parameter()
		return MainParameter.interest_expense_account_id
	
	interest_expense_account_id = fields.Many2one('account.account',string=u'Cuenta para Gasto de Intereses',default=get_default_interest_expense_account_id)

	def get_default_commission_expense_account_id(self):
		MainParameter = self.env['leasing.main.parameter'].get_main_parameter()
		return MainParameter.commission_expense_account_id
	
	commission_expense_account_id = fields.Many2one('account.account',string=u'Cuenta para Gasto de Comisiones',default=get_default_commission_expense_account_id)

	def get_default_insurance_expense_account_id(self):
		MainParameter = self.env['leasing.main.parameter'].get_main_parameter()
		return MainParameter.insurance_expense_account_id
	
	insurance_expense_account_id = fields.Many2one('account.account',string='Cuenta para Gasto de Seguros',default=get_default_insurance_expense_account_id)

	def get_default_purchase_journal_id(self):
		MainParameter = self.env['leasing.main.parameter'].get_main_parameter()
		return MainParameter.purchase_journal_id

	purchase_journal_id = fields.Many2one('account.journal',string='Diario Facturas de Compras',default=get_default_purchase_journal_id)

	def get_default_journal_id(self):
		MainParameter = self.env['leasing.main.parameter'].get_main_parameter()
		return MainParameter.journal_id
	
	journal_id = fields.Many2one('account.journal',string='Diario para Devengos y Asiento General',default=get_default_journal_id)

	@api.onchange('date')	
	def rate_tc(self):
		for record in self:				
			import datetime							
			fecha_actual = datetime.datetime.now()
			nueva_fecha = fecha_actual - datetime.timedelta(hours=5)			
			type_now=self.env['res.currency.rate'].sudo().search([('name','=',nueva_fecha.date()),('company_id','=',record.company_id.id)])			
			if type_now:
				record.tc = type_now.sale_type					
			else:
				record.tc = 1	

	def view_account_move(self):
		return {
			'name':u'Asiento de Contrato %s'%self.name,
			'view_mode': 'form',
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': self.move_id.id,
		}
	
	def action_post(self):
		for i in self:
			i.state = 'posted'
	
	def action_draft(self):
		for i in self:
			if i.move_id:
				raise UserError(u'Debe eliminar el asiento generado antes de Establecer a Borrador.')
			for line in i.line_ids:
				if line.invoice_id:
					raise UserError(u'Debe eliminar las facturas generadas antes de Establecer a Borrador.')
				if line.move_id:
					raise UserError(u'Debe eliminar los asientos generados antes de Establecer a Borrador.')
			i.state = 'draft'

	def validate_fields(self):
		if not self.asset_account_id:
			raise UserError('Falta configurar Campo "Cuenta de Activo Fijo" en pestaña Contabilidad')
		if not self.deferred_interest_account_id:
			raise UserError('Falta configurar Campo "Cuenta de Intereses Diferidos" en pestaña Contabilidad')
		if not self.deferred_insurance_account_id:
			raise UserError('Falta configurar Campo "Cuenta de Seguros Diferidos" en pestaña Contabilidad')
		if not self.leasing_payable_account_id:
			raise UserError('Falta configurar Campo "Cuenta por Pagar Leasing" en pestaña Contabilidad')
		if not self.interest_payable_account_id:
			raise UserError('Falta configurar Campo "Cuenta por Pagar Intereses" en pestaña Contabilidad')
		if not self.insurance_payable_account_id:
			raise UserError('Falta configurar Campo "Cuenta por Pagar Seguros" en pestaña Contabilidad')
		if not self.journal_id:
			raise UserError('Falta configurar Campo "Diario para Devengos y Asiento General" en pestaña Contabilidad')
		return True

	def create_move(self):
		self.validate_fields()
		lineas = []
		doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)
		accounts = [self.asset_account_id.id,self.deferred_interest_account_id.id,self.deferred_insurance_account_id.id,self.leasing_payable_account_id.id,self.interest_payable_account_id.id,self.insurance_payable_account_id.id]
		ac = [self.value,self.interest_value,self.insurance_value,self.value*-1,self.interest_value*-1,self.insurance_value*-1]
		if self.currency_id.id != self.company_id.currency_id.id:
			debit = [self.value*self.tc,self.interest_value*self.tc,self.insurance_value*self.tc,0,0,0]
			credit = [0,0,0,self.value*self.tc,self.interest_value*self.tc,self.insurance_value*self.tc]
		else:
			debit = [self.value,self.interest_value,self.insurance_value,0,0,0]
			credit = [0,0,0,self.value,self.interest_value,self.insurance_value]
		for g in range(6):
			vals = (0,0,{
				'account_id': accounts[g],
				'partner_id':self.partner_id.id,
				'type_document_id':doc.id,
				'nro_comp': self.name,
				'name': self.name,
				'currency_id': self.currency_id.id,
				'amount_currency': ac[g],
				'debit': debit[g],
				'credit': credit[g],
				'company_id': self.company_id.id,
				'tc': self.tc,
			})
			lineas.append(vals)
		#raise UserError(str(lineas))
		data = {
			'company_id': self.company_id.id,
			'journal_id': self.journal_id.id,
			'date': self.date,
			'invoice_date': self.date,
			'line_ids':lineas,
			'ref': self.name,
			'glosa':self.name,
			'currency_rate':self.tc,
			'move_type':'entry'}
		
		move_id = self.env['account.move'].create(data)
		move_id.action_post()
		self.move_id = move_id.id
	
	def import_lines(self):
		wizard = self.env['import.leasing.line.wizard'].create({
			'leasing_id':self.id
			})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_import_leasing_line_wizard_form' % module)
		return {
			'name':u'Importar Detalles',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'import.leasing.line.wizard',
			'view_id': view.id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

class AccountLeasingItLine(models.Model):
	_name = 'account.leasing.it.line'
	_description = 'Account Leasing IT Detail'

	main_id = fields.Many2one('account.leasing.it',string=u'Main')
	quote = fields.Integer(string=u'N° Cuota')
	date_due = fields.Date(string='Fecha de Vencimiento')
	amortization = fields.Float(string=u'Amortización')
	interest = fields.Float(string=u'Interés')
	insurance = fields.Float(string=u'Seguros')
	value = fields.Float(string=u'Capital')
	port = fields.Float(string=u'Portes')
	amount_quote = fields.Float(string=u'Cuota')
	tax = fields.Float(string=u'IGV')
	total = fields.Float(string=u'Com. Pago')
	invoice_id = fields.Many2one('account.move',string='Factura',copy=False)
	move_id = fields.Many2one('account.move',string='Asiento',copy=False)

	def action_create_invoice_wizard(self):
		wizard = self.env['account.leasing.invoice.wizard'].create({
			'line_id':self.id,
			'date':self.date_due
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_account_leasing_invoice_wizard_form' % module)
		return {
			'name':u'Crear Factura',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'account.leasing.invoice.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def validate_invoice_fields(self):
		if not self.main_id.leasing_payable_account_id:
			raise UserError('Falta configurar Campo "Cuenta por Pagar Leasing" en pestaña Contabilidad')
		if not self.main_id.interest_payable_account_id:
			raise UserError('Falta configurar Campo "Cuenta por Pagar Intereses" en pestaña Contabilidad')
		if not self.main_id.insurance_payable_account_id:
			raise UserError('Falta configurar Campo "Cuenta por Pagar Seguros" en pestaña Contabilidad')
		if not self.main_id.commission_expense_account_id:
			raise UserError('Falta configurar Campo "Cuenta para Gasto de Comisiones" en pestaña Contabilidad')
		if not self.main_id.purchase_journal_id:
			raise UserError('Falta configurar Campo "Diario Facturas de Compras" en pestaña Contabilidad')
		if not self.main_id.purchase_tax_id:
			raise UserError('Falta configurar Campo "Impuesto de Compras" en pestaña Contabilidad')
		return True
	
	def create_invoice(self,type_document_id,nro_comp,date):
		if self.invoice_id:
			raise UserError(u'Ya tiene una factura creada.')
		self.validate_invoice_fields()
		currency_id = self.env.ref('base.USD') if self.main_id.currency_id == self.main_id.company_id.currency_id else self.main_id.currency_id
		values = {
			'partner_id' : self.main_id.partner_id.id,
			'currency_id' : self.main_id.currency_id.id,
			'invoice_user_id':self.env.uid,
			'move_type' : 'in_invoice',
			'date':date,
			'invoice_date':date,
			'invoice_date_due': self.date_due,
			'journal_id' : self.main_id.purchase_journal_id.id,
			'l10n_latam_document_type_id' : type_document_id.id,
			'nro_comp' : nro_comp,
			'glosa': 'Leasing %s'%self.main_id.name,
			'company_id' : self.main_id.company_id.id,
			'currency_rate': self.env['res.currency.rate'].search([('name','=',date),('currency_id','=',currency_id.id),('company_id','=',self.main_id.company_id.id)],limit=1).sale_type
		}
		if date != self.date_due:
			values['invoice_payment_term_id'] = None
		invoice = self.env['account.move'].create(values)
		line_vals = []
		line = (0,0,{
					'quantity' : 1,
					'price_unit' : self.amortization if self.quote != 0 else self.amount_quote,
					'name' : 'Contrato de Leasing',
					'account_id' : self.main_id.leasing_payable_account_id.id,
					'company_id' : self.main_id.company_id.id,
					'tax_ids':([(6,0,[self.main_id.purchase_tax_id.id])])
				})
		line_vals.append(line)
		if self.quote != 0:
			line = (0,0,{
					'quantity' : 1,
					'price_unit' : self.interest,
					'name' : u'Interés Leasing',
					'account_id' : self.main_id.interest_payable_account_id.id,
					'company_id' : self.main_id.company_id.id,
					'tax_ids':([(6,0,[self.main_id.purchase_tax_id.id])])
				})
			line_vals.append(line)
			line = (0,0,{
					'quantity' : 1,
					'price_unit' : self.insurance,
					'name' : u'Seguro Leasing',
					'account_id' : self.main_id.insurance_payable_account_id.id,
					'company_id' : self.main_id.company_id.id,
					'tax_ids':([(6,0,[self.main_id.purchase_tax_id.id])])
				})
			line_vals.append(line)
			line = (0,0,{
					'quantity' : 1,
					'price_unit' : self.port,
					'name' : u'Otras comisiones y Gastos bancarios',
					'account_id' : self.main_id.commission_expense_account_id.id,
					'company_id' : self.main_id.company_id.id,
					'tax_ids':([(6,0,[self.main_id.purchase_tax_id.id])])
				})
			line_vals.append(line)

		invoice.write({'invoice_line_ids' :line_vals })
		invoice._get_currency_rate()
		invoice._compute_amount()
		invoice.flush_model()

		invoice.action_post()
		self.invoice_id = invoice.id
		doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)
		lines = invoice.line_ids.filtered(lambda l: l.account_id.code[:2] == '45')
		lines.write({
			'type_document_id': doc.id,
			'nro_comp': self.main_id.name
		})
			
	def validate_fields(self):
		if not self.main_id.interest_expense_account_id:
			raise UserError('Falta configurar Campo "Cuenta para Gasto de Intereses" en pestaña Contabilidad del Leasing')
		if not self.main_id.insurance_expense_account_id:
			raise UserError('Falta configurar Campo "Cuenta para Gasto de Seguros" en pestaña Contabilidad del Leasing')
		if not self.main_id.deferred_interest_account_id:
			raise UserError('Falta configurar Campo "Cuenta de Intereses Diferidos" en pestaña Contabilidad del Leasing')
		if not self.main_id.deferred_insurance_account_id:
			raise UserError('Falta configurar Campo "Cuenta de Seguros Diferidos" en pestaña Contabilidad del Leasing')
		if not self.main_id.journal_id:
			raise UserError('Falta configurar Campo "Diario para Devengos y Asiento General" en pestaña Contabilidad del Leasing')
		return True
	
	def create_move(self):
		for i in self:
			if not i.move_id and i.quote != 0:
				i.validate_fields()
				lineas = []
				doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)
				accounts = [i.main_id.interest_expense_account_id.id,i.main_id.insurance_expense_account_id.id,i.main_id.deferred_interest_account_id.id,i.main_id.deferred_insurance_account_id.id]
				tc = i.main_id.tc if i.main_id.currency_id.id != i.main_id.company_id.currency_id.id else 1
				ac = [i.interest*tc,i.insurance*tc,i.interest*tc*-1,i.insurance*tc*-1]
				debit = [i.interest*tc,i.insurance*tc,0,0]
				credit = [0,0,i.interest*tc,i.insurance*tc]
				for g in range(4):
					vals = (0,0,{
						'account_id': accounts[g],
						'partner_id':i.main_id.partner_id.id,
						'type_document_id':doc.id,
						'nro_comp': i.main_id.name,
						'name': i.main_id.name,
						'currency_id': i.main_id.company_id.currency_id.id,
						'amount_currency': ac[g],
						'debit': debit[g],
						'credit': credit[g],
						'company_id': i.main_id.company_id.id,
						'tc': i.main_id.tc,
					})
					lineas.append(vals)
				#raise UserError(str(lineas))
				data = {
					'company_id': i.main_id.company_id.id,
					'journal_id': i.main_id.journal_id.id,
					'date': i.date_due,
					'invoice_date': i.date_due,
					'line_ids':lineas,
					'ref': i.main_id.name,
					'glosa':i.main_id.name,
					'currency_rate':i.main_id.tc,
					'move_type':'entry'}
				
				move_id = self.env['account.move'].create(data)
				move_id.action_post()
				i.move_id = move_id.id

		return self.env['popup.it'].get_message('SE CREARON CORRECTAMENTE LOS ASIENTOS DE DEVENGO, INTERESES Y SEGUROS.')
	
	def view_account_invoice(self):
		return {
			'name':u'Factura de Cuota %s'%self.quote,
			'view_mode': 'form',
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': self.invoice_id.id,
		}
	
	def view_account_move(self):
		return {
			'name':u'Asiento de Cuota %s'%self.quote,
			'view_mode': 'form',
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': self.move_id.id,
		}