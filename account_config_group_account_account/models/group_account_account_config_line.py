# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountAccountConfigLine(models.Model):
	_name = 'group.account.account.config.line'
	_description = 'AccountAccountConfigLine'

	name = fields.Char('nombre')

	main_id = fields.Many2one(
		string=_('config_id'),
		comodel_name='group.account.account.config',
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
	
	
	prefix = fields.Char(string=_('Prefijo'))
	
	
	