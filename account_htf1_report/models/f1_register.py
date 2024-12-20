# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class F1Register(models.Model):
	_name = 'f1.register'
	_description = 'F1 Register'
	_auto = False
	_order = 'mayor'

	date_from = fields.Date(string='Fecha Inicio')
	date_to = fields.Date(string='Fecha Final')
	mayor = fields.Char(string='Mayor')
	cuenta = fields.Char(string='Cuenta')
	nomenclatura = fields.Char(string='Nomenclatura')
	debe = fields.Float(string='Debe')
	haber = fields.Float(string='Haber')
	saldo_deudor = fields.Float(string='Saldo Deudor')
	saldo_acreedor = fields.Float(string='Saldo Acreedor')
	activo = fields.Float(string='Activo')
	pasivo = fields.Float(string='Pasivo')
	perdinat = fields.Float(string='Perdinat')
	ganannat = fields.Float(string='Ganannat')
	perdifun = fields.Float(string='Perdifun')
	gananfun = fields.Float(string='Gananfun')
	rubro = fields.Char(string='Rubro Estado Financiero')
	group_balance = fields.Char(string='Grupo Balance')
	group_nature = fields.Char(string='Grupo Naturaleza')
	group_function = fields.Char(string='Grupo Función')

	def view_detail(self):
		self.env.cr.execute("""SELECT aml.id as move_line_id FROM account_move_line aml 
		left join account_account aa on aa.id = aml.account_id
		left join account_move am on am.id = aml.move_id
		WHERE am.state = 'posted' 
		AND (am.date between '%s' and '%s') 
		AND aa.code = '%s'
		AND am.company_id = %d""" % (self.date_from.strftime('%Y/%m/%d'),self.date_to.strftime('%Y/%m/%d'),self.cuenta,self.env.company.id))
		res = self.env.cr.dictfetchall()
		elem = []
		for key in res:
			elem.append(key['move_line_id'])

		return {
			'name': 'Detalle',
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.line',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': '_blank',
		}
	
	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id, T.* FROM (
					select 
			left(a2.code,2) as mayor,
			a2.code as cuenta,
			a2.name as nomenclatura,
			a1.debe,
			a1.haber,
			case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end as saldo_deudor,
			case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end as saldo_acreedor,
			case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end as activo,
			case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end as pasivo,
			case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end as perdinat,
			case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end as ganannat,
			case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end as perdifun,
			case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end as gananfun,
			ati.name as rubro,
			ati.group_balance,
			ati.group_nature,
			ati.group_function
			from get_sumas_mayor_f1('2019/01/01','2019/01/01',1,TRUE) a1
			left join account_account a2 on a2.id=a1.account_id
			left join account_type_it ati on ati.id = a2.account_type_it_id
			order by a2.code
				)T limit 1
			
			)''' % (self._table,)
		)