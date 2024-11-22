from odoo import api, fields, models


class reporteclinicacorporal(models.Model):
    _name = "reporte.clinica.corporal"
    _description = "Reporte Corporal Clínica Zegarra"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    appointment_count = fields.Integer(string='Appointment Count', compute='_compute_appointment_count')
    order_ids = fields.One2many('sale.order', 'ficha_paciente_id', string='Orders')
    def _compute_appointment_count(self):
        for rec in self:
            appointment_count = self.env['sale.order'].search_count([('ficha_paciente_id', '=', rec.name)])
            rec.appointment_count = appointment_count

    def action_open_sales(self):
        action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
        action['context'] = {
            'search_default_draft': 1,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_ficha_paciente_id': self.id
        }
        action['domain'] = [('ficha_paciente_id', '=', self.id), ('state', 'in', ['draft', 'sent'])]
        quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent'))
        if len(quotations) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = quotations.id
        return action


    @api.model
    def create(self, vals):

        obj = super(reporteclinicacorporal, self).create(vals)

        number = self.env['ir.sequence'].get('mer.sequence.code.report.pgm') or '/'
        obj.write({'name': number})

        return obj

    state = fields.Selection([('new', 'Nuevo'), ('confirmado', 'Confirmado'),
                              ('cancelado', 'Cancelado')],
                             string="Estado", default='new', tracking=True)

    name = fields.Char(string='Nombre', default='Nuevo')
    image = fields.Image(max_width=1920, max_height=1920, compute='_cambio_imagen')
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id,
                                 required=True)

    @api.onchange('partner_id')
    def _cambio_imagen(self):
        for rec in self:
            rec.image = rec.partner_id.image_1920

    partner_id = fields.Many2one('res.partner', string='Nombres y Apellido', required=True)
    pago_consulta = fields.Char(string='Tipo Pago', tracking=True, required=True)
    fecha_consulta = fields.Date(string='Fecha', tracking=True, required=True)
    hora_consulta = fields.Char(string='Hora', tracking=True, required=True)

    id_cliente = fields.Char(string='ID', tracking=True, readonly=True, store=True)
    fecha_nacimiento = fields.Date(string='Fecha de Nacimiento', tracking=True, readonly=True, store=True)
    edad = fields.Char(string='Edad', tracking=True, readonly=True, store=True)
    tipo_hora = fields.Selection([('PM', 'PM'), ('AM', 'AM')],
                                 string="Hora", tracking=True, required=True)

    @api.onchange('partner_id')
    def cambio_cliente(self):
        for rec in self:
            if rec.partner_id:
                rec.id_cliente = rec.partner_id.vat
                # rec.fecha_nacimiento = rec.partner_id.fecha_nacimiento
                # rec.edad = rec.partner_id.edad
                rec.direccion_cliente = rec.partner_id.street
                rec.telefono_cliente = rec.partner_id.phone
                rec.correo_cliente = rec.partner_id.email
                rec.ocupacion_cliente = rec.partner_id.function

    nombre_cliente = fields.Char(string='Apellidos y Nombres', tracking=True, readonly=True, store=True)
    direccion_cliente = fields.Char(string='Dirección', tracking=True, readonly=True, store=True)
    telefono_cliente = fields.Char(string='Teléfono', tracking=True, readonly=True, store=True)
    correo_cliente = fields.Char(string='Correo', tracking=True, readonly=True, store=True)
    ocupacion_cliente = fields.Char(string='Ocupacion', tracking=True, readonly=True, store=True)
    consulta = fields.Char(string='Consulta', tracking=True, required=True)
    descripcion_consulta = fields.Text(string='Descripcion', tracking=True, required=True)



