# -*- coding: utf-8 -*-

from odoo import api, fields, models

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    suspension_type_id = fields.Many2one('hr.suspension.type',u'Tipo de Suspensión')
    # ausencia_wd_id = fields.Many2one('hr.work.entry.type', string='WD Ausencia')

    @api.model
    def store_leave_type(self):
        for leave in self.env['hr.leave.type'].search([('name', 'in',['Paid Time Off', 'Sick Time Off', 'Compensatory Days', 'Unpaid',
                                                             'Extra Time Off'])]):
            leave.active = False