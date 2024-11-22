# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class CrmLead(models.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead', 'timer.mixin']

    timesheet_ids = fields.One2many('account.analytic.line', 'crm_id', 'Timesheets')
    allow_timesheets = fields.Boolean(
        "Allow timesheets",
        compute='_compute_allow_timesheets',
        compute_sudo=True, readonly=True,
        help="Timesheets can be logged on this task.")
    #use_helpdesk_timesheet = fields.Boolean('Timesheet activated on Team', related='team_id.use_helpdesk_timesheet', readonly=True)
    display_timesheet_timer = fields.Boolean("Display Timesheet Time", compute='_compute_display_timesheet_timer')
    total_hours_spent = fields.Float("Hours Spent", compute='_compute_total_hours_spent', default=0, compute_sudo=True, store=True)
    display_timer_start_secondary = fields.Boolean(compute='_compute_display_timer_buttons')
    # display_timer = fields.Boolean(compute='_compute_display_timer')
    encode_uom_in_days = fields.Boolean(compute='_compute_encode_uom_in_days')
    analytic_account_id = fields.Many2one('account.analytic.account',store=True, readonly=False,
                                          string='Analytic Account', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")


    def _compute_encode_uom_in_days(self):
        self.encode_uom_in_days = self.env.company.timesheet_encode_uom_id == self.env.ref('uom.product_uom_day')

    #@api.depends('project_id.allow_timesheets')
    def _compute_allow_timesheets(self):
        for task in self:
            #task.allow_timesheets = task.project_id.allow_timesheets
            task.allow_timesheets = True

    @api.depends('display_timesheet_timer', 'timer_start', 'timer_pause', 'total_hours_spent')
    def _compute_display_timer_buttons(self):
        for record in self:
            if not record.display_timesheet_timer:
                record.update({
                    'display_timer_start_primary': False,
                    'display_timer_start_secondary': False,
                    'display_timer_stop': False,
                    'display_timer_pause': False,
                    'display_timer_resume': False,
                })
            else:
                super(CrmLead, record)._compute_display_timer_buttons()
                record.display_timer_start_secondary = record.display_timer_start_primary
                if not record.timer_start:
                    record.update({
                        'display_timer_stop': False,
                        'display_timer_pause': False,
                        'display_timer_resume': False,
                    })
                    if not record.total_hours_spent:
                        record.display_timer_start_secondary = False
                    else:
                        record.display_timer_start_primary = False

    # def _compute_display_timer(self):
    #     if self.env.user.has_group('helpdesk.group_helpdesk_user') and self.env.user.has_group('hr_timesheet.group_hr_timesheet_user'):
    #         self.display_timer = True
    #     else:
    #         self.display_timer = False

    @api.depends('allow_timesheets')
    def _compute_display_timesheet_timer(self):
        for record in self:
            record.display_timesheet_timer = record.allow_timesheets

    @api.depends('timesheet_ids.unit_amount')
    def _compute_total_hours_spent(self):
        if not any(self._ids):
            for record in self:
                record.total_hours_spent = round(sum(record.timesheet_ids.mapped('unit_amount')), 2)
            return
        crm_read_group = self.env['account.analytic.line']._read_group(
            [('crm_id', 'in', self.ids)],
            ['crm_id'],
            ['unit_amount:sum'],
        )
        crm_per_ticket = {crm_ticket.id: unit_amount_sum for crm_ticket, unit_amount_sum in crm_read_group}
        for ticket in self:
            ticket.total_hours_spent = round(crm_per_ticket.get(ticket.id, 0.0), 2)

    def action_timer_start(self):
        if not self.user_timer_id.timer_start and self.display_timesheet_timer:
            super(CrmLead, self).action_timer_start()

    def action_timer_stop(self):
        # timer was either running or paused
        if self.user_timer_id.timer_start and self.display_timesheet_timer:
            rounded_hours = self._get_rounded_hours(self.user_timer_id._get_minutes_spent())
            return self._action_open_new_timesheet(rounded_hours)
        return False

    def _action_open_new_timesheet(self, time_spent):
        return {
            "name": _("Confirmar tiempo utilizado"),
            "type": 'ir.actions.act_window',
            "res_model": 'crm.lead.create.timesheet',
            "views": [[False, "form"]],
            "target": 'new',
            "context": {
                **self.env.context,
                'active_id': self.id,
                'active_model': self._name,
                'default_time_spent': time_spent,
                'dialog_size': 'medium',
            },
        }

    def _get_rounded_hours(self, minutes):
        minimum_duration = int(self.env['ir.config_parameter'].sudo().get_param('timesheet_grid.timesheet_min_duration', 0))
        rounding = int(self.env['ir.config_parameter'].sudo().get_param('timesheet_grid.timesheet_rounding', 0))
        rounded_minutes = self._timer_rounding(minutes, minimum_duration, rounding)
        return rounded_minutes / 60
