# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import re

class AccountMove(models.Model):
	_inherit = 'account.move'
	
	s_retencion = fields.Boolean(string=u'Tiene Retención',copy=False)

	def _post(self, soft=True):
		to_post = super(AccountMove,self)._post(soft=soft)
		param = self.env['account.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1)
		for move in self:
			partner = move.partner_id
			if (not partner.is_partner_perception and not partner.good_taxpayer and not partner.executing_unit) \
			and move.l10n_latam_document_type_id.id not in partner.is_partner_retencion and not move.linked_to_detractions \
			and abs(move.amount_total_signed) > param.amount_retention:
				move.s_retencion = True
			else:
				move.s_retencion = False
		return to_post
	
	def button_draft(self):
		for move in self:
			move.s_retencion = False
		return super(AccountMove,self).button_draft()
