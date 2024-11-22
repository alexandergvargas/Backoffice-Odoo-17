# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MultipaymentAdvanceIt(models.Model):
    _inherit = 'multipayment.advance.it'


    def direct_form_wizard_move(self):
        for i in self:
              return {
                    'name': 'Facturas Negociales',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'move.invoice.cash',
                    'context': {'default_multipayment_advance_id': i.id},
                    'target': 'new',
                }