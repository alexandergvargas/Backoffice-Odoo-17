
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero
import base64

class AccountAssetCategory(models.Model):
	_name = 'account.asset.category'
	_description = 'Asset category'
	_inherit = "analytic.mixin"

	active = fields.Boolean(default=True)
	name = fields.Char(required=True, index=True, string="Categoria de Activo")
	analytic_distribution = fields.Json(
		string=u'Distribución Analítica',
		compute="_compute_analytic_distribution", store=True, copy=True, readonly=False,
		precompute=True
	)
	def _compute_analytic_distribution(self):
		pass
	#analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Etiqueta Analitca')
	account_asset_id = fields.Many2one('account.account', string='Cuenta de Activo', required=True, domain=[('account_type','=','asset_fixed'), ('deprecated', '=', False)], help="Account used to record the purchase of the asset at its original price.")
	account_depreciation_id = fields.Many2one('account.account', string='Cuenta de Depreciacion', required=True, domain=[('account_type','=','asset_fixed'), ('deprecated', '=', False)], help="Account used in the depreciation entries, to decrease the asset value.")
	account_depreciation_expense_id = fields.Many2one('account.account', string='Cuenta de Gasto Depreciacion', required=True, domain=[('account_type','=','expense_depreciation'), ('deprecated', '=', False)], help="Account used in the periodical entries, to record a part of the asset as expense.")
	account_retire_id = fields.Many2one('account.account', string='Cuenta de Retiro', domain=[('account_type','=','expense'), ('deprecated', '=', False)])
	journal_id = fields.Many2one('account.journal', string='Diario', required=True)
	company_id = fields.Many2one('res.company', string=u'Compañia', required=True, default=lambda self: self.env['res.company']._company_default_get('account.asset.category'))
	method = fields.Selection([('linear', 'Linear'), ('degressive', 'Degressive')], string='Metodo de Calculo', required=True, default='linear')
	method_number = fields.Integer(string='Numero de Entradas', default=5, help="The number of depreciations needed to depreciate your asset")
	method_period = fields.Integer(string='Una Entrada Cada', default=1, help="State here the time between 2 depreciations, in months", required=True)
	method_progress_factor = fields.Float('Degressive Factor', default=0.3)
	method_time = fields.Selection([('number', 'Numero de Entradas'), ('end', 'Ultimo Dia')], string='Tiempo Basado En', required=True, default='number')
	method_end = fields.Date('Ending date')
	prorata = fields.Boolean(string='Prorata Temporis', help='Indicates that the first depreciation entry for this asset have to be done from the purchase date instead of the first of January')
	open_asset = fields.Boolean(string='Auto-Confirmar Activos', help="Check this if you want to automatically confirm the assets of this category when created by invoices.")
	group_entries = fields.Boolean(string='Agrupar Entradas de Diario', help="Check this if you want to group the generated entries by categories.")
	type = fields.Selection([('sale', 'Sale: Revenue Recognition'), ('purchase', 'Purchase: Asset')], required=True, index=True, default='purchase')
	date_first_depreciation = fields.Selection([
		('last_day_period', 'Primer Dia del Mes Siguiente'),
		('manual', 'Manual')],
		string=u'Inicio de Depreciacion', default='manual', required=True)
	depreciation_rate = fields.Float(string=u'Tasa de Depreciación')

	@api.onchange('account_asset_id')
	def onchange_account_asset(self):
		if self.type == "purchase":
			self.account_depreciation_id = self.account_asset_id
		elif self.type == "sale":
			self.account_depreciation_expense_id = self.account_asset_id

	@api.onchange('depreciation_rate')
	def onchange_depreciation_rate(self):
		if self.depreciation_rate and self.depreciation_rate != 0:
			self.method_number = (100/(self.depreciation_rate))*12

	@api.onchange('type')
	def onchange_type(self):
		if self.type == 'sale':
			self.prorata = True
			self.method_period = 1
		else:
			self.method_period = 1

	@api.onchange('method_time')
	def _onchange_method_time(self):
		if self.method_time != 'number':
			self.prorata = False
