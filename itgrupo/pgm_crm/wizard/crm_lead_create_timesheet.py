# -*- coding: utf-8 -*-
from odoo import fields, models


class CrmLeadCreateTimesheet(models.TransientModel):
    _name = 'crm.lead.create.timesheet'
    _description = "Crear parte de horas a partir de la oportunidad"

    _sql_constraints = [('time_positive', 'CHECK(time_spent > 0)', 'The timesheet\'s time must be positive')]

    time_spent = fields.Float(string='Horas utlizadas')
    description = fields.Char(string='Descripción')
    crm_id = fields.Many2one('crm.lead', "Oportunidad", required=True,default=lambda self: self.env.context.get('active_id', None),)

    def save_timesheet(self):
        values = {
            'crm_id': self.crm_id.id,
            'date': fields.Date.context_today(self),
            'name': self.description,
            'user_id': self.env.uid,
            'employee_id': self.env.user.employee_id.id if self.env.user.employee_id else False,
            'unit_amount': self.crm_id._get_rounded_hours(self.time_spent * 60),
        }
        self.crm_id.user_timer_id.unlink()
        line = self.env['account.analytic.line'].sudo().create(values)
        return line

    def action_delete_timesheet(self):
        self.crm_id.user_timer_id.unlink()
