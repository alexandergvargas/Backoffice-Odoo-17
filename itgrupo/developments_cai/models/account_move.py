from odoo import models, fields, api
from random import randint

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_default_color(self):
        return randint(1, 11)

    color = fields.Integer('Color', default=_get_default_color)


    tag_ids = fields.Many2many(
        comodel_name='crm.tag',
        relation='account_move_tag_rel',
        string="Etiquetas")

    tipo_ingreso = fields.Selection([('nuew_in', 'Nuevo Ingreso'),
                                     ('nuew_apli', 'No Aplica')
                                     ], string='Tipo de Ingreso', store=True, tracking=True)

    # employee_id = fields.Many2one('hr.employee', string='Líder Comercial',
    #                               domain=[('department_id.name', '=', 'ABOGADOS')], tracking=True)

    lider_comercial_id = fields.Many2one('lider.comercial', string='Líder Comercial',
                                         readonly=False, tracking=True)

    tipo_categ_service = fields.Selection([('admi_con', 'Administración contractual'),
                                           ('sumi_fo', 'Sumisión Formal'),
                                           ('fami_dia', 'Familiarización/Diagnóstico'),
                                           ('tra_di', 'Trato Directo'),
                                           ('cur_ta', 'Cursos y Talleres'),
                                           ('arbi', 'Arbitraje'),
                                           ('anu_lau', 'Anulación de laudo'),
                                           ('eje_lau', 'Ejecución de Laudo'),
                                           ('med_cau', 'Medida cautelar'),
                                           ('opi_le', 'Opinión legal')
                                           ], string='Categoría del servicio', store=True, tracking=True)

    tipo_pacto = fields.Selection([('cuota', 'Cuota'),
                                   ('hito', 'Hito'),
                                   ('hora_adi', 'Horas Adicionales'),
                                   ('mo_fi', 'Monto Fijo'),
                                   ('no_apli', 'No Aplica'),
                                   ('paque', 'Paquete'),
                                   ('por_ho', 'Por Horas')
                                   ], string='Tipo de Pacto de Honorario', store=True, tracking=True)

    grupo_cliente_id = fields.Many2one('grupo.partner',string='Grupo Cliente 1', tracking=True, store=True)
    grupo_cliente_id_02 = fields.Many2one('grupo.partner', string='Grupo Cliente 2', tracking=True, store=True)
    grupo_cliente_id_03 = fields.Many2one('grupo.partner', string='Grupo Cliente 3', tracking=True, store=True)
    code_project = fields.Char(string='Codigo de Proyecto', tracking=True, store=True)
    tipo_factura_cai = fields.Selection([('invoice_cai', 'Facturado'),
                                         ('invoice_cai_he', 'Facturado H.E'),
                                         ], string='Tipo de Factura', store=True, tracking=True)

