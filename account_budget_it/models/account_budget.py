# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CrossoveredBudget(models.Model):
	_inherit = 'crossovered.budget'

	@api.onchange('date_from')
	def onchange_date_from(self):
		for budget in self:
			budget.crossovered_budget_line.date_from = budget.date_from

	@api.onchange('date_to')
	def onchange_date_to(self):
		for budget in self:
			budget.crossovered_budget_line.date_to = budget.date_to

class CrossoveredBudgetLines(models.Model):
	_inherit = 'crossovered.budget.lines'

	amount_diff = fields.Monetary(compute='_compute_amount_diff', string='Diferencia', store=True)

	def _compute_percentage(self):
		for line in self:
			if line.planned_amount != 0.00:
				line.percentage = float((line.practical_amount or 0.0) / line.planned_amount)
			else:
				line.percentage = 0.00

	def _compute_amount_diff(self):
		for line in self:
			line.amount_diff = (line.planned_amount or 0) - (line.practical_amount or 0)