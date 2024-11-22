# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountAccountConfigLine(models.Model):
	_name = 'account.account.config.line'
	_description = 'AccountAccountConfigLine'

	name = fields.Char('nombre')

	config_sheet_id = fields.Many2one(
		string=_('config_id'),
		comodel_name='account.account.config',
		ondelete="cascade"
	)

	config_m_close_id = fields.Many2one(
		string=_('config_id'),
		comodel_name='account.account.config',
		ondelete="cascade"
	)

	config_type_it_id = fields.Many2one(
		string=_('config_id'),
		comodel_name='account.account.config',
		ondelete="cascade"
	)

	config_type_fe_id = fields.Many2one(
		string=_('config_id'),
		comodel_name='account.account.config',
		ondelete="cascade"
	)

	config_type_ptn_id = fields.Many2one(
		string=_('config_id'),
		comodel_name='account.account.config',
		ondelete="cascade"
	)

	#HOJA TRABAJO
	clasification_sheet = fields.Selection(
		string=_('Clasificación Hoja de Trabajo'),
		selection=[
		  	('0',u'Situación Financiera'),
			('1','Resultados por Naturaleza'),
			('2','Resultados por Función'),
			('3','Resultados'),
			('4','Cuenta de Orden'),
			('5','Cuenta de Mayor')
		],
	)
	#METODO CIERRE
	m_close = fields.Selection(
		string=_('Metodo de cierre'),
		selection=[
			('1','Costo de Ventas'),
			('2','Cierre Clase 9'),
			('3','Cierre Cuentas Resultados'),
			('4','Cierre de Activo y Pasivo')
		],
	)
	#ESTADO FINANCIERO
	account_type_it_id = fields.Many2one(
		string=_('Tipo Estado Financiero'),
		comodel_name='account.type.it',
	)
	#FLUJO EJECTIVO
	account_type_cash_id = fields.Many2one(
		string=_('Flujo Efectivo'),
		comodel_name='account.efective.type',
	)
	#PATRIMONIO NETO
	patrimony_id = fields.Many2one(
		string=_('Patrimonio Neto'),
		comodel_name='account.patrimony.type',
	)
	
	prefix = fields.Char(string=_('Prefijo'))
	
	field_type = fields.Selection(
		string=_('type'),
		selection=[
			('sheet', 'Clasificación Hoja de Trabajo'),
			('m_close', 'Metodo de cierre'),
			('type_it', 'Tipo Estado Financiero'),
			('fe_it', 'Tipo Flujo Ejectivo'),
			('pnt_it', 'Patrimonio Neto'),
		],
	)

	@api.model
	def create(self, values):
		result = super(AccountAccountConfigLine,self).create(values)
		for i in result:
			if i.config_sheet_id:
				i.field_type = 'sheet'		
			elif i.config_m_close_id:
				i.field_type = 'm_close'				
			elif i.config_type_it_id:
				i.field_type = 'type_it'
			elif i.account_type_cash_id:
				i.field_type = 'fe_it'
			elif i.patrimony_id:
				i.field_type = 'pnt_it'				     
		return result