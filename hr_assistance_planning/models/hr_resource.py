# -*- coding:utf-8 -*-
from random import randint
from datetime import datetime, time, timedelta
from odoo import api, fields, models

class ResourceResource(models.Model):
    _inherit = 'resource.resource'

    def _default_color(self):
        return randint(1, 11)

    color = fields.Integer(default=_default_color)
    avatar_128 = fields.Image(compute='_compute_avatar_128')
    # role_ids
    role_types_shift_ids = fields.Many2many('attendance.activity', 'resource_resource_attendance_activity_rel',
                                'resource_resource_id', 'types_shift_id', 'Turnos',
                                compute='_compute_role_ids', store=True, readonly=False)
    # default_role_id
    default_types_shift_id = fields.Many2one('attendance.activity', string="Tipo de Turno",
        compute='_compute_default_role_id', groups='hr.group_hr_user', store=True, readonly=False,
        help="Turno que se seleccionará de forma predeterminada al crear un horario para este empleado.\n"
             "Este turno también tendrá prioridad sobre los demás turnos del empleado a la hora de planificar Horarios.")

    @api.depends('employee_id')
    def _compute_avatar_128(self):
        is_hr_user = self.env.user.has_group('hr.group_hr_user')
        if not is_hr_user:
            public_employees = self.env['hr.employee.public'].with_context(active_test=False).search([('resource_id', 'in', self.ids),])
            avatar_per_employee_id = {emp.id: emp.avatar_128 for emp in public_employees}

        for resource in self:
            employee = resource.with_context(active_test=False).employee_id
            if is_hr_user:
                resource.avatar_128 = employee and employee[0].avatar_128
            else:
                resource.avatar_128 = avatar_per_employee_id[employee[0].id]

    @api.depends('role_types_shift_ids')
    def _compute_default_role_id(self):
        self.env.remove_to_compute(self._fields['role_types_shift_ids'], self)
        for resource in self:
            if resource.default_types_shift_id not in resource.role_types_shift_ids:
                resource.default_types_shift_id = resource.role_types_shift_ids[:1]

    @api.depends('default_types_shift_id')
    def _compute_role_ids(self):
        self.env.remove_to_compute(self._fields['default_types_shift_id'], self)
        resources_wo_default_role_ids = []
        for resource in self:
            if resource.default_types_shift_id:
                resource.role_types_shift_ids |= resource.default_types_shift_id
            else:
                resources_wo_default_role_ids.append(resource.id)
        self.browse(resources_wo_default_role_ids)._compute_default_role_id()

    def get_formview_id(self, access_uid=None):
        if self.env.context.get('from_planning'):
            return self.env.ref('resource.resource_resource_form', raise_if_not_found=False).id
        return super().get_formview_id(access_uid)

    @api.model_create_multi
    def create(self, vals_list):
        resources = super().create(vals_list)
        if self.env.context.get('from_planning'):
            create_vals = []
            for resource in resources.filtered(lambda r: r.resource_type == 'user'):
                create_vals.append({
                    'name': resource.name,
                    'resource_id': resource.id,
                })
            self.env['hr.employee'].sudo().with_context(from_planning=False).create(create_vals)
        return resources

    @api.depends('employee_id')
    @api.depends_context('show_job_title')
    def _compute_display_name(self):
        if not self.env.context.get('show_job_title'):
            return super()._compute_display_name()
        for resource in self:
            resource.display_name = resource.employee_id.display_name if resource.employee_id else resource.name

    def action_archive(self):
        res = super().action_archive()
        departure_date = datetime.combine(fields.Date.context_today(self) + timedelta(days=1), time.min)
        planning_slots = self.env['hr.assistance.planning.line'].sudo().search([
            ('resource_id', 'in', self.ids),
            ('resource_type', '=', 'material'),
            ('end_datetime', '>=', departure_date),
        ])
        planning_slots._manage_archived_resources(departure_date)
        return res