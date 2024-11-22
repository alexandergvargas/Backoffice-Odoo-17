# -*- coding: utf-8 -*-

from odoo import fields, api, models, _

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company,
                                 readonly=True)