from random import randint

from odoo import models, fields

class GrupoPartner(models.Model):
    _name = 'grupo.partner'
    _description = 'Grupos de Clientes'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', required=True)
    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company,
                                 readonly=True)

class LiderComercial(models.Model):
    _name = 'lider.comercial'
    _description = 'Lider Comerciales'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', required=True)
    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company,
                                 readonly=True)
    def _get_default_color(self):
        return randint(1, 11)

    color = fields.Integer('Color', default=_get_default_color)
