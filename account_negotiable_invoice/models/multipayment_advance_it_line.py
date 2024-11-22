# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MultipaymentAdvanceItLine(models.Model):
    _inherit = 'multipayment.advance.it.line'


    descrip = fields.Char(string=_('Descripción'), compute='_compute_descrip',readonly=False)
    

    
    @api.depends('invoice_id','invoice_id.name')
    def _compute_descrip(self):
        for i in self:
            if i.invoice_id.name:
                i.descrip = i.invoice_id.name
            else:
                i.descrip = ''
    