# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

  
    @api.model
    def _action_sunat_exchange_rate_pgm(self):
        return self._action_sunat_exchange_rate()