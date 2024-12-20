# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date, get_lang

class AccountBalancePeriodBook(models.Model):
	_name = 'account.balance.period.book'
	_description = 'Account Balance Period Book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	fecha_con = fields.Date(string='Fecha Con')
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	td_partner = fields.Char(string='TDP', size=50)
	doc_partner = fields.Char(string='RUC',size=50)
	partner = fields.Char(string='Partner')
	td_sunat = fields.Char(string='TD',size=3)
	nro_comprobante = fields.Char(string='Nro Comp', size=50)
	fecha_doc = fields.Date(string='Fecha Doc')
	fecha_ven = fields.Date(string='Fecha Ven')
	cuenta = fields.Char(string='Cuenta')
	moneda = fields.Char(string='Moneda')
	monto_ini_mn = fields.Float(string='Saldo Inicial MN', digits=(64,2))
	monto_ini_me = fields.Float(string='Saldo Inicial ME', digits=(64,2))
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
	saldo_mn = fields.Float(string='Saldo Mn', digits=(64,2))
	saldo_me = fields.Float(string='Saldo Me', digits=(64,2))
	partner_id = fields.Many2one('res.partner',string='Partner ID')
	account_id = fields.Many2one('account.account',string='Cuenta ID')
	
	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT a1.* FROM get_saldos('2019/01/01','2019/01/01',1) a1 limit 1
			
			)''' % (self._table,)
		)

	def action_view_move_line(self):
		if len(self)>1:
			raise UserError(u'Solo puede seleccionar un item.')
		return {
			'name': 'Detalle Apuntes Contables',
			'domain' : [('date','>=', self.env.context.get('default_date_from')),('date','<=', self.env.context.get('default_date_to')),('partner_id','=',self.partner_id.id),('account_id','=',self.account_id.id),('nro_comp','=',self.nro_comprobante),('type_document_id','=',self.env['l10n_latam.document.type'].search([('code','=',self.td_sunat)],limit=1).id)],
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.line',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': '_blank',
		}