from http.cookiejar import domain_match

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    lider_comercial_sale_id = fields.Many2one('lider.comercial', string='Líder Comercial')
    lider_comercial_purchase_id = fields.Many2one('lider.comercial', string='Equipo de Facturacion')
    grupo_cliente_id = fields.Many2one('grupo.partner',string='Grupo Cliente 1', tracking=True, store=True)
    grupo_cliente_id_02 = fields.Many2one('grupo.partner', string='Grupo Cliente 2', tracking=True, store=True)
    grupo_cliente_id_03 = fields.Many2one('grupo.partner', string='Grupo Cliente 3', tracking=True, store=True)