# -*- coding: utf-8 -*-
import itertools
from odoo import api, fields, models, tools, _, SUPERUSER_ID
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @tools.ormcache()
    def _get_default_category_id(self):
        print('Print')
        # return self.env.ref('product.product_category_all')


    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company,
                                 readonly=True)

    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True, default=_get_default_category_id, group_expand='_read_group_categ_id',
        required=True)


class ProductBrand(models.Model):
    _inherit = 'product.brand'


    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company,
                                 readonly=True)
