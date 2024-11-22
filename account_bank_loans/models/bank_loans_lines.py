# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

class bank_loans_lines(models.Model):
	_name = 'bank.loans.lines'
	_description = 'Lineas Prestamos'
	

	loan_id = fields.Many2one('bank.loans', string='Prestamo')
	month = fields.Char('Meses')
	date = fields.Date('Fecha')
	amount_amort = fields.Float(u'Amortización')
	inters = fields.Float(u'Interes')    
	quota = fields.Float(u'Cuota')
	amount_debt = fields.Float(u'Saldo Deuda')
	company_id = fields.Many2one('res.company', string=u'Compañia',related='loan_id.company_id')
	move_id = fields.Many2one('account.move', string='Asiento',copy=False)
	state = fields.Selection([
		('draft', 'SIN PUBLICAR'),
		('posted', 'PUBLICADO'),
		('cancel', 'CANCELADO')
	], string='Estado',tracking=True,copy=False,default='draft',compute='_compute_state')
	state_detalle = fields.Selection(related='loan_id.state')
	@api.depends('move_id','move_id.state')
	def _compute_state(self):
		for i in self:
			i.state = 'draft'
			if i.move_id:
				i.state = i.move_id.state
    
	def create_account(self):
		for i in self:
			if not i.move_id:
				doc = i.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)
				data=i.libray_data_move(doc)

				#REDONDEO
				total_debit = sum(round(line[2]['debit'],2) for line in data['line_ids'])
				total_credit = sum(round(line[2]['credit'],2) for line in data['line_ids'])

				# Calcular la diferencia
				difference = total_debit - total_credit

				# Evaluar el resultado
				if float(difference) > 0:
					rounding_gain_account = self.env['account.main.parameter'].search([('company_id','=',i.company_id.id)],limit=1).rounding_gain_account
					if not rounding_gain_account:
						raise UserError(u'No existe Cuenta de Ganancia en Parametros Principales de Contabilidad para su Compañía')
					data['line_ids'].append((0,0,{
								'account_id': rounding_gain_account.id,
								'currency_id': i.company_id.currency_id.id,
								'amount_currency': difference*-1,
								'debit':0,
								'credit':difference,
								'company_id': i.company_id.id
								}))
				elif float(difference) < 0:
					rounding_loss_account = self.env['account.main.parameter'].search([('company_id','=',i.company_id.id)],limit=1).rounding_loss_account
					if not rounding_loss_account:
						raise UserError(u'No existe Cuenta de Pérdida en Parametros Principales de Contabilidad para su Compañía')
					data['line_ids'].append((0,0,{
								'account_id': rounding_loss_account.id,
								'currency_id': i.company_id.currency_id.id,
								'amount_currency': difference*-1,
								'debit':difference*-1,
								'credit':0,
								'company_id': i.company_id.id
								}))
					
				obj_move = self.env['account.move'].create(data)
				i.move_id=obj_move.id
				obj_move.action_post()
	
	def libray_data_line(self,doc):
		for line in self:
			for i in line.loan_id:
				move_lines = []
				account = [i.due_account_id.id,i.interest_debt_account.id,i.company_id.account_journal_payment_credit_account_id.id,i.expense_account_id.id,i.interest_account_id.id]
				amount_currency = [line.amount_amort,line.inters,line.quota*-1,line.inters,line.inters*-1]
				if i.currency_id.name == 'USD':
					debit =  [line.amount_amort*i.tc,line.inters*i.tc,0,line.inters*i.tc,0]
					credit =  [0,0,line.quota*i.tc,0,line.inters*i.tc]
				else:
					debit =  [line.amount_amort,line.inters,0,line.inters,0]
					credit = [0,0,line.quota,0,line.inters]
				for r in range(5):
					line_firt = (0,0,{
								'account_id': account[r],
								'currency_id': i.currency_id.id,
								'amount_currency': float(amount_currency[r]),
								'debit':debit[r],
								'credit':credit[r],
								'name': i.nro_comp,
								'partner_id': i.partner_id.id,
								'company_id': i.company_id.id,		
								'nro_comp': i.nro_comp,
								'type_document_id': doc.id,
								'tc': i.tc,
								})	
					move_lines.append(line_firt)
			return move_lines
	
	def libray_data_move(self,doc):
		for i in self.loan_id:
			if not i.journal_id.id:
				raise ValidationError (u'NO SE PUEDE GENERAL UN ASIENTO SIN EL DIARIO')
			data = {
				'journal_id': i.journal_id.id,
				'ref': i.nro_comp,
				'date': self.date,
				'company_id': i.company_id.id,
				'glosa': "PAGO CUOTA %s PRESTAMO %s"%(str(self.month),i.nro_comp),
				'currency_rate': i.tc,
				'currency_id': i.currency_id.id,
				'move_type':'entry',
				'line_ids':self.libray_data_line(doc)
			}			
		return data
	
	def view_account_move(self):
		return {
			'view_mode': 'form',
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': self.move_id.id,
		}