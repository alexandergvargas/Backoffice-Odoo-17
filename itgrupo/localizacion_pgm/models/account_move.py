# -*- coding: utf-8 -*-
import logging
from odoo import fields, api, models, _
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    tipo_financiamiento = fields.Selection([('fina_ban', 'Financiamiento Bancos'),
                                            ('fon_cole', 'Fondo Colectivo'),
                                            ('pago_inme', 'Pago Inmediato')
                                            ], string='Tipo de Financiamiento', store=True)