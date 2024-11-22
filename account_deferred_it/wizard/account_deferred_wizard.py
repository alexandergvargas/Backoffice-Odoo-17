# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import *
import datetime
from odoo.tools import frozendict, format_date, float_compare, Query

class account_deferred_wizard(models.TransientModel):
	_name = 'account.deferred.wizard'
	_description = 'Modelos diferidos Reporte'


	
	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final')
	type = fields.Selection([
		('income', 'Ingreso'),
		('expense','Gastos')
	], string='Tipo')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	
	def get_report(self):
		self.env.cr.execute("""
					SELECT 
						adl.id as deferrend_line_id 
					FROM account_deferred_line adl 
					LEFT join account_deferred af on af.id = adl.account_deferred_id
					WHERE af.state != 'draft'
					AND (adl.date between '%s' and '%s') 
					AND af.company_id = %d
					AND adl.move_id is null
					AND af.type = '%s'""" % (	self.period_from.date_start.strftime('%Y/%m/%d'),
													self.period_from.date_end.strftime('%Y/%m/%d'),
													self.env.company.id,
													self.type))
		res = self.env.cr.dictfetchall()
		elem = []
		for key in res:
			elem.append(key['deferrend_line_id'])
			line = self.env['account.deferred.line'].browse(key['deferrend_line_id'])
			if line:
				line.post_line()
		return {
				'name': 'Generar Asientos Contables',
				'type': 'ir.actions.act_window',
				'domain' : [('id','in',elem)],
				'res_model': 'account.deferred.line',
				'view_mode': 'tree',
				'views': [(False, 'tree')],
			}

		
