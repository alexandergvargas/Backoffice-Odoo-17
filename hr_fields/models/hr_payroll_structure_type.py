# -*- coding:utf-8 -*-

from odoo import api, fields, models

class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'
    _description = 'Salary Structure Type'

    default_resource_calendar_id = fields.Many2one(default=None)
    active = fields.Boolean(string='Activo', default=True)
    wage_type = fields.Selection([
        ('monthly', 'Salario Fijo'),
        ('hourly', 'Salario por Dia')
    ], string="Tipo de Salario", default='monthly', required=True)

    @api.model
    def store_structure_type(self):
        for data_structure_type in self.env['hr.payroll.structure.type'].search([('name', 'in', ['Worker'])]):
            data_structure_type.active = False