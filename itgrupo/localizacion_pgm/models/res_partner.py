# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company,
                                 readonly=False)

    @api.onchange('name')
    def _onchange_name_lang(self):
        for cc in self:
            cc.lang = 'es_PE'


    @api.onchange('vat')
    def _renombrar_ref(self):
        for rec in self:
            rec.ref = rec.vat

    @api.constrains('vat')
    def _check_duplicate_partner(self):
        for rec in self:
            if rec.vat:

                existing_partner = self.env['res.partner'].search([
                    ('vat', '=', rec.vat),
                    ('id', '!=', rec.id),
                    ('company_id', '=', rec.company_id.id),
                    ('active', '=', True)
                ], limit=1)

                if existing_partner:
                    raise ValidationError(
                        f'Ya existe un Partner creado con el mismo documento {existing_partner.vat} en la compañía: {existing_partner.company_id.name}')

    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        current_company = self.env.company
        domain += [('company_id', '=', current_company.id)]
        return super().search_fetch(domain, field_names, offset, limit, order)


class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'


    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company,
                                 readonly=True)