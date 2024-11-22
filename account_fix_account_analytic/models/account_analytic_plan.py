# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountAnalyticPlan(models.Model):
	_inherit = 'account.analytic.plan'
	

	check_main = fields.Boolean(string=_('Plan Principal'), default=False)
	
	parent_id = fields.Many2one(
		'account.analytic.plan',
		string="Principal",
		inverse='_inverse_parent_id',
		ondelete='cascade',
		domain="[('check_main', '=', True)]"
	)

	@api.constrains('check_main')
	def _check_unique_check_main_default(self):
		if self.check_main:
			self.env.cr.execute("""select id from account_analytic_plan where check_main = True""")
			res = self.env.cr.dictfetchall()
			if len(res) == 1:
				raise UserError(u"Ya existe un Plan analítico como Principal.")

	def unlink(self):
		for i in self:
			if i.check_main:
				raise UserError("Imposible Eliminar un Plan Analitico Principal")
		return super(AccountAnalyticPlan, self).unlink()