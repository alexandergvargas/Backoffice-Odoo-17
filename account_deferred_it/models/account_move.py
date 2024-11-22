# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class account_move(models.Model):
	_inherit = 'account.move'
	

	
	asset_deferred_id = fields.Many2one('account.deferred', string='Modelo Diferido')


			

	def _post(self, soft=True):
		to_post = super(account_move,self)._post(soft=soft)
		for i in self:
			i.values_for_deferred()
		return to_post
	
	def values_for_deferred(self):
		for record in self:		
			for lines in record.line_ids.filtered(lambda l: l.account_id.account_type in ['liability_non_current','asset_prepayments'] and l.account_id.type_deferrend and l.account_id.type_deferrend != 'no'):
				if not record.asset_deferred_id:
					asset_deferred_copy = lines.account_id.account_deferrend_id.copy()
					record.asset_deferred_id  = asset_deferred_copy.id
				record.asset_deferred_id.name = lines.name
				record.asset_deferred_id.amount_origin = lines.price_subtotal
							
			record.asset_deferred_id.move_id = record.id
			record.asset_deferred_id.date_ad = record.date
			record.asset_deferred_id.nro_comp = record.nro_comp
			record.asset_deferred_id.l10n_latam_document_type_id = record.l10n_latam_document_type_id.id
			record.asset_deferred_id.partner_id = record.partner_id.id
			record.asset_deferred_id._onchange_date_ad()
			record.asset_deferred_id.create_lines_ids()

	


	def action_open_deferred_ids(self):
		for record in self:
			context_type = self.env.context.get('type')
			if context_type == 'expense':
				model_name = u'Modelo Gastos Diferidos'
			elif context_type == 'income':
				model_name = u'Modelo Ingreso Diferidos'
			else:
				continue		
			
			action = {
				'name': model_name,
				'res_model': 'account.deferred',
				'type': 'ir.actions.act_window',
				'res_id': record.asset_deferred_id.id,
				'view_mode':'form',
				'view_type':'form',
				'view_id': self.env.ref('account_deferred_it.view_account_deferred_form').id
			}
			
			return action



