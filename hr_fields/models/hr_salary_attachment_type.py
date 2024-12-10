# -*- coding:utf-8 -*-

from odoo import api, fields, models


class HrSalaryAttachment(models.Model):
    _inherit = 'hr.salary.attachment.type'

    name = fields.Char(required=True, translate=False)
    # active = fields.Boolean(string='Activo', default=True)

    # @api.model
    # def store_salary_attachment(self):
    #     for data_salary in self.env['hr.salary.attachment.type'].search([('code','in',['ATTACH_SALARY','ASSIG_SALARY','CHILD_SUPPORT'])]):
    #         data_salary.active = False
