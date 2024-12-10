# -*- coding: utf-8 -*-

from odoo import fields, models

class HrSalaryHistory(models.Model):
    _name = 'hr.salary.history'
    _description = 'Salary History'
    _order = 'updated_date desc'

    employee_id = fields.Char(string='ID de empleado', help="Empleado")
    employee_name = fields.Char(string='Nombre Empleado', help="Nombre")
    updated_date = fields.Datetime(string='Actualizado en', help="Fecha de actualización del salario")
    current_value = fields.Float(string='Salario actual', help="Salario actualizado")
