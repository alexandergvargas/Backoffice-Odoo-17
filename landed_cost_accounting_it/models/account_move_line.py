# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    invoice_date_landed = fields.Date(
        string=_('Fecha Factura'),
        related='move_id.invoice_date'
    )

    is_landed = fields.Boolean(
        string=_('Usa GV'), 
        related='product_id.product_tmpl_id.is_landed_cost'
    )

    landed_cost_id = fields.Many2one(
        string=_('Gasto Vinculado'),
        comodel_name='landed.cost.it',
        related='move_id.landed_cost_id',
        store=True
    )