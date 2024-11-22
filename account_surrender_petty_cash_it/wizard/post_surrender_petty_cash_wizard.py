# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _

class PostSurrenderPettyCash(models.TransientModel):
	_name = "post.surrender.petty.cash.wizard"
	
	type_selection = fields.Selection([('invoice','Facturas'),('delivery','Entregas'),('return','Devoluciones'),('all','Todos')],string='Publicar',default='all')
	spt_id = fields.Many2one('account.surrender.petty.cash.it',string=u'Rendicion/Caja')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
		
	def post(self):
		if self.type_selection == 'invoice':
			self.spt_id.create_invoices_and_payments()
		elif self.type_selection == 'delivery':
			self.spt_id.create_accounts_delivery()
		elif self.type_selection == 'return':
			self.spt_id.create_accounts_returns()
		else:
			self.spt_id.apply_all()