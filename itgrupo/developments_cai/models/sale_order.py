from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_opportunity_quotation_context(self):
        quotation_context = super(CrmLead, self)._prepare_opportunity_quotation_context()
        quotation_context['default_tipo_ingreso'] = self.tipo_ingreso
        quotation_context['default_lider_comercial_id'] = self.lider_comercial_id.id
        quotation_context['default_tipo_categ_service'] = self.tipo_categ_service
        quotation_context['default_tipo_pacto'] = self.tipo_pacto
        quotation_context['default_grupo_cliente_id'] = self.grupo_cliente_id.id
        quotation_context['default_grupo_cliente_id_02'] = self.grupo_cliente_id_02.id
        quotation_context['default_grupo_cliente_id_03'] = self.grupo_cliente_id_03.id
        quotation_context['default_tipo_factura_cai'] = self.tipo_factura_cai
        return quotation_context

    tipo_ingreso = fields.Selection([('nuew_in', 'Nuevo Ingreso'),
                                     ('nuew_apli', 'No Aplica')
                                     ], string='Tipo de Ingreso', store=True, tracking=True)

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
