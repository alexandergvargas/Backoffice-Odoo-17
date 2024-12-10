# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
import calendar
from collections import namedtuple, defaultdict
from odoo.tools.translate import _

class hr_work_suspension(models.Model):
    _inherit='hr.work.suspension'

    leave_id = fields.Many2one('hr.leave','Ausencia')

class hr_accrual_vacation(models.Model):
    _inherit='hr.accrual.vacation'

    leave_id = fields.Many2one('hr.leave','Ausencia')

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    # contract_id = fields.Many2one('hr.contract','Contrato')
    # payslip_run_id = fields.Many2one('hr.payslip.run','Planilla')
    work_suspension_id = fields.Many2one('hr.suspension.type',related='holiday_status_id.suspension_type_id',string=u'Tipo de Suspensión', store=True)
    # payslip_status = fields.Boolean('Enviado a Planillas', copy=False, default= False)

    # envio de data a nomina central
    def prepare_suspension_data(self,employee_id,date_from,date_to,dias_periodo,periodo):
        vals = {
                'suspension_type_id': self.work_suspension_id.id,
                'reason': self.holiday_status_id.work_entry_type_id.name,
                'request_date_from': date_from,
                'request_date_to': date_to,
                'days': dias_periodo,
                'periodo_id': periodo,
                'leave_id': self.id,
                'contract_id': employee_id.contract_id.id,
                'employee_id': employee_id.id,
            }
        return vals

    def action_confirm(self):
        t = super(HrLeave, self).action_confirm()
        for l in self:
            # if l.payslip_status == False:
            #     if l.state=='validate':
            if l.work_suspension_id:
                dias_periodo = 0
                year_1 = l.request_date_from.year
                year_2 = l.request_date_to.year
                if year_1 == year_2:
                    nro_meses = (l.request_date_to.month-l.request_date_from.month) + 1
                else:
                    nro_meses = (13 - l.request_date_from.month) + l.request_date_to.month
                date = l.request_date_from
                # print("date",date)
                # print("nro_meses",nro_meses)
                for c, fee in enumerate(range(nro_meses), 1):
                    last_day = calendar.monthrange(date.year,date.month)[1]
                    # print("last_day",last_day)
                    if c == 1 and c != nro_meses:
                        # print("c pri",c)
                        date_from = l.request_date_from
                        date_to = l.request_date_from.replace(day=last_day)
                        dias_periodo = last_day - l.request_date_from.day + 1
                    elif c == nro_meses:
                        # print("c ult",c)
                        date = l.request_date_to
                        if c == 1:
                            date_from = l.request_date_from
                            date_to = l.request_date_to
                            dias_periodo = l.number_of_days
                        else:
                            date_from = l.request_date_to.replace(day=1)
                            date_to = l.request_date_to
                            dias_periodo = l.request_date_to.day
                    else:
                        # print("c",c)
                        date = date
                        date_from = date.replace(day=1)
                        date_to = date.replace(day=last_day)
                        dias_periodo = last_day
                    # print("date",date)
                    # print("dias_periodo",dias_periodo)
                    periodo=self.env['hr.period'].search([('date_start', '<=', date),('date_end', '>=',date)],limit=1).id
                    date = date + relativedelta(months=1)

                    vals = l.prepare_suspension_data(l.employee_id,date_from,date_to,dias_periodo,periodo)
                    # print("vals",vals)
                    if l.holiday_status_id.work_entry_type_id.code == 'DLAB' and l.work_suspension_id.code == '23':
                        continue
                    else:
                        self.env['hr.work.suspension'].create(vals)
        return t
        #     else:
        #         raise UserError(u'Esta ausencia %s de %s ya fue enviada a la planilla Mensual' % (l.name, l.employee_id.name))
        # return self.env['popup.it'].get_message(u'Se mandó al Lote de Nóminas exitosamente.')

    def action_refuse(self):
        super(HrLeave,self).action_refuse()
        for holiday in self:
            # if l.payslip_status == False:
            #     if l.state=='validate':
            contract = holiday.employee_id.contract_id.work_suspension_ids.filtered(lambda reg: reg.leave_id.id == self.id)
            vaca = self.env['hr.accrual.vacation'].search([('leave_id','=',self.id)])
            # print("l",l)
            # print("l",h)
            if len(contract)>0 or len(vaca)>0:
                # raise UserError(u'No se puede rechazar si ya se encuentra en reportado en planilla')
                contract.unlink()
                vaca.unlink()
            holiday.payslip_state = 'normal'
            holiday.employee_ids = holiday.employee_id


    @api.depends('holiday_type')
    def _compute_from_holiday_type(self):
        allocation_from_domain = self.env['hr.leave.allocation']
        if (self._context.get('active_model') == 'hr.leave.allocation' and self._context.get('active_id')):
            allocation_from_domain = allocation_from_domain.browse(self._context['active_id'])
        for holiday in self:
            if holiday.holiday_type == 'employee':
                if not holiday.employee_ids:
                    if allocation_from_domain:
                        holiday.employee_ids = allocation_from_domain.employee_id
                        holiday.holiday_status_id = allocation_from_domain.holiday_status_id
                    else:
                        # Esto maneja el caso en el que se realiza una solicitud solo con el id_empleado
                        # pero no es necesario volver a calcular los cambios en el id_empleado.
                        holiday.employee_ids = holiday.employee_id
                holiday.mode_company_id = False
                holiday.category_id = False
            elif holiday.holiday_type == 'company':
                holiday.employee_ids = False
                if not holiday.mode_company_id:
                    holiday.mode_company_id = self.env.company.id
                holiday.category_id = False
            elif holiday.holiday_type == 'department':
                holiday.employee_ids = False
                holiday.mode_company_id = False
                holiday.category_id = False
            elif holiday.holiday_type == 'category':
                holiday.employee_ids = False
                holiday.mode_company_id = False
            else:
                holiday.employee_ids = self.env.context.get('default_employee_id') or holiday.employee_id or self.env.user.employee_id

    @api.model_create_multi
    def create(self, vals_list):
        # t = super(HrLeave, self).create(vals_list)
        # print("vals_list",vals_list)
        holidays = super(HrLeave, self.with_context(mail_create_nosubscribe=True)).create(vals_list)
        for holiday in holidays:
            # print("holiday",holiday)
            if holiday.employee_id.contract_id.work_entry_source == 'manual':
                raise UserError(_('Este empleado esta configurado para que su entrada de trabajo sea manual.'))
            else:
                if holiday.validation_type == 'no_validation':
                    holiday.state = 'draft'
                    holidays.action_confirm()
        return holidays