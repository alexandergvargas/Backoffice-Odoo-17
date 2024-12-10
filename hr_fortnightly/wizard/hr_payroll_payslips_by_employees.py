# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import format_date

class HrPayslipEmployeesFortnightly(models.TransientModel):
    _name = 'hr.payslip.employees.fortnightly'
    _description = 'Generate payslips Fortnightly'

    def _get_available_contracts_domain(self):
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            payslip_run = self.env['hr.fortnightly'].create({
                'name': from_date.strftime('%B %Y'),
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.fortnightly'].browse(self.env.context.get('active_id'))
        type_id = self.env['hr.payroll.structure.type'].search([('name', '=', 'MENSUAL'),('active', '=',True)],limit=1).id
        return [('contract_ids.state', 'in', ('open', 'close')), ('company_id', '=', self.env.company.id),('contract_ids.structure_type_id', '=', type_id),
				('contract_ids.date_start', '<=', payslip_run.date_end),'|', ('contract_ids.date_end', '=', False),
				('contract_ids.date_end', '>=', payslip_run.date_start)]

    def _get_employees(self):
        active_employee_ids = self.env.context.get('active_employee_ids', False)
        if active_employee_ids:
            return self.env['hr.employee'].browse(active_employee_ids)
        # YTI check dates too
        return self.env['hr.employee'].search(self._get_available_contracts_domain())

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_fortnightly_rel', 'payslip_id', 'employee_id', 'Empleados',
                                    default=lambda self: self._get_employees(), required=True,
                                    compute='_compute_employee_ids', store=True, readonly=False)
    structure_id = fields.Many2one('hr.payroll.structure', string='Estructura Salarial',domain=lambda self:[('company_id', '=', self.env.company.id)],
                                   default=lambda self: self.get_structure_id())
    # type_id = fields.Many2one('hr.payroll.structure.type', required=True)
    department_id = fields.Many2one('hr.department')

    def get_structure_id(self):
        # return self.env['hr.payroll.structure'].search([('schedule_pay', '=', 'monthly'),('active', '=',True),('company_id', '=', self.env.company.id)],limit=1).id
        return self.env['hr.payroll.structure'].search([('name', '=', 'ADE_QUINCENAL'),('active', '=',True),('company_id', '=', self.env.company.id)],limit=1).id

    @api.depends('department_id')
    def _compute_employee_ids(self):
        for wizard in self:
            domain = wizard._get_available_contracts_domain()
            if wizard.department_id:
                domain = expression.AND([
                    domain,
                    [('department_id', 'child_of', self.department_id.id)]
                ])
            wizard.employee_ids = self.env['hr.employee'].search(domain)

    def _filter_contracts(self, contracts):
        # Podría anularse para evitar tener 2 nóminas de 'bono de fin de año', etc.
        return contracts

    def compute_sheet_multi(self):
        self.ensure_one()
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            today = fields.date.today()
            first_day = today + relativedelta(day=1)
            last_day = today + relativedelta(day=31)
            if from_date == first_day and end_date == last_day:
                batch_name = from_date.strftime('%B %Y')
            else:
                batch_name = _('Desde %s Hasta %s', format_date(self.env, from_date), format_date(self.env, end_date))
            payslip_run = self.env['hr.fortnightly'].create({
                'name': batch_name,
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.fortnightly'].browse(self.env.context.get('active_id'))

        employees = self.with_context(active_test=False).employee_ids
        if not employees:
            raise UserError(_("Debe seleccionar empleado(s) para generar una nomina."))

        #Evite que payslip_run tenga varios recibos de pago para el mismo empleado
        employees -= payslip_run.slip_ids.employee_id
        # print("employees",employees)
        success_result = {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.fortnightly',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }
        if not employees:
            return success_result

        payslips = self.env['hr.payslip']
        Payslip = self.env['hr.payslip']

        contracts = employees._get_contracts(payslip_run.date_start, payslip_run.date_end, states=['open', 'close']).filtered(lambda c: c.active)
        # print("contracts",contracts)
        contracts.generate_work_entries(payslip_run.date_start, payslip_run.date_end)
        work_entries = self.env['hr.work.entry'].search([
            ('date_start', '<=', payslip_run.date_end + relativedelta(days=1)),
            ('date_stop', '>=', payslip_run.date_start + relativedelta(days=-1)),
            ('employee_id', 'in', employees.ids),
        ])

        for slip in payslip_run.slip_ids:
            slip_tz = pytz.timezone(slip.contract_id.resource_calendar_id.tz)
            utc = pytz.timezone('UTC')
            date_from = slip_tz.localize(datetime.combine(slip.date_from, time.min)).astimezone(utc).replace(tzinfo=None)
            date_to = slip_tz.localize(datetime.combine(slip.date_to, time.max)).astimezone(utc).replace(tzinfo=None)
            payslip_work_entries = work_entries.filtered_domain([
                ('contract_id', '=', slip.contract_id.id),
                ('date_stop', '<=', date_to),
                ('date_start', '>=', date_from),
            ])
            payslip_work_entries._check_undefined_slots(slip.date_from, slip.date_to)

        if(self.structure_id.type_id.default_struct_id == self.structure_id):
            work_entries = work_entries.filtered(lambda work_entry: work_entry.state != 'validated')
            if work_entries._check_if_error():
                work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])

                for work_entry in work_entries.filtered(lambda w: w.state == 'conflict'):
                    work_entries_by_contract[work_entry.contract_id] |= work_entry

                for contract, work_entries in work_entries_by_contract.items():
                    conflicts = work_entries._to_intervals()
                    time_intervals_str = "\n - ".join(['', *["%s -> %s (%s)" % (s[0], s[1], s[2].employee_id.name) for s in conflicts._items]])
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Algunas entradas de trabajo no se pudieron validar.'),
                        'message': _('Intervalos de tiempo a buscar:%s', time_intervals_str),
                        'sticky': False,
                    }
                }

        MainParameter = self.env['hr.main.parameter'].get_main_parameter()

        default_values = Payslip.default_get(Payslip.fields_get())
        payslips_vals = []

        for contract in self._filter_contracts(contracts):
            values = dict(default_values, **{
                # 'name': _('Recibo Nomina'),
                'name': 'Quincena - %s - %s' % (contract.employee_id.name or '',payslip_run.name or ''),
                'employee_id': contract.employee_id.id,
                'identification_id': contract.employee_id.identification_id,
                'fortnightly_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                # 'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
                'struct_id': self.structure_id.id or contract.structure_id.id,
                # 'struct_type_id': self.type_id.id,
                'wage': contract.wage,
                'labor_regime': contract.labor_regime,
                'social_insurance_id': contract.social_insurance_id.id,
                'distribution_id': contract.distribution_id.id,
                'membership_id': contract.membership_id.id,
                'commision_type': contract.commision_type,
                'fixed_commision': contract.membership_id.fixed_commision,
                'mixed_commision': contract.membership_id.mixed_commision,
                'prima_insurance': contract.membership_id.prima_insurance,
                'retirement_fund': contract.membership_id.retirement_fund,
                'insurable_remuneration': contract.membership_id.insurable_remuneration,
                # 'is_afp': contract.membership_id.is_afp,
                'rmv': MainParameter.rmv,
				'company_id': self.env.company.id
            })
            payslips_vals.append(values)
        payslips = Payslip.with_context(tracking_disable=True).create(payslips_vals)
        payslips.generate_inputs_and_wd_lines()
        payslips._compute_name()
        payslips.compute_sheet()
        payslip_run.state = 'verify'

        return success_result