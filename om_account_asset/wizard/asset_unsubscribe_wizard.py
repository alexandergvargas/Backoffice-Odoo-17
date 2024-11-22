# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _

class AssetUnsubscribeWizard(models.TransientModel):
	_name = "asset.unsubscribe.wizard"
	
	asset_id = fields.Many2one('account.asset.asset',string='Activo',required=True)
	journal_id = fields.Many2one('account.journal',string='Diario')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
		
	def unsubscribe(self):
		return self.asset_id.change_to_unsubscribe(self.journal_id)