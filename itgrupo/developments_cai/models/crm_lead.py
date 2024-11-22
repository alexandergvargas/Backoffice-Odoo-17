from http.cookiejar import domain_match

from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    color = fields.Integer('Color Index', related='lider_comercial_id.color')

    date_solicitud = fields.Date(string='Fecha de solicitud', tracking=True, store=True)
    date_send_pro = fields.Date(string='Fecha de envio de propuesta', tracking=True, store=True)

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

    lider_comercial_id = fields.Many2one('lider.comercial', string='Líder Comercial',
                                  readonly=False, tracking=True)



    tipo_ingreso = fields.Selection([('nuew_in', 'Nuevo Ingreso'),
                                     ('nuew_apli', 'No Aplica')
                                     ], string='Tipo de Ingreso', store=True, tracking=True)

    grupo_cliente_id = fields.Many2one('grupo.partner',string='Grupo Cliente 1', tracking=True, store=True, readonly=False, compute='_onchange_name')
    grupo_cliente_id_02 = fields.Many2one('grupo.partner', string='Grupo Cliente 2', tracking=True, store=True, compute='_onchange_name')
    grupo_cliente_id_03 = fields.Many2one('grupo.partner', string='Grupo Cliente 3', tracking=True, store=True,  compute='_onchange_name')



    @api.depends('name')
    def _onchange_name(self):
        for record in self:
            record.grupo_cliente_id = record.partner_id.grupo_cliente_id
            record.grupo_cliente_id_02 = record.partner_id.grupo_cliente_id_02
            record.grupo_cliente_id_03 = record.partner_id.grupo_cliente_id_03


    tipo_factura_cai = fields.Selection([('invoice_cai', 'Facturado'),
                                         ('invoice_cai_he', 'Facturado H.E'),
                                         ], string='Tipo de Factura', store=True, tracking=True)

    def action_new_quotation(self):
        action = super(CrmLead, self).action_new_quotation()
        action['context']['search_default_tag_ids'] = self.tag_ids
        action['context']['search_default_tipo_ingreso'] = self.tipo_ingreso
        action['context']['search_default_lider_comercial_id'] = self.lider_comercial_id.id
        action['context']['search_default_tipo_categ_service'] = self.tipo_categ_service
        action['context']['search_default_tipo_pacto'] = self.tipo_pacto
        action['context']['search_default_grupo_cliente_id'] = self.grupo_cliente_id.id
        action['context']['search_default_grupo_cliente_id_02'] = self.grupo_cliente_id_02.id
        action['context']['search_default_grupo_cliente_id_03'] = self.grupo_cliente_id_03.id
        action['context']['search_default_tipo_factura_cai'] = self.tipo_factura_cai
        return action

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
