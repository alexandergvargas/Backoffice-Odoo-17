# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
	_inherit = 'account.move'

	asset_depreciation_ids = fields.One2many('account.asset.depreciation.line', 'move_id', string='Assets Depreciation Lines', ondelete="restrict")

	def button_cancel(self):
		for move in self:
			for line in move.asset_depreciation_ids:
				line.move_posted_check = False
		return super(AccountMove, self).button_cancel()

	def _post(self, soft=True):
		posted = super()._post(soft)
		for move in self:
			for depreciation_line in move.asset_depreciation_ids:
				depreciation_line.post_lines_and_close_asset()
		return posted