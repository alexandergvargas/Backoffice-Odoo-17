# -*- coding: utf-8 -*-

from odoo import fields, api, models, _

class CrmStage(models.Model):
    _inherit = 'crm.stage'

    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company, readonly=True)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    my_custom_currency_id = fields.Many2one('res.currency', string='Moneda', default=1, store=True)


class CrmStag(models.Model):
    _inherit = 'crm.tag'

    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company, readonly=True)
