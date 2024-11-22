from odoo import models, fields, api

class ModeloReporte(models.Model):
    _name = 'plantilla.reporte'


    name = fields.Char(required=True)
    is_default = fields.Boolean(string="Por Defecto")
    contenido = fields.Html()
    leyenda = fields.Html(compute="get_leyenda")
    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company,
                                 readonly=True)

    @api.depends('leyenda')
    def get_leyenda(self):
        for record in self:
            record.leyenda = '''
                    <strong>@facturar:</strong> Persona a facturar<br/>
                    <strong>@ruc_factura:</strong> Ruc de la factura<br/>
                    <strong>@direccion_factura:</strong> Dirección de la factura<br/>
                    <strong>@telefono_factura:</strong> Telefono de la Factura<br/>
                    <strong>@cliente:</strong></strong> Nombre del Cliente<br/>
                    <strong>@cliente_email:</strong> Correo del cliente<br/>
                    <strong>@empresa_name:</strong> Nombre de la compañía<br/>
                    <strong>@empresa_direccion:</strong> Dirección de la empresa<br/>
                    <strong>@vendedor:</strong> Nombre del vendedor<br/>
                    <strong>@vendedor_telefono:</strong> Celular del vendedor<br/>
                    <strong>@empresa_email:</strong> Correo de la empresa<br/>
                    <strong>@empresa_web:</strong> Página web de la empresa<br/>
                    <strong>@año:</strong> Año<br/>
                    <strong>@mes:</strong> Mes<br/>
                    <strong>@dia:</strong> Día<br/>
                    <strong>@ciudad:</strong> Ciudad de la compañia<br/>
                    <strong>@name:</strong> Número de la Orden<br/>
                    <strong>@servicio:</strong> Nombre del Servicio

                    '''
