# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountPatrimonyBook(models.Model):
	_name = 'account.patrimony.book'
	_auto = False
	
	glosa = fields.Char(string='Conceptos')
	capital = fields.Float(string='Capital', digits=(64,2))
	acciones = fields.Float(string='Acciones de Inversion', digits=(64,2))
	cap_add = fields.Float(string='Capital Adicional', digits=(64,2))
	res_no_real = fields.Float(string='Resultados no Realizados', digits=(64,2))
	exce_de_rev = fields.Float(string='Excedente de Revaluacion', digits=(64,2))
	reservas = fields.Float(string='Reservas', digits=(64,2))
	res_ac = fields.Float(string='Resultados Acumulados', digits=(64,2))
	total = fields.Float(string='Totales', digits=(64,2))

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				select row_number() OVER () AS id,T2.* FROM (
				SELECT am.glosa, T.capital, T.acciones,T.cap_add,T.res_no_real,
				T.exce_de_rev, T.reservas, T.res_ac, T.total FROM(SELECT 
				aml.move_id,
				SUM(CASE WHEN apt.code='001' THEN -aml.balance ELSE 0 END) AS capital,
				SUM(CASE WHEN apt.code='002' THEN -aml.balance ELSE 0 END) AS acciones,
				SUM(CASE WHEN apt.code='003' THEN -aml.balance ELSE 0 END) AS cap_add,
				SUM(CASE WHEN apt.code='004' THEN -aml.balance ELSE 0 END) AS res_no_real,
				SUM(CASE WHEN apt.code='005' THEN -aml.balance ELSE 0 END) AS exce_de_rev,
				SUM(CASE WHEN apt.code='006' THEN -aml.balance ELSE 0 END) AS reservas,
				SUM(CASE WHEN apt.code='007' THEN -aml.balance ELSE 0 END) AS res_ac,
				SUM(-aml.balance) AS total
				FROM account_move_line aml
				LEFT JOIN account_account aa ON aa.id=aml.account_id
				LEFT JOIN account_move am on am.id = aml.move_id
				LEFT JOIN  account_patrimony_type apt ON apt.id = aa.patrimony_id
				WHERE left(aa.code,1)='5' AND (am.date between '2020/01/01' AND '2020/01/01')
				AND (right(periodo_de_fecha(am.date,am.is_opening_close)::character varying,2)::integer between '00'::integer and '12'::integer)
				AND am.company_id = 1 AND am.state = 'posted' 
				GROUP BY aml.move_id)T
				LEFT JOIN account_move am ON am.id = T.move_id
				ORDER BY am.date
				)T2
			
			)''' % (self._table,)
		)