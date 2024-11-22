from odoo import models, fields, api

class Ventas(models.Model):
    _inherit = 'sale.order'

    servicio_sale = fields.Char(string='Servicio', store=True)
    plantilla_term = fields.Many2one('plantilla.reporte', string="Plantilla Term. y Condiciones")
    leyenda = fields.Html(string='Leyenda', related='plantilla_term.leyenda')
    plantilla_reporte = fields.Html(string="Terminos y Condiciones")
    plantilla_reporte_rem = fields.Html(string="Terminos y Condiciones", compute='_set_plantilla')
    total_letras = fields.Char(compute="to_integer_letras")

    dia = fields.Char(compute="get_data_print")
    mes = fields.Char(compute="get_data_print")
    ano = fields.Char(compute="get_data_print")

    def get_data_print(self):
        meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'setiembre', 'octubre',
                 'noviembre', 'diciembre']
        for record in self:
            dia = mes = ano = None
            if record.date_order:
                d = str(record.date_order).split(' ')
                d = str(d[0]).split('-')
                dia = str(d[2])
                mes = meses[int(d[1]) - 1]
                # ano = str(d[0])[2:]
                ano = str(d[0])
            record.dia = dia
            record.mes = mes
            record.ano = ano

    '''
    user_id_it = fields.Many2one('res.users')
    digital_signature = fields.Binary(string="Firma Vendedor", compute="get_digital_signature")
    user_id2_it = fields.Many2one('res.users')
    digital_signature2 = fields.Binary(string="Firma Vendedor", compute="get_digital_signature")

    term_new_line = fields.Boolean(default=False, string='Imprimir en una Hoja')
    '''

    @api.model
    def default_get(self, fields):
        res = super(Ventas, self).default_get(fields)
        plantilla = self.env['plantilla.reporte'].search([('is_default', '=', True)], limit=1)
        res.update({
            'plantilla_term': plantilla.id if plantilla else None
        })
        return res

    # funcion convierte  numero a  letras
    def numero_to_letras(self, numero):
        indicador = [("", ""), ("MIL", "MIL"), ("MILLON", "MILLONES"), ("MIL", "MIL"), ("BILLON", "BILLONES")]
        entero = int(numero)
        decimal = int(round((numero - entero) * 100))
        # print 'decimal : ',decimal
        contador = 0
        numero_letras = ""
        while entero > 0:
            a = entero % 1000
            if contador == 0:
                en_letras = self.convierte_cifra(a, 1).strip()
            else:
                en_letras = self.convierte_cifra(a, 0).strip()
            if a == 0:
                numero_letras = en_letras + " " + numero_letras
            elif a == 1:
                if contador in (1, 3):
                    numero_letras = indicador[contador][0] + " " + numero_letras
                else:
                    numero_letras = en_letras + " " + indicador[contador][0] + " " + numero_letras
            else:
                numero_letras = en_letras + " " + indicador[contador][1] + " " + numero_letras
            numero_letras = numero_letras.strip()
            contador = contador + 1
            entero = int(entero / 1000)

        d = str(decimal)
        if len(d) == 1:
            d = '0' + str(d)

        numero_letras = numero_letras + " con " + d + "/100"
        # print ('numero: ',numero)
        return numero_letras

    def convierte_cifra(self, numero, sw):
        lista_centana = ["", ("CIEN", "CIENTO"), "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS",
                         "SEISCIENTOS",
                         "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]
        lista_decena = ["", (
            "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE"),

                        ("VEINTE", "VEINTI"), ("TREINTA", "TREINTA Y "), ("CUARENTA", "CUARENTA Y "),

                        ("CINCUENTA", "CINCUENTA Y "), ("SESENTA", "SESENTA Y "),

                        ("SETENTA", "SETENTA Y "), ("OCHENTA", "OCHENTA Y "),

                        ("NOVENTA", "NOVENTA Y ")

                        ]

        lista_unidad = ["", ("UN", "UNO"), "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE"]
        centena = int(numero / 100)
        decena = int((numero - (centena * 100)) / 10)
        unidad = int(numero - (centena * 100 + decena * 10))
        # print "centena: ",centena, "decena: ",decena,'unidad: ',unidad
        texto_centena = ""
        texto_decena = ""
        texto_unidad = ""
        # Validad las centenas
        texto_centena = lista_centana[centena]
        if centena == 1:
            if (decena + unidad) != 0:
                texto_centena = texto_centena[1]
            else:
                texto_centena = texto_centena[0]
        # Valida las decenas
        texto_decena = lista_decena[decena]
        if decena == 1:
            texto_decena = texto_decena[unidad]
        elif decena > 1:
            if unidad != 0:
                texto_decena = texto_decena[1]
            else:
                texto_decena = texto_decena[0]
        # Validar las unidades
        # print "texto_unidad: ",texto_unidad
        if decena != 1:
            texto_unidad = lista_unidad[unidad]
            if unidad == 1:
                texto_unidad = texto_unidad[sw]
        return "%s %s %s" % (texto_centena, texto_decena, texto_unidad)

    # @api.onchange('plantilla_term')
    # def change_plantilla_term(self):
    #     self.term_condiciones = self.plantilla_term.contenido

    def to_integer_letras(self):
        for s in self:
            s.total_letras = str(self.numero_to_letras(s.amount_total)) + " " + str(s.currency_id.currency_unit_label)

    # signature_up = fields.Binary(string="Firma Vendedor", related="user_id.signature_up")
    '''
    @api.onchange('digital_signature')
    def get_digital_signature(self):
        for record in self:
            if record.user_id_it.signature_up:
                record.digital_signature = record.user_id_it.signature_up
            else:
                record.digital_signature = record.user_id_it.digital_signature
            if record.user_id2_it.signature_up:
                record.digital_signature2 = record.user_id2_it.signature_up
            else:
                record.digital_signature2 = record.user_id2_it.digital_signature
    '''

    @api.onchange('plantilla_term')
    def change_plantilla(self):
        self.plantilla_reporte = self.plantilla_term.contenido

    @api.depends('plantilla_reporte')
    def _set_plantilla(self):
        # buscar la plantilla
        if self.plantilla_reporte:
            contenido = self.plantilla_reporte
            contenido = contenido.replace('@facturar', str(self.partner_invoice_id.name))
            contenido = contenido.replace('@ruc_factura', str(self.partner_invoice_id.vat))
            contenido = contenido.replace('@direccion_factura', str(self.partner_invoice_id.contact_address))
            contenido = contenido.replace('@telefono_factura', str(self.partner_invoice_id.phone))
            contenido = contenido.replace('@cliente', str(self.partner_id.name))
            contenido = contenido.replace('@cliente_email', str(self.partner_id.email))
            contenido = contenido.replace('@empresa_name', str(self.company_id.name))
            contenido = contenido.replace('@empresa_direccion', str(self.company_id.partner_id.contact_address))
            contenido = contenido.replace('@vendedor', str(self.user_id.name))
            contenido = contenido.replace('@vendedor_telefono', str(self.user_id.phone))
            contenido = contenido.replace('@empresa_email', str(self.user_id.company_id.email))
            contenido = contenido.replace('@empresa_web', str(self.user_id.company_id.website))
            contenido = contenido.replace('@ciudad', str(self.company_id.partner_id.district_id.name))
            contenido = contenido.replace('@dia', str(self.dia))
            contenido = contenido.replace('@mes', str(self.mes))
            contenido = contenido.replace('@año', str(self.ano))
            contenido = contenido.replace('@name', str(self.name))
            contenido = contenido.replace('@servicio', str(self.servicio_sale))
            self.plantilla_reporte_rem = contenido
        else:
            self.plantilla_reporte_rem = None

    def print_report_pgm(self):
        return self.env.ref('developments_pgm.report_sale_order_plantilla_reperte_id').report_action(self)