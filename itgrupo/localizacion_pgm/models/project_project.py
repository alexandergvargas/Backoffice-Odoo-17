# -*- coding: utf-8 -*-
from odoo import fields, api, models, _



class ProjectProject(models.Model):
    _inherit = 'project.project'

    activity_count = fields.Integer(compute='_compute_activity_count')
    account_aprobados = fields.Integer(compute='_compute_activity_count_stados')
    porcentaje_avance_projecto = fields.Float(compute='_porcentaje_avance')

    @api.depends('activity_count', 'account_aprobados')
    def _porcentaje_avance(self):
        for rec in self:
            if rec.activity_count > 1:
                rec.porcentaje_avance_projecto = rec.account_aprobados * 100 / rec.activity_count
            else:
                rec.porcentaje_avance_projecto = 0

    def _compute_activity_count(self):
        for obj in self:
            count = 0
            if self._context:
                ctx = self._context.copy()
            else:
                ctx = {}
            ctx['active_test'] = False
            for activity in self.env['project.task'].with_context(ctx).search([('project_id', '=', obj.id)]):
                count += 1
            obj.activity_count = count

    def _compute_activity_count_stados(self):
        for obj in self:
            count = 0
            if self._context:
                ctx = self._context.copy()
            else:
                ctx = {}
            ctx['active_test'] = False
            for activity in self.env['project.task'].with_context(ctx).search([('project_id', '=', obj.id),
                                                                               ('state', '=', '1_done')]):
                count += 1
            obj.account_aprobados = count


    progress = fields.Integer(String="Progreso", compute='_compute_progress',store=True)

    @api.depends('activity_count')
    def _compute_progress(self):
        for rec in self:
            if rec.porcentaje_avance_projecto > 0:
                progress = rec.porcentaje_avance_projecto
            else:
                progress = rec.porcentaje_avance_projecto
            rec.progress = progress
