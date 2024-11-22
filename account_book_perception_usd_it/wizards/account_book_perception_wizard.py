# -*- coding: utf-8 -*-

from socket import herror
from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class AccountBookPerceptionWizard(models.TransientModel):
	_inherit = 'account.book.perception.wizard'


	currency_id = fields.Many2one('res.currency', string='Moneda',required=True, default=lambda self: self.env.company.currency_id.id)
	
	#SI ES SOLES LO TOMA DEL AMOUNT CURRENCY
	#si ES OTRA MONEDA CONVERTIR
	def _get_sql(self,date_ini,date_end,company_id):
		if self.type == 'solo':
			if self.currency_id.name == 'PEN':
				sql = """SELECT periodo_con::CHARACTER varying, 
								periodo_percep::CHARACTER varying, 
								fecha_uso,
								libro,
								voucher,
								tipo_per,
								ruc_agente,
								partner,
								tipo_comp,
								serie_cp,
								numero_cp,
								fecha_com_per,
								percepcion
						FROM get_percepciones_sp('%s','%s',%d)
				""" % (date_ini.strftime('%Y/%m/%d'),
					date_end.strftime('%Y/%m/%d'),
					company_id)
			else:
				sql = """SELECT periodo_con::CHARACTER varying, 
								periodo_percep::CHARACTER varying, 
								fecha_uso,
								libro,
								voucher,
								tipo_per,
								ruc_agente,
								partner,
								tipo_comp,
								serie_cp,
								numero_cp,
								fecha_com_per,
								percepcion
						FROM get_percepciones_sp_usd('%s','%s',%d)
				""" % (date_ini.strftime('%Y/%m/%d'),
					date_end.strftime('%Y/%m/%d'),
					company_id)
		else:
			if self.currency_id.name == 'PEN':
				sql = """SELECT periodo_con::character varying, 
								periodo_percep::character varying, 
								fecha_uso, 
								libro,
								voucher, 
								tipo_per, 
								ruc_agente, 
								partner, 
								tipo_comp, 
								serie_cp, 
								numero_cp,
								fecha_com_per, 
								percepcion, 
								t_comp, 
								serie_comp, 
								numero_comp, 
								fecha_cp, 
								montof
						FROM get_percepciones('%s','%s',%d)
				""" % (date_ini.strftime('%Y/%m/%d'),
					date_end.strftime('%Y/%m/%d'),
					company_id)
			else:
				sql = """SELECT periodo_con::character varying, 
								periodo_percep::character varying, 
								fecha_uso, 
								libro,
								voucher, 
								tipo_per, 
								ruc_agente, 
								partner, 
								tipo_comp, 
								serie_cp, 
								numero_cp,
								fecha_com_per, 
								percepcion, 
								t_comp, 
								serie_comp, 
								numero_comp, 
								fecha_cp, 
								montof
						FROM get_percepciones_usd('%s','%s',%d;%d)
				""" % (date_ini.strftime('%Y/%m/%d'),
					date_end.strftime('%Y/%m/%d'),
					company_id,
					self.currency_id.id)
		
		return sql
	
