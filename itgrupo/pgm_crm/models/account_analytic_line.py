# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo import api, Command, fields, models, _
from odoo.osv import expression
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    crm_id = fields.Many2one('crm.lead', 'Oportunidad', store=True, readonly=False, domain="[('company_id', '=', company_id)]")
