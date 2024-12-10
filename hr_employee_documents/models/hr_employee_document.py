# -*- coding: utf-8 -*-

from datetime import date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrEmployeeDocument(models.Model):
    _name = 'hr.employee.document'
    _description = 'HR Employee Document'

    name = fields.Char(string='Codigo del Documento', required=True, copy=False, help='Puede dar su número de documento.')
    description = fields.Text(string='Descripción', copy=False, help="Descripción sobre el documento.")
    expiry_date = fields.Date(string='Fecha de Caducidad', copy=False, help="Fecha de caducidad de los documentos.")
    employee_ref_id = fields.Many2one(comodel_name='hr.employee', invisible=1, copy=False)
    doc_attachment_ids = fields.Many2many(comodel_name='ir.attachment',
                                          relation='doc_attach_rel_ids',
                                          column1='doc_id',
                                          column2='attach_id3',
                                          string="Adjunto",
                                          help='Puedes adjuntar la copia de tu documento', copy=False)
    issue_date = fields.Date(string='Fecha de Emision', default=fields.datetime.now(), help="Fecha de emisión de los documentos de los empleados.", copy=False)
    document_type_id = fields.Many2one(comodel_name='hr.document.type', string="Tipo de Documento", help="Tipo de documento del empleado")
    before_days = fields.Integer(string="Días", help="¿Cuántos días antes para recibir el correo electrónico de notificación?")
    notification_type = fields.Selection([
        ('single', 'Notificar en fecha de caducidad'),
        ('multi', 'Notificación antes de unos días'),
        ('everyday', 'Todos los días hasta la fecha de caducidad'),
        ('everyday_after', 'Notificación al vencimiento y después')
    ], string='Tipo de Notificación',
        help="Notificar en fecha de caducidad: recibirá una notificación solo en la fecha de caducidad.  "
             "Notificación antes de unos días: recibirá una notificación en 2 fechas, en la fecha de caducidad y el número de días antes de la fecha. "
             "Todos los días hasta la fecha de caducidad: recibirá una notificación desde la cantidad de días hasta la fecha de caducidad del documento. "
             "Notificación al vencimiento y después: recibirá una notificación en la fecha de caducidad y continuará hasta los días. "
             "Si no seleccionó ninguno, recibirá una notificación antes de los 7 días a la fecha de caducidad del documento.")

    @api.constrains('expiry_date')
    def check_expr_date(self):
        for each in self:
            if each.expiry_date:
                exp_date = fields.Date.from_string(each.expiry_date)
                if exp_date < date.today():
                    raise UserError(_('Su documento ha caducado.'))

    def mail_reminder(self):
        """Envío de notificación de caducidad de documentos a los empleados."""
        date_now = fields.Date.today()
        for record in self.search([]):
            if record.expiry_date:
                if record.notification_type == 'single':
                    if date_now == record.expiry_date:
                        mail_content = ("  Hola  " + record.employee_ref_id.name +
                                        ",<br>Su documento " + record.name +
                                        " se esta caducando hoy, por favor renuévelo")
                        main_content = {
                            'subject': _('Documento-%s caducó el %s') % (record.name, record.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': record.employee_ref_id.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
                elif record.notification_type == 'multi':
                    exp_date = fields.Date.from_string(record.expiry_date) - timedelta(days=record.before_days)
                    if date_now == exp_date or date_now == record.expiry_date:
                        mail_content = ("  Hola  " + record.employee_ref_id.name +
                                        ",<br>Su documento " + record.name +
                                        " va a caducar el " + str(record.expiry_date) +
                                        ". Por favor renovarlo antes de la fecha de caducidad.")
                        main_content = {
                            'subject': _('Documento-%s Caducara el %s') % (record.name, record.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': record.employee_ref_id.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
                elif record.notification_type == 'everyday':
                    exp_date = fields.Date.from_string(record.expiry_date) - timedelta(days=record.before_days)
                    if exp_date <= date_now <= record.expiry_date:
                        mail_content = ("  Hola  " + record.employee_ref_id.name
                                        + ",<br>Su documento " + record.name +
                                        " va a caducar el " + str(record.expiry_date) +
                                        ". Por favor renovarlo antes de la fecha de caducidad.")
                        main_content = {
                            'subject': _('Documento-%s Caducara el %s') % (record.name, record.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': record.employee_ref_id.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
                elif record.notification_type == 'everyday_after':
                    exp_date = fields.Date.from_string(record.expiry_date) + timedelta(days=record.before_days)
                    if record.expiry_date <= date_now <= exp_date:
                        mail_content = ("  Hola  " + record.employee_ref_id.name +
                                        ",<br>Su documento " + record.name +
                                        " se caduco el " + str(record.expiry_date) +
                                        ". Por favor renovarlo ")
                        main_content = {
                            'subject': _('Documento-%s Caducado el %s') % (record.name, record.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': record.employee_ref_id.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
                else:
                    exp_date = fields.Date.from_string(record.expiry_date) - timedelta(days=7)
                    if date_now == exp_date:
                        mail_content = ("  Hola  " + record.employee_ref_id.name +
                                        ",<br>Su documento " + record.name +
                                        " va a caducar el " + str(record.expiry_date) +
                                        ". Por favor renovarlo antes de la fecha de caducidad. ")
                        main_content = {
                            'subject': _('Documento-%s Caducado el %s') % (record.name, record.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': record.employee_ref_id.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
