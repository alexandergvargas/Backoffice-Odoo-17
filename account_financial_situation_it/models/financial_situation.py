# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class FinancialSituation(models.Model):
	_name = 'financial.situation'
	_auto = False
	_order = 'order_balance'

	name = fields.Char(string='Nombre')
	group_balance = fields.Char(string='Grupo')
	total = fields.Float(string='Total')
	order_balance = fields.Integer(string='Orden')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				select row_number() OVER () AS id,T.* FROM (
					  
					SELECT ati.name,
					ati.group_balance,
					case
						when ati.group_balance in ('B1','B2')
						then sum(a1.debe) - sum(a1.haber)
						else sum(a1.haber) - sum(a1.debe)
					end as total,
					ati.order_balance
					from get_sumas_mayor_f1('2020/01/01','2020/01/01',1,FALSE) a1
					left join account_account a2 on a2.id=a1.account_id
					left join account_type_it ati on ati.id = a2.account_type_it_id
					where ati.group_balance is not null
					group by ati.name,ati.group_balance,ati.order_balance
					order by ati.order_balance
							
				)T
			
			)''' % (self._table,)
		)