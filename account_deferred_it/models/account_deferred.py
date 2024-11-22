# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import *
import datetime
from odoo.tools import frozendict, format_date, float_compare, Query

class account_deferred(models.Model):
	_name = 'account.deferred'
	_inherit = "analytic.mixin"
	_description = 'Modelos diferidos'
	

	name = fields.Char('Nombre', copy=False)
	number = fields.Integer(string=u'Número de reconocimientos')
	period = fields.Selection([
		('anio', u'Años'),
		('month',u'Meses')
	], string='Periodo', default='month')
	account_deferred_id = fields.Many2one('account.account', string='Cuenta de diferidos')
	account_id = fields.Many2one('account.account', string='Cuenta')
	journal_id = fields.Many2one('account.journal', string='Diario')
	
	type = fields.Selection([
		('income', 'Ingreso'),
		('expense','Gastos')
	], string='Tipo')

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

	currency_id = fields.Many2one('res.currency', string='Moneda',required=True, default=lambda self: self.env.company.currency_id.id,readonly=True)
	
	amount_origin = fields.Monetary('Valor Original', readonly=True,copy=False)
	
	date_ad = fields.Date(u'Fecha de Adquisión',copy=False)

	move_id = fields.Many2one('account.move', string="Asiento Contable",copy=False)

	line_ids = fields.One2many('account.deferred.line', 'account_deferred_id', string='Tabla',copy=False)

	is_model = fields.Boolean('Es Modelo',copy=False)

	first_date = fields.Date('Primera fecha de reconocimiento')

	state = fields.Selection([
		('draft', 'Borrador'),
		('open', 'En Proceso'),
		('close', 'Cerrado'),
	], string='Estado', default='draft')

	analytic_distribution = fields.Json(
		string=u'Distribución Analítica',
		compute="_compute_analytic_distribution", store=True, copy=True, readonly=False,
		precompute=True
	)

	nro_comp = fields.Char('Nro de Comprobante', copy=False)

	l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type', string='Tipo Comprobante', copy=False)

	partner_id = fields.Many2one('res.partner', string='Socio', copy=False)

	model_id = fields.Many2one('account.deferred', string='Modelo', change_default=True, domain="[('is_model', '=', True),('type', '=', type)]")

	def _compute_analytic_distribution(self):
		pass

	number_moves = fields.Integer(compute='_compute_number_moves', string='Asientos Contables')
	
	@api.depends('line_ids')
	def _compute_number_moves(self):
		for i in self:
			count = len(i.line_ids.filtered(lambda l: l.move_id))
			i.number_moves = count if count else 0

	@api.onchange('date_ad')
	def _onchange_date_ad(self):
		import calendar
		for i  in self:
			if i.date_ad:
				date = i.date_ad
				_, last_day = calendar.monthrange(date.year, date.month)
				i.first_date=date.replace(day=last_day)
	
	def create_lines_ids(self):		
		for i in self:		
			from datetime import date, timedelta
			import calendar				
			first_day_of_month = i.first_date
			next_month = first_day_of_month.replace(day=calendar.monthrange(first_day_of_month.year, first_day_of_month.month)[1])
			if i.amount_origin != 0:
				monto = i.amount_origin / i.number
				amount_accumulated = monto
				amount_next = i.amount_origin - monto			
				lines = []
				for line in i.line_ids:
					line.unlink()
				for y in range(i.number):					
					if y == 0:
						lines.append((0, 0, {'name': '%s (%s/%s)'%(str(i.name),str(y+1),str(i.number)),
											'amount': monto, 
											'date': str(next_month), 
											'amount_accumulated': amount_accumulated, 
											'amount_next': amount_next,
											'sequence':str(y+1)}))
					else:
						amount_next -= monto
						amount_accumulated += monto
						if i.period == 'month':
							next_month = next_month + timedelta(days=1)
							next_month = next_month.replace(day=calendar.monthrange(next_month.year, next_month.month)[1])
						else:
							next_month = next_month.replace(year=next_month.year + 1)
						lines.append((0, 0, {'name': '%s (%s/%s)'%(str(i.name),str(y+1),str(i.number)), 
											'amount': monto, 
											'date': str(next_month), 
											'amount_accumulated': amount_accumulated, 
											'amount_next': amount_next,
											'sequence':str(y+1)}))
				
				i.write({'line_ids': lines})

	def post(self):
		
		for i in self:
			if len(i.line_ids) <= 0:
				raise UserError(str("No se puede validar lineas inexistentes"))
			else:
				i.validate_fields()						
				i.action_open()

	def action_draft(self):
		for i in self:
			i.create_lines_ids()
			i.state="draft"

	def action_open(self):
		for i in self:
			i.state="open"

	def action_close(self):
		for i in self:
			i.state="close"
	
	def view_action_move_ids(self):
		for i in self:
			moves_ids = []
			for line in i.line_ids.filtered(lambda l: l.move_id):
				moves_ids.append(line.move_id.id)
		return {
			'name': 'Asientos',
			'domain' : [('id','in',moves_ids)],
			'type': 'ir.actions.act_window',
			'res_model': 'account.move',
			'view_mode': 'tree,form',
			'view_type': 'form',
			
		}
	
	def unlink(self):
		for i in self:
			if i.state != 'draft':
				raise UserError ("El diferido debe estar en estado Borrador para eliminar")
			return super(account_deferred,i).unlink()
	
	@api.onchange('model_id')
	def _onchange_model_id(self):
		model = self.model_id
		if model:
			self.number = model.number
			self.period = model.period
			self.account_deferred_id = model.account_deferred_id.id
			self.account_id = model.account_id.id
			self.analytic_distribution = model.analytic_distribution		
			self.journal_id = model.journal_id.id
	
	def validate_fields(self):
		for i in self:
			if not i.l10n_latam_document_type_id:
				raise UserError (u"Falta agregar el Tipo de Comprobante en la pestaña Otra información")
			if not i.partner_id:
				raise UserError (u"Falta agregar el Socio en la pestaña Otra información")
			if not i.nro_comp:
				raise UserError (u"Falta agregar el Socio en la pestaña Otra información")

