# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountSunatTableMi(models.Model):
	_name = 'account.sunat.table.mi'
	_description = 'AccountSunatTableMi'

	name = fields.Char('Descripción')
	code = fields.Char(string=_('codigo'))

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		recs = self.browse()
		if name:
			recs = self.search(['|',('code', '=', name),('name','=',name)] + args, limit=limit)
		if not recs:
			recs = self.search(['|',('code', operator, name),('name',operator,name)] + args, limit=limit)
		return recs.name_get()

	def name_get(self):
		result = []
		for einv in self:
			name = '('+ einv.code +')'+ ' ' + einv.name
			result.append((einv.id, name))
		return result