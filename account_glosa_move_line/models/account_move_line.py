# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
   
    @api.depends('product_id','move_id','move_id.glosa')
    def _compute_name(self):
        for i in self:
            res = super(AccountMoveLine, i)._compute_name()
            if not i.name:
                if i.move_id.glosa:
                    i.name=i.move_id.glosa
            return res