class account_deferred_line(models.Model):
	_name = 'account.deferred.line'
	
	name = fields.Char('Referencia',copy=False)
	account_deferred_id = fields.Many2one('account.deferred', string='Modelo',copy=False)
	date = fields.Date(u'Fecha',copy=False)
	currency_id = fields.Many2one('res.currency', string='Moneda',required=True, default=lambda self: self.env.company.currency_id.id,readonly=True)
	amount = fields.Monetary('Monto',copy=False)
	amount_accumulated = fields.Monetary('Monto Acumulado',copy=False)
	amount_next = fields.Monetary(u'Monto Próximo Periodo',copy=False)	
	move_id = fields.Many2one('account.move', string="Asiento Contable",copy=False)
	sequence = fields.Integer('Secuencia')
	
	def post_line(self):
		for i in self:
			if not i.move_id:				
				doc = i.account_deferred_id.l10n_latam_document_type_id
				data=i.libray_data_move(doc)
				obj_move = self.env['account.move'].create(data)
				i.move_id=obj_move.id
				if i.account_deferred_id.account_deferred_id.type_deferrend == 'posted':
					obj_move.action_post()
				if len(i.account_deferred_id.line_ids.filtered(lambda l: l.move_id))==i.account_deferred_id.number:
					i.account_deferred_id.action_close()

	
			
	def libray_data_move(self,doc):
		for i in self:
			rate = self.env['res.currency.rate'].search([('name','=',str(i.date)),('company_id','=',i.account_deferred_id.company_id.id)],limit=1).sale_type		
			data = {
				'journal_id': i.account_deferred_id.journal_id.id,
				'date': i.date,
				'company_id': i.account_deferred_id.company_id.id,
				'glosa': i.name,
				'ref': "DEVENGUE %s"%(str(i.sequence if i.sequence else "")) if i.account_deferred_id.type == 'expense' else "INGRESO %s"%(str(i.sequence if i.sequence else "")),
				'currency_rate': rate if rate else 1,
				'currency_id': i.currency_id.id,
				'move_type':'entry',
				'line_ids':i.libray_data_line(doc,rate if rate else 1)
			}			
		return data
	
	def libray_data_line(self,doc,rate):
		for i in self:
			move_lines = []
			account = [i.account_deferred_id.account_deferred_id.id,i.account_deferred_id.account_id.id]
			amount_currency = [i.amount*-1,i.amount]
			analytic_distribution = [i.account_deferred_id.analytic_distribution,""]
			if i.currency_id.name == 'USD':
				credit =  [i.amount*rate,0]
				debit =  [0,i.amount*rate]
			else:
				credit =  [i.amount,0]
				debit =  [0,i.amount]
			for r in range(2):
				line_firt = (0,0,{
							'account_id': account[r],
							'currency_id': i.currency_id.id,
							'amount_currency': float(amount_currency[r]),
							'debit':debit[r],
							'credit':credit[r],
							'name': i.name,
							'partner_id': i.account_deferred_id.partner_id.id,
							'company_id': i.account_deferred_id.company_id.id,		
							'analytic_distribution':analytic_distribution[r],
	  					 	'display_type': 'product',
							'type_document_id': doc.id,
							'tc': rate,
							'nro_comp':i.account_deferred_id.nro_comp
							})				
				move_lines.append(line_firt)
			return move_lines
		
	def view_action_move_id(self):
		for i in self:
			return {
				'name': 'Asiento',
				'domain' : [('id','=',i.move_id.id)],
				'type': 'ir.actions.act_window',
				'res_model': 'account.move',
				'view_mode': 'tree,form',
				'view_type': 'form',				
			}