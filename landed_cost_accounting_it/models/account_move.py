# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    landed_cost_id = fields.Many2one(
        string=_('Gasto Vinculado'),
        comodel_name='landed.cost.it',
    )