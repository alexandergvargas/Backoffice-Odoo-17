# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountExchangeDocumentCurrencyView(models.Model):
	_name = 'account.exchange.document.currency.view'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	cuenta = fields.Char(string='Cuenta')
	partner = fields.Char(string='Partner', size=150)
	td_sunat = fields.Char(string='TD', size=3)
	nro_comprobante = fields.Char(string='Nro. Comprobante', size=3)
	debe = fields.Float(string='Debe',digits=(12,2))
	haber = fields.Float(string='Haber',digits=(12,2))
	saldomn = fields.Float(string='Saldo MN',digits=(12,2))
	saldome = fields.Float(string='Saldo ME',digits=(12,2))
	tc = fields.Float(string='TC',digits=(12,3))
	saldo_act = fields.Float(string='Saldo Act.',digits=(12,2))
	diferencia = fields.Float(string='Diferencia',digits=(12,2))
	cuenta_diferencia = fields.Char(string='Cuenta Diferencia')
	account_id = fields.Many2one('account.account',string='Cuenta ID')
	currency_id = fields.Many2one('res.currency',string='Moneda')
	partner_id = fields.Many2one('res.partner',string='Partner ID')
	period_id = fields.Many2one('account.period',string='Periodo ID')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				select row_number() OVER () AS id,T.* FROM (
				SELECT
				'202000' as periodo,
				aa.code as cuenta,
				rp.name as partner,
				vst.td_sunat,
				vst.nro_comprobante,
				vst.debe,
				vst.haber,
				vst.saldomn,
				vst.saldome,
				vst.tc,
				vst.saldo_act,
				vst.diferencia,
				aa2.code as cuenta_diferencia,
				vst.account_id,
				aa.currency_id,
				vst.partner_id,
				null::integer as period_id
				FROM get_saldos_me_documento_final('2020','202000',1) vst
				LEFT JOIN account_account aa ON aa.id = vst.account_id
				LEFT JOIN account_account aa2 ON aa2.id = vst.difference_account_id
				LEFT JOIN res_partner rp ON rp.id = vst.partner_id
				WHERE vst.saldome = 0 
				)T
			
			)''' % (self._table,)
		)