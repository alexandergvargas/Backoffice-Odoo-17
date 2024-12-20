# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from io import BytesIO

class AccountSunatWizard(models.TransientModel):
	_inherit = 'account.sunat.wizard'
	
	move_opening_id = fields.Many2one('account.move',string='Asiento Apertura')
	
	def get_ple_asset_71(self):
		wizard = self.env['account.asset.71.rep'].create({
			'fiscal_year_id': self.period_id.fiscal_year_id.id,
			'period': self.period_id.id,
			'company_id': self.company_id.id,
		})

		return wizard.get_ple(self.move_opening_id.id)
	
	def get_ple_excel_asset_71(self):
		wizard = self.env['account.asset.71.rep'].create({
			'fiscal_year_id': self.period_id.fiscal_year_id.id,
			'period': self.period_id.id,
			'company_id': self.company_id.id,
		})

		return wizard.get_excel_ple(self.move_opening_id.id)
	
	def get_ple_asset_74(self):
		wizard = self.env['account.asset.74.rep'].create({
			'fiscal_year_id': self.period_id.fiscal_year_id.id,
			'period': self.period_id.id,
			'company_id': self.company_id.id,
		})

		return wizard.get_ple()
	
	def get_ple_excel_asset_74(self):
		wizard = self.env['account.asset.74.rep'].create({
			'fiscal_year_id': self.period_id.fiscal_year_id.id,
			'period': self.period_id.id,
			'company_id': self.company_id.id,
		})

		return wizard.get_excel_ple()