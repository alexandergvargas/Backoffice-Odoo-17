# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.onchange('wage')
    def onchange_wage(self):
        """ Function for create salary history when wage changes"""
        if self.wage and self.wage > 0:
            vals = {
                'employee_id': self.employee_id.id,
                'employee_name': self.employee_id,
                'updated_date': fields.Datetime.now(),
                'current_value': self.wage,
            }
            self.env['hr.salary.history'].sudo().create(vals)

    def salary_history(self):
        """ Function to show salary history"""
        res_user = self.env['res.users'].browse(self._uid)
        if res_user.has_group('hr.group_hr_manager'):
            return {
                'name': _("Historial de Remuneraciones"),
                'view_mode': 'tree',
                'res_model': 'hr.salary.history',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': [('employee_id', '=', self.employee_id.id)]
            }
        elif self.employee_id.id == self.env.user.employee_id.id:
            return {
                'name': _("Historial de Remuneraciones"),
                'view_mode': 'tree',
                'res_model': 'hr.salary.history',
                'type': 'ir.actions.act_window',
                'target': 'new'
            }
        else:
            raise UserError('Usted no puede acceder al historial de salarios!!!!')
