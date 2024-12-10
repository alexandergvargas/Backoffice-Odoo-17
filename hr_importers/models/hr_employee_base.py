# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_time

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    mobile_phone = fields.Char(compute="", inverse='')
    work_email = fields.Char(compute="", inverse='')
    # work_contact_id = fields.Many2one('res.partner', 'Work Contact', copy=False)
    # identification_id = fields.Char(store=True, inverse='_inverse_create_partner')

    def _create_work_contacts(self):
        if any(employee.work_contact_id for employee in self):
            raise UserError(_('Algún empleado ya tiene este contacto laboral.'))
        for employee in self:
            partner = self.env['res.partner'].search([('vat', '=', employee.identification_id)], limit=1)
            if not partner:
                partner = self.env['res.partner'].sudo().create({
                    'is_company': False,
                    'type': 'contact',
                    'name': employee.name,
                    'image_1920': employee.image_1920,
                    'street': employee.private_street,
                    'email': employee.work_email,
                    'phone': employee.work_phone,
                    'mobile': employee.mobile_phone,
                    'l10n_latam_identification_type_id': self.env['l10n_latam.identification.type'].search([('name', '=', employee.type_document_id.name)], limit=1).id,
                    'vat': employee.identification_id,
                    'ref': employee.identification_id,
                    'country_id': employee.country_id.id,
                    'function': employee.job_id.name,
                    'employee': True,
                    'is_employee': True, #campos personalizados
                    'name_p': employee.names,
                    'last_name': employee.last_name,
                    'm_last_name': employee.m_last_name,
                })
            if not employee.user_partner_id:
                employee.user_partner_id = partner.id
                employee.work_contact_id = partner.id
        # for employee, work_contact in zip(self, work_contacts):
        #     print("employee",employee)
        #     print("work_contact",work_contact)
        #     employee.work_contact_id = work_contact
        #     employee.user_partner_id = work_contact