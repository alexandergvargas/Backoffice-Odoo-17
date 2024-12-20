# -*- encoding: utf-8 -*-

import codecs
import pprint
import codecs

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64


class importacion_actualizar_analiticos(models.TransientModel):
	_name='importacion.actualizar.analiticos'
	_description = 'Importacion Actualizar Analiticos'

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_id =fields.Many2one('account.period','Periodo',required=True)
	


	def primerpaso(self):
		self.env.cr.execute("""DELETE 
					 			FROM account_analytic_line 
					 			WHERE (date BETWEEN '%s' AND '%s') 
					 				AND company_id = %d """%(
						   		self.period_id.date_start.strftime('%Y/%m/%d'),
								self.period_id.date_end.strftime('%Y/%m/%d'),
								self.company_id.id))
		
		self.env.cr.execute("""SELECT aml.id
					 			FROM account_move_line aml
					  			left join account_move am on am.id=aml.move_id
					 			WHERE (am.date BETWEEN '%s' AND '%s') 
					 				AND am.company_id = %d 
					  				AND aml.analytic_distribution IS NOT NULL"""%(
						   		self.period_id.date_start.strftime('%Y/%m/%d'),
								self.period_id.date_end.strftime('%Y/%m/%d'),
								self.company_id.id))		
		res = self.env.cr.dictfetchall()
		move_lines  = []
		for ids in res:
			move_lines.append(ids['id'])		
		line_obj = self.env['account.move.line'].sudo().search([('id','in',move_lines)])
		for lines in line_obj:
			lines._inverse_analytic_distribution()

		return self.env['popup.it'].get_message(u'SE ACTUALIZARON CORRECTAMENTE LOS DIARIOS ANALÍTICOS')
			
		#self.env.cr.execute("""
		#	insert into account_analytic_line (
		#			account_id,
		#			company_id,
		#			amount,
		#			unit_amount,
		#			date,
		#			name,
		#			general_account_id,
		#			product_uom_id,
		#			product_id,
		#			ref,move_id,
		#			currency_id)
		#	select 
		#	a1.analytic_account_id as account_id,
		#	a1.company_id as company_id,
		#	case when a1.debit>0 then -a1.debit else a1.credit end as amount,
		#	0 as unit_amount,
		#	a2.date as date,
		#	coalesce(a1.name,'/') as name,
		#	account_id as general_account_id,
		#	null::numeric as product_uom_id,
		#	null::numeric as product_id,
		#	a2.ref as ref,
		#	a1.id as move_id,
		#	coalesce(a1.currency_id,162) as currency_id
		#	from account_move_line a1
		#	left join account_move a2 on a2.id=a1.move_id
		#	where a1.analytic_account_id is not null and
		#	a1.id not in (select aal.move_id from account_analytic_line aal where aal.company_id=%d)
		#	and (a2.date BETWEEN '%s' AND '%s') AND
		#	a2.company_id = %d"""% (self.company_id.id,
		#				   self.period_id.date_start.strftime('%Y/%m/%d'),
		#		self.period_id.date_end.strftime('%Y/%m/%d'),
		#		self.company_id.id))