class reportecorporal(models.Model):
    _name = "reporte.corporal"
    _description = "Reporte Corporal Clínica Zegarra"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', default='Nuevo', tracking=True)

    @api.model
    def create(self, vals):
        obj = super(reportecorporal, self).create(vals)

        number = self.env['ir.sequence'].get('mer.sequence.reports.corporal') or '/'
        obj.write({'name': number})

        return obj

    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id,
                                 required=True)

    partner_id = fields.Many2one('res.partner', string='Nombres y Apellido', tracking=True)
    motivo_consul = fields.Char(string='Motivo de la consulta', tracking=True)
    causa_origen = fields.Text(string='¿Cuál cree usted que sea la causa u origen?', tracking=True)
    desde_prese_pro = fields.Text(string='¿Desde cuándo presenta este problema?', tracking=True)
    tra_este_ante = fields.Boolean(string="No", tracking=True)
    tra_este_ante_01 = fields.Boolean(string="Si", tracking=True)
    donde = fields.Char(string='dónde?', tracking=True)
    real_activi_fi = fields.Boolean(string="No", tracking=True)
    real_activi_fi_01 = fields.Boolean(string="Si", tracking=True)
    donde_01 = fields.Char(string='dónde?', tracking=True)
    ostio_articulares = fields.Boolean(string="Ostio articulares", tracking=True)
    diabetes = fields.Boolean(string="Diabetes", tracking=True)
    renales = fields.Boolean(string="Renales", tracking=True)
    ninguna_gra_croni = fields.Boolean(string="Ninguna grave o crónica", tracking=True)
    cardiacas = fields.Boolean(string="Cardiacas", tracking=True)
    epilepsia = fields.Boolean(string="Epilepsia", tracking=True)
    cancer = fields.Boolean(string="Cáncer", tracking=True)
    otras = fields.Boolean(string="Otras", tracking=True)
    alergias = fields.Boolean(string="Alergias", tracking=True)
    tiroides = fields.Boolean(string="Tiroides", tracking=True)
    proble_piel = fields.Boolean(string="Problemas en la piel", tracking=True)
    inter_quirur = fields.Boolean(string="No", tracking=True)
    inter_quirur_01 = fields.Boolean(string="Si", tracking=True)
    obser_qui = fields.Char(string='Obervacion', tracking=True)
    toma_hormonas = fields.Boolean(string="No", tracking=True)
    toma_hormonas_01 = fields.Boolean(string="Si", tracking=True)
    obser_hormona = fields.Char(string='Obervacion', tracking=True)
    normal = fields.Boolean(string="Normal", tracking=True)
    alta = fields.Boolean(string="Alta", tracking=True)
    baja = fields.Boolean(string="Baja", tracking=True)
    lenta = fields.Boolean(string="Lenta", tracking=True)
    normal_01 = fields.Boolean(string="Normal", tracking=True)
    rapida = fields.Boolean(string="Rápida", tracking=True)
    obser = fields.Text(string='Observaciones', tracking=True)
    state = fields.Selection([('new', 'Nuevo'), ('confirmado', 'Confirmado'),
                              ('cancelado', 'Cancelado')],
                             string="Estado", default='new', tracking=True)

    eval_diagnostico_1 = fields.Char(string='Evaluacion y Diagnóstico', tracking=True)
    eval_diagnostico_2 = fields.Char(string='Evaluacion y Diagnóstico', tracking=True)

    eval_observaciones_1_2 = fields.Char(string='Observaciones', tracking=True)

    eval_diagnostico_3 = fields.Char(string='Evaluacion y Diagnóstico', tracking=True)
    eval_diagnostico_4 = fields.Char(string='Evaluacion y Diagnóstico', tracking=True)

    eval_observaciones_3_4 = fields.Char(string='Observaciones', tracking=True)

    primera = fields.Char(string='1era', tracking=True)
    segunda = fields.Char(string='2da', tracking=True)
    tercera = fields.Char(string='3ra', tracking=True)

    monto_a_pagar = fields.Char(string='Monto a pagar:', tracking=True)
    promocion_descuento = fields.Char(string='Promoción y/o descuento', tracking=True)
    sesiones_adicionales = fields.Char(string='Sesiones adicionales', tracking=True)
    vencimiento_tratamiento = fields.Date(string='Vencimiento de tratamiento', tracking=True)
    forma_pago = fields.Char(string='Forma de pago', tracking=True)

    date_order = fields.Datetime(string='Fecha de Creación', index=True, copy=False, tracking=True,
                                 default=fields.Datetime.now)

    order_line = fields.One2many('control.medidas', 'order_id', string='Control de Medidas',tracking=True)
    order_line_01 = fields.One2many('control.terapista', 'order_id_01', string='Control Terapista',tracking=True)

    note = fields.Char(string='Observaciones y otros Tratamientos',tracking=True)
    note_01 = fields.Char(string='Observaciones',tracking=True)

class controlmedidas(models.Model):
    _name = "control.medidas"
    _description = "Control de Medidas"

    fecha = fields.Date(string='Fecha')
    pecto_busto = fields.Char(string='Pectoral o Busto')
    espalda = fields.Char(string='Espalda')
    abd_alto = fields.Char(string='ABD Alto')
    cintura = fields.Char(string='Cintura')
    abd_bajo = fields.Char(string='ABD Bajo')
    cad_alta = fields.Char(string='CAD. Alta')
    muslo = fields.Char(string='Muslo')
    brazo = fields.Char(string='Brazo')
    lineas = fields.Char(string='Lineas',default='-')
    order_id = fields.Many2one('reporte.corporal', string='Corporal')

class controlterapista(models.Model):
    _name = "control.terapista"
    _description = "Control Terapista"

    terapista = fields.Char(string='Terapista')
    fecha = fields.Date(string='Fecha')
    maquinas = fields.Char(string='Maquinas')
    zona_tratar = fields.Char(string='Zonas a Tratar')
    paciente = fields.Many2one('res.partner', string='Paciente')
    firma = fields.Char(string='Firma')

    order_id_01 = fields.Many2one('reporte.corporal', string='Corporal')

    note = fields.Char(string='Observaciones')

    @api.onchange('order_id_01.partner_id', 'paciente')
    def _paciente_nom(self):
        for rec in self:
            rec.paciente = rec.order_id_01.partner_id

class saleorder(models.Model):
    _inherit = 'sale.order'

    ficha_paciente_id = fields.Many2one('reporte.clinica.corporal', string='Ficha de Paciente')