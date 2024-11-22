# -*- coding: utf-8 -*-

from odoo import fields, api, models, _

class ProductCategory(models.Model):
    _inherit = 'product.category'

    company_id = fields.Many2one('res.company', string=u'Compañia',default=lambda self: self.env.company, readonly=True)

