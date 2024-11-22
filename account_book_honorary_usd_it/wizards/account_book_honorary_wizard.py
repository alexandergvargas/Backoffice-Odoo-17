# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class AccountBookHonoraryWizard(models.TransientModel):
	_inherit = 'account.book.honorary.wizard'


	currency_id = fields.Many2one('res.currency', string='Moneda',required=True, default=lambda self: self.env.company.currency_id.id)


	


	def _get_sql(self,x_date_ini,x_date_end,x_company_id,x_date_type):
		if self.currency_id.name == 'PEN':
			sql = """select
				tt.periodo::character varying,
				tt.libro,
				tt.voucher,
				tt.fecha_e,
				tt.fecha_p,
				tt.td,
				tt.serie,
				tt.numero,
				tt.tdp,
				tt.docp,
				rp.name,
				tt.divisa,
				tt.tipo_c,
				tt.renta,
				tt.retencion,
				tt.neto_p,
				tt.periodo_p,
				tt.is_not_home
				from get_recxhon_1_1('%s','%s',%d,'%s') tt
				LEFT JOIN account_move am ON am.id = tt.am_id
				LEFT JOIN res_partner rp ON rp.id = am.partner_id
			""" % (x_date_ini.strftime('%Y/%m/%d'),x_date_end.strftime('%Y/%m/%d'),x_company_id,x_date_type)
		else:
			sql = """select
				tt.periodo::character varying,
				tt.libro,
				tt.voucher,
				tt.fecha_e,
				tt.fecha_p,
				tt.td,
				tt.serie,
				tt.numero,
				tt.tdp,
				tt.docp,
				rp.name,
				tt.divisa,
				tt.tipo_c,
				tt.renta,
				tt.retencion,
				tt.neto_p,
				tt.periodo_p,
				tt.is_not_home
				from get_recxhon_1_1_usd('%s','%s',%d,'%s') tt
				LEFT JOIN account_move am ON am.id = tt.am_id
				LEFT JOIN res_partner rp ON rp.id = am.partner_id
			""" % (x_date_ini.strftime('%Y/%m/%d'),x_date_end.strftime('%Y/%m/%d'),x_company_id,x_date_type)
		return sql

	