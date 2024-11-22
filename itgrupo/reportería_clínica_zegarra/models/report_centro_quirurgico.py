from odoo import api, fields, models


class reportecentroquirurgico(models.Model):
    _name = "reporte.centro.quirurgico"
    _description = 'Centro Quirúrgcico'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Historia Clinica N°')

    @api.model
    def create(self, vals):
        obj = super(reportecentroquirurgico, self).create(vals)
        number = self.env['ir.sequence'].get('secuencia.centro.quirurgico') or '/'
        obj.write({'name': number})

        return obj

    # @api.onchange('paciente', 'edad')
    # def _cambio_edad(self):
    #     for rec in self:
    #         if rec.paciente:
    #             rec.edad = rec.paciente.edad

    medico_cirujano = fields.Many2one('res.partner', string='Médico Cirujano')
    paciente = fields.Many2one('res.partner', string='Paciente')
    edad = fields.Char(string='Edad')
    tipo_cirugia = fields.Char(string='Tipo de Cirugia')
    hora_inicio = fields.Char(string='Hora de Inicio')
    hora_termino = fields.Char(string='Hora de Termino')
    tiempo = fields.Char(string='Tiempo')
    anestesiologo = fields.Char(string='Anestesiologo')

    tipo_anestesia = fields.Char(string='Tipo de Anestesia')
    fecha_ingreso = fields.Date(string='Fecha de Ingreso')
    fecha_alta = fields.Date(string='Fecha de Alta')
    dias_hospita = fields.Char(string='Dias de Hospitalización')
    ayudante_cirujano = fields.Many2one('res.partner', string='Ayudante de Cirujano')
    instrumentista = fields.Char(string='Instrumentista')
    circulante = fields.Char(string='Circulante')
    observaciones = fields.Char(string='Observación')

    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id,
                                 required=True)

    equipamientos_ids = fields.One2many('uso.equipamiento', 'quirurgico_ids', string='Uso Equipamiento')


class usoequipamiento(models.Model):
    _name = "uso.equipamiento"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    quirurgico_ids = fields.Many2one('reporte.centro.quirurgico', string='Cirugias')
    centrifuga = fields.Char(string='Centrifuga')
    cialitica = fields.Char(string='Cialitica')
    co2 = fields.Char(string='CO2')
    electrocauterio = fields.Char(string='Electrocauterio')
    esterilizacion = fields.Char(string='Esterilización')
    maq_anestesia = fields.Char(string='Maq. De Anestesia')
    maq_aspiración = fields.Char(string='Maq. De Aspiración')
    maq_de_lipo_la = fields.Char(string='Maq. De Lipo Laser')
    moni_sig_vi = fields.Char(string='Monitor de Signos Vitales')
    lase_co2 = fields.Char(string='Laser CO2')
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id,
                                 required=True)
