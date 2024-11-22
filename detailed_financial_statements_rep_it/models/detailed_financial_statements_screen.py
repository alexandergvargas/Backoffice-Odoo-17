# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DetailedFinancialStatementsScreen(models.Model):
    _name = 'detailed.financial.statements.screen'
    _description = 'DetailedFinancialStatementsScreen'
    _auto = False 

    periodo = fields.Char(string=_('PERIODO'))
    libro = fields.Char(string=_('LIBRO'))    
    voucher = fields.Char(string=_('VOUCHER'))
    group = fields.Char(string=_('GRUPO'))
    account = fields.Char(string=_('CUENTA'))
    debe = fields.Float(string=_('DEBE'))
    haber = fields.Float(string=_('HABER'))
    balance = fields.Float(string=_('BALANCE'))
    amount_currency  = fields.Float(string=_('IMPORTE MONEDA'))
    currency_id = fields.Char(string=_('MONEDA'))
    date = fields.Date(
        string=_('FECHA'),
    )
    td = fields.Char(string=_('TD'))
    nro_comp = fields.Char(string=_('NRO_COMP'))
    type_ef = fields.Char(string=_('TIPO ESTADO FINANCIERO'))