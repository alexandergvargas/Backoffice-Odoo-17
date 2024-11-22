from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
class account_move(models.Model):
	_inherit = 'account.move'
	
	personalizadas_id = fields.Many2one(
		'account.personalizadas',
		string='Cuenta Personalizadas',
		)
	cuenta_p_p = fields.Boolean(string="Cuenta de pago personalizada",default=True)

	@api.model
	def create(self, vals):
		res = super(account_move, self).create(vals)
		for i in res:
			i._onchange_cuenta_p_p()
		return res
	
	@api.onchange('cuenta_p_p','l10n_latam_document_type_id')
	def _onchange_cuenta_p_p(self):
		for i  in self:			
			custom = self.env['account.personalizadas'].search([('company_id','=',self.env.company.id),('p_type','=','asset_receivable' if i.move_type == 'out_invoice' or i.move_type == 'out_refund' else 'liability_payable'),('type_document_id','=',i.l10n_latam_document_type_id.id)],limit=1).id			
			if not custom:
				custom = self.env['account.personalizadas'].search([('use_default','=',True),('company_id','=',self.env.company.id),('p_type','=','asset_receivable' if i.move_type == 'out_invoice' or i.move_type == 'out_refund' else 'liability_payable')],limit=1).id
				i.personalizadas_id = custom
			else:
				i.personalizadas_id = custom
					
	def _post(self, soft=True):
		for record in self:
			record.actualizar_cuentas_personalizadas()			
		return super(account_move, self)._post(soft=soft)
		
	@api.onchange('personalizadas_id','currency_id')
	def actualizar_cuentas_personalizadas(self):
		for i in self:			
			if i.state == "draft":
				if i.cuenta_p_p:
					if i.personalizadas_id:	                     
						if i.move_type == 'out_invoice' or i.move_type == 'out_refund':   					
							if i.line_ids:  
								for lines in i.line_ids:
									if lines.account_id.account_type == 'asset_receivable':                               
										if i.currency_id.name == 'PEN':
											lines.account_id = i.personalizadas_id.cuenta_mn_id.id
										else:
											lines.account_id = i.personalizadas_id.cuenta_me_id.id									
							else:
								pass
						if i.move_type == 'in_invoice' or i.move_type=='in_refund':                    
							if i.line_ids:  
								for lines in i.line_ids:
									if lines.account_id.account_type == 'liability_payable':
										if i.currency_id.name == 'PEN':
											lines.account_id = i.personalizadas_id.cuenta_mn_id.id
										else:
											lines.account_id = i.personalizadas_id.cuenta_me_id.id
							else:
								pass
			else:
				raise UserError ("SOLO SE PUEDE ACTUALIZAR LA CUENTA EN EL ESTADO BORRADOR")
class account_move_line(models.Model):
	_inherit = 'account.move.line'

	def _check_constrains_account_id_journal_id(self):		
		self.flush_recordset()
		for line in self.filtered(lambda x: x.display_type not in ('line_section', 'line_note')):
			account = line.account_id
			account_currency = account.currency_id
			
			
			if account_currency and account_currency != line.company_currency_id and account_currency != line.currency_id:				
				line.move_id._onchange_cuenta_p_p()
				line.move_id.actualizar_cuentas_personalizadas()
		return super(account_move_line, self)._check_constrains_account_id_journal_id()