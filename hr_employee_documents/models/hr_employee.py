# -*- coding: utf-8 -*-

from odoo import fields, models, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    document_count = fields.Integer(compute='_compute_document_count', string='N° Documentos', help="Número de documentos del empleado")

    def _compute_document_count(self):
        """Calcula la cantidad de documentos de empleados."""
        for each in self:
            document_ids = self.env['hr.employee.document'].sudo().search([('employee_ref_id', '=', each.id)])
            each.document_count = len(document_ids)

    def action_document_view(self):
        """Vista detallada del documento del empleado."""
        self.ensure_one()
        domain = [('employee_ref_id', '=', self.id)]
        return {
            'name': _('Documentos'),
            'domain': domain,
            'res_model': 'hr.employee.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Haga clic para crear nuevos documentos
                        </p>'''),
            'limit': 80,
            'context': "{'default_employee_ref_id': %s}" % self.id
        }
