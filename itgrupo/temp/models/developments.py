from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # employee_sale_id = fields.Many2one('hr.employee', string='Líder Comercial',domain=[('department_id.name', '=','ABOGADOS')])
    # employee_purchase_id = fields.Many2one('hr.employee', string='Equipo de Facturacion',domain=[('department_id.name', '=','ABOGADOS')])
    # grupo_cliente_id = fields.Many2one('grupo.partner',string='Grupo Cliente', tracking=True, store=True)
    # lider_comercial_sale_id = fields.Many2one('lider.comercial', string='Líder Comercial')
    # lider_comercial_purchase_id = fields.Many2one('lider.comercial', string='Equipo de Facturacion')
    grupo_cliente_id_02 = fields.Many2one('grupo.partner', string='Grupo Cliente 2', tracking=True, store=True)
    grupo_cliente_id_03 = fields.Many2one('grupo.partner', string='Grupo Cliente 3', tracking=True, store=True)