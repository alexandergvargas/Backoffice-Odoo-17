# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountDiffDestinoAnaliticaView(models.Model):
	_name = 'account.diff.destino.analitica.view'
	_description = 'Account Diff Destino Analitica View'
	_auto = False
	
	aml_id = fields.Integer(string='AML ID')
	am_id = fields.Integer(string='AM ID')
	fecha = fields.Date(string='Fecha')
	diario = fields.Char(string='Diario')
	asiento = fields.Char(string='Asiento')
	cuenta = fields.Char(string='Cuenta')
	monto_conta = fields.Float(string='Monto En Contabilidad',digits=(12,2))
	monto_analiticas = fields.Float(string='Monto En Analitica',digits=(12,2))
	diferencia = fields.Float(string='Diferencia',digits=(12,2))

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				select row_number() OVER () AS id,T.* FROM (
					select a2.id as aml_id,
					a4.id as am_id,
					a4.date as fecha,
					a5.name as diario,
					a4.name as asiento,
					a3.code as cuenta,
					a2.balance as monto_conta,
					a1.monto  as monto_analiticas,
					abs(a2.balance)-abs(a1.monto) as diferencia 
					from 
					(
					select  move_line_id,sum(round(amount,2)) as monto  from account_analytic_line where company_id=1
					and (date between '2020/01/01' and '2020/01/01')
					group by move_line_id) a1

					left join account_move_line a2 on a2.id=a1.move_line_id
					left join account_account a3 on a3.id=a2.account_id
					left join account_move a4 on a4.id=a2.move_id
					left join account_journal a5 on a5.id=a4.journal_id
					where (abs(a2.balance)-abs(a1.monto))<>0   
					order by a4.date,a5.name,a4.name
				)T
			
			)''' % (self._table,)
		)