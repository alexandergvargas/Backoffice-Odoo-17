# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta,time
from dateutil.relativedelta import relativedelta

class HrtareajeManager(models.Model):
    _name = "hr.tareaje.manager"
    _description = "Gestion de Asistencias"


    name = fields.Char(string='Nombre')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Hecho'),
    ], string='Estado', readonly=True, copy=False, default='draft')

    # category_id = fields.Many2one('hr.employee.category', string='Categoria')
    date_start = fields.Date(string='Desde', required=True,
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_end = fields.Date(string='Hasta', required=True,
                           default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))

    time_tolerancia = fields.Float('Tiempo Tolerancia', default=0.0)
    is_compute_he = fields.Boolean(string='Calcular Horas Extras', default=False)

    tareaje_line_ids = fields.One2many('hr.tareaje.manager.line','tareaje_id','Detalle Tareajes')
    company_id = fields.Many2one('res.company',string=u'Compañia', default=lambda self: self.env.company,readonly=True)

    def set_reopen(self):
        # self.tareaje_line_ids.attendance_line_ids.unlink()
        # self.tareaje_line_ids.unlink()
        self.state = 'draft'

    def set_close(self):
        self.state = 'done'

    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft_or_cancel(self):
        if any(self.filtered(lambda tareaje: tareaje.state not in ('draft'))):
            raise UserError(_('¡No puede eliminar Tareos que no esten en estado borrador!'))

    def _get_sql_tareo(self,employee_id):
        sql = """
select
    T.employee_id,
       T.work_location_id,
       T.code,
       T.fecha,
       T.day_name,
       T.state,
       T.horario_asis,
       T.mar_hora_ing,
       T.mar_hora_sal,
       T.mar_duration_ref,
       T.worked_hours,
       T.incos,
       CASE WHEN T.worked_hours = 0 then 0 else T.htd/T.worked_hours end as dlab,
       CASE WHEN T.worked_hours = 0 then 0 else T.htn/T.worked_hours end as dlabn,
       T.htd,
       T.htn,
       T.dom,
       T.fer,
       T.tar,
       T.dvac,
       T.dmed,
       T.dpat,
       T.lcgh,
       T.lsgh,
       T.smar,
       T.senf,
       T.fal,
       T.he25,
       T.he35,
       T.he100
FROM(        
    select
       T.employee_id,
       T.work_location_id,
       T.code,
       T.fecha,
       T.day_name,
       T.state,
       T.horario_asis,
       T.mar_hora_ing,
       T.mar_hora_sal,
       T.mar_duration_ref,
       T.worked_hours, 
       CASE WHEN T.state in ('no_ok') THEN 1 ELSE 0 END as incos,
 
       CASE WHEN T.state in ('ok','descansotrab')
            THEN CASE WHEN T.cant_dia > 0
                THEN CASE WHEN (T.hora_ing >= 6 and T.hora_ing < 22)
                                THEN CASE WHEN (T.hora_sal < 6) THEN 22 - T.hora_ing ELSE (22 - T.hora_ing) + (T.hora_sal - 6) END
                          ELSE CASE WHEN (T.hora_sal < 6) THEN 0 ELSE (T.hora_sal - 6) END END
                ELSE CASE WHEN (T.hora_ing > 0 and T.hora_ing < 6)
                                THEN CASE WHEN (T.hora_sal < 6) THEN 0 ELSE T.hora_sal - 6 END
                          WHEN (T.hora_ing >= 6 and T.hora_ing < 22)
                                THEN CASE WHEN (T.hora_sal < 22) THEN T.worked_hours ELSE 22 - T.hora_ing END
                          ELSE 0 END
                END
            ELSE 0 END AS htd,

       CASE WHEN T.state in ('ok','descansotrab')
            THEN CASE WHEN T.cant_dia > 0
                THEN CASE WHEN (T.hora_ing >= 6 and T.hora_ing < 22)
                                THEN CASE WHEN (T.hora_sal < 6) THEN 2 + (6 - T.hora_sal) ELSE 8 END
                          ELSE CASE WHEN (T.hora_sal < 6) THEN (2 - T.hora_ing) + (6 - T.hora_sal) ELSE (2 - T.hora_ing) + 6 END END
                ELSE CASE WHEN (T.hora_ing > 0 and T.hora_ing < 6)
                                THEN CASE WHEN (T.hora_sal < 6) THEN T.worked_hours ELSE 6 - T.hora_ing END
                          WHEN (T.hora_ing >= 6 and T.hora_ing < 22)
                                THEN CASE WHEN (T.hora_sal < 22) THEN 0 ELSE T.hora_sal - 22 END
                          ELSE CASE WHEN (T.hora_sal < 6) THEN (24 - T.hora_ing) + T.hora_sal ELSE (24 - T.hora_ing) + 6 END END
                END
            ELSE 0 END AS htn,

       CASE WHEN T.state in ('descanso') THEN 1 ELSE 0 END as dom,

       CASE WHEN T.state in ('descansotrab') THEN 1 ELSE 0 END as fer,

       CASE WHEN T.mar_hora_ing > (T.hora_ing + {tolerancia}) THEN abs(T.mar_hora_ing - T.hora_ing) + T.tar_ref ELSE T.tar_ref END as tar,

       CASE WHEN T.state in ('vacaciones') THEN 1 ELSE 0 END as dvac,
       CASE WHEN T.state in ('justificada') and T.code in ('DMED') THEN 1 ELSE 0 END as dmed,
       CASE WHEN T.state in ('justificada') and T.code in ('DPAT') THEN 1 ELSE 0 END as dpat,
       CASE WHEN T.state in ('justificada') and T.code in ('LCGH') THEN 1 ELSE 0 END as lcgh,
       CASE WHEN T.state in ('justificada') and T.code in ('LSGH') THEN 1 ELSE 0 END as lsgh,
       CASE WHEN T.state in ('justificada') and T.code in ('SMAR') THEN 1 ELSE 0 END as smar,
       CASE WHEN T.state in ('justificada') and T.code in ('SENF') THEN 1 ELSE 0 END as senf,
       CASE WHEN T.state in ('justificada') and T.code in ('FAL') THEN 1 ELSE 0 END as fal,

       CASE WHEN T.state in ('ok')
            THEN CASE WHEN T.hours_ext >= 0 and T.hours_ext < 2
                THEN T.hours_ext
                ELSE 2 END 
            ELSE 0 END AS he25,
            
       CASE WHEN T.state in ('ok')
            THEN CASE WHEN T.hours_ext > 2
                THEN T.hours_ext - 2
                ELSE 0 END 
            ELSE 0 END AS he35,

       CASE WHEN T.state in ('descansotrab')
            THEN CASE WHEN T.hours_ext > 0
                THEN T.hours_ext
                ELSE 0 END
            ELSE 0 END as he100

    from (
         select ham.employee_id,
                ham.work_location_id,
                ham.fecha,
                ham.day_name,
                ham.horario_asis,
                ham.hora_ing,
                ham.hora_sal,
                ham.mar_hora_ing,
                ham.mar_hora_sal,
                CASE WHEN ham.state = 'ok' THEN abs(ham.hora_sal - ham.hora_ing- ham.duration_ref) ELSE 0 END as worked_hours,
                CASE WHEN ham.state in ('ok','descansotrab') and (ham.mar_duration_ref > ham.duration_ref) THEN abs(ham.mar_duration_ref - ham.duration_ref) ELSE 0 END as tar_ref,
                CASE WHEN ham.state in ('ok','descansotrab') THEN ham.mar_duration_ref ELSE 0 END as mar_duration_ref,
                CASE WHEN ham.state in ('ok','descansotrab') and (ham.mar_hora_sal > ham.hora_sal) THEN abs(ham.mar_hora_sal - ham.hora_sal) ELSE 0 END as hours_ext,
                ham.cant_dia,
                ham.state,
                ham.leave_id,
                hwet.code,
                ham.feriado,
                ham.company_id
         from hr_attendance_monitor ham
                left join hr_work_entry_type hwet on hwet.id = ham.work_entry_type_id
         where ham.fecha  between '{date_from}' and '{date_to}'
           and ham.employee_id = {employee_id}
           and ham.company_id = {company_id}
     )T
)T     
		""".format(
            tolerancia = self.time_tolerancia,
            date_from=self.date_start.strftime('%Y/%m/%d'),
            date_to=self.date_end.strftime('%Y/%m/%d'),
            employee_id = employee_id,
            company_id = self.company_id.id
        )
        return sql

    def _get_sql_employee(self):
        sql = """          
    select T.employee_id,
        sum(T.incos) as incos,
        sum(CASE WHEN T.worked_hours = 0 then 0 else T.htd/T.worked_hours end) as dlab,
        sum(CASE WHEN T.worked_hours = 0 then 0 else T.htn/T.worked_hours end) as dlabn,
        sum(T.htd) as htd,
        sum(T.htn) as htn,
        sum(T.dom) as dom,
        sum(T.fer) as fer,
        sum(T.tar) as tar,
        sum(T.dvac) as dvac,
        sum(T.dmed) as dmed,
        sum(T.dpat) as dpat,
        sum(T.lcgh) as lcgh,
        sum(T.lsgh) as lsgh,
        sum(T.smar) as smar,
        sum(T.senf) as senf,
        sum(T.fal) as fal,
        sum(T.he25) as he25,
        sum(T.he35) as he35,
        sum(T.he100) as he100
    from (
    select
       T.employee_id,
       T.worked_hours,
       CASE WHEN T.state in ('no_ok') THEN 1 ELSE 0 END as incos,     

       CASE WHEN T.state in ('ok','descansotrab')
            THEN CASE WHEN T.cant_dia > 0
                THEN CASE WHEN (T.hora_ing >= 6 and T.hora_ing < 22)
                                THEN CASE WHEN (T.hora_sal < 6) THEN 22 - T.hora_ing ELSE (22 - T.hora_ing) + (T.hora_sal - 6) END
                          ELSE CASE WHEN (T.hora_sal < 6) THEN 0 ELSE (T.hora_sal - 6) END END
                ELSE CASE WHEN (T.hora_ing > 0 and T.hora_ing < 6)
                                THEN CASE WHEN (T.hora_sal < 6) THEN 0 ELSE T.hora_sal - 6 END
                          WHEN (T.hora_ing >= 6 and T.hora_ing < 22)
                                THEN CASE WHEN (T.hora_sal < 22) THEN T.worked_hours ELSE 22 - T.hora_ing END
                          ELSE 0 END
                END
            ELSE 0 END AS htd,

       CASE WHEN T.state in ('ok','descansotrab')
            THEN CASE WHEN T.cant_dia > 0
                THEN CASE WHEN (T.hora_ing >= 6 and T.hora_ing < 22)
                                THEN CASE WHEN (T.hora_sal < 6) THEN 2 + (6 - T.hora_sal) ELSE 8 END
                          ELSE CASE WHEN (T.hora_sal < 6) THEN (2 - T.hora_ing) + (6 - T.hora_sal) ELSE (2 - T.hora_ing) + 6 END END
                ELSE CASE WHEN (T.hora_ing > 0 and T.hora_ing < 6)
                                THEN CASE WHEN (T.hora_sal < 6) THEN T.worked_hours ELSE 6 - T.hora_ing END
                          WHEN (T.hora_ing >= 6 and T.hora_ing < 22)
                                THEN CASE WHEN (T.hora_sal < 22) THEN 0 ELSE T.hora_sal - 22 END
                          ELSE CASE WHEN (T.hora_sal < 6) THEN (24 - T.hora_ing) + T.hora_sal ELSE (24 - T.hora_ing) + 6 END END
                END
            ELSE 0 END AS htn,

       CASE WHEN T.state in ('descanso') THEN 1 ELSE 0 END as dom,

       CASE WHEN T.state in ('descansotrab') THEN 1 ELSE 0 END as fer,

       CASE WHEN T.mar_hora_ing > (T.hora_ing + {tolerancia}) THEN abs(T.mar_hora_ing - T.hora_ing) + T.tar_ref ELSE T.tar_ref END as tar,

       CASE WHEN T.state in ('vacaciones') THEN 1 ELSE 0 END as dvac,
       CASE WHEN T.state in ('justificada') and T.code in ('DMED') THEN 1 ELSE 0 END as dmed,
       CASE WHEN T.state in ('justificada') and T.code in ('DPAT') THEN 1 ELSE 0 END as dpat,
       CASE WHEN T.state in ('justificada') and T.code in ('LCGH') THEN 1 ELSE 0 END as lcgh,
       CASE WHEN T.state in ('justificada') and T.code in ('LSGH') THEN 1 ELSE 0 END as lsgh,
       CASE WHEN T.state in ('justificada') and T.code in ('SMAR') THEN 1 ELSE 0 END as smar,
       CASE WHEN T.state in ('justificada') and T.code in ('SENF') THEN 1 ELSE 0 END as senf,
       CASE WHEN T.state in ('justificada') and T.code in ('FAL') THEN 1 ELSE 0 END as fal,

       CASE WHEN T.state in ('ok')
            THEN CASE WHEN T.hours_ext >= 0 and T.hours_ext < 2
                THEN T.hours_ext
                ELSE 2 END 
            ELSE 0 END AS he25,
            
       CASE WHEN T.state in ('ok')
            THEN CASE WHEN T.hours_ext > 2
                THEN T.hours_ext - 2
                ELSE 0 END 
            ELSE 0 END AS he35,

       CASE WHEN T.state in ('descansotrab')
            THEN CASE WHEN T.hours_ext > 0
                THEN T.hours_ext
                ELSE 0 END
            ELSE 0 END as he100

    from (
         select ham.employee_id,
                ham.hora_ing,
                ham.hora_sal,
                ham.mar_hora_ing,
                ham.mar_hora_sal,
                CASE WHEN ham.state = 'ok' THEN abs(ham.hora_sal - ham.hora_ing- ham.duration_ref) ELSE 0 END as worked_hours,
                CASE WHEN ham.state in ('ok','descansotrab') and (ham.mar_duration_ref > ham.duration_ref) THEN abs(ham.mar_duration_ref - ham.duration_ref) ELSE 0 END as tar_ref,
                CASE WHEN ham.state in ('ok','descansotrab') and (ham.mar_hora_sal > ham.hora_sal) THEN abs(ham.mar_hora_sal - ham.hora_sal) ELSE 0 END as hours_ext,
                ham.cant_dia,
                ham.state,
                ham.leave_id,
                hwet.code,
                ham.feriado,
                ham.company_id
         from hr_attendance_monitor ham
                left join hr_work_entry_type hwet on hwet.id = ham.work_entry_type_id
         where ham.fecha  between '{date_from}' and '{date_to}'
           and ham.company_id = {company_id}
     )T
    )T
        group by T.employee_id
        		""".format(
            tolerancia = self.time_tolerancia,
            date_from = self.date_start.strftime('%Y/%m/%d'),
            date_to = self.date_end.strftime('%Y/%m/%d'),
            company_id = self.company_id.id
        )
        return sql

    def get_tareaje(self):
        self.tareaje_line_ids.attendance_line_ids.unlink()
        self.tareaje_line_ids.unlink()
        for record in self:
            # if not record.category_id.is_manager:
            self.env.cr.execute(self._get_sql_employee())
            res_employees = self.env.cr.dictfetchall()
            # print(res_employees)
            for employee in res_employees:
                self.env.cr.execute(self._get_sql_tareo(employee['employee_id']))
                res_asistencia = self.env.cr.dictfetchall()
                # print("res_asistencia",res_asistencia)
                employee_id = self.env['hr.employee'].search([('id', '=', employee['employee_id']),('company_id', '=', self.env.company.id)], limit=1)
                is_overtime = employee_id.contract_id.is_overtime
                # print("is_overtime",is_overtime)

                data={
                    'tareaje_id': record.id,
                    'employee_id': employee['employee_id'],
                    'incos': employee['incos'],
                    'dlab': employee['dlab'],
                    'dlabn': employee['dlabn'],
                    'htd': employee['htd'],
                    'htn': employee['htn'],
                    'dom': employee['dom'],
                    'fer': employee['fer'],
                    'fal': employee['fal'],
                    'tar': employee['tar'],
                    'dmed': employee['dmed'],
                    'dpat': employee['dpat'],
                    'lcgh': employee['lcgh'],
                    'lsgh': employee['lsgh'],
                    'dvac': employee['dvac'],
                    'smar': employee['smar'],
                    'senf': employee['senf'],
                    'he25': 0 if not record.is_compute_he else employee['he25'] if is_overtime else 0,
                    'he35': 0 if not record.is_compute_he else employee['he35'] if is_overtime else 0,
                    'he100': 0 if not record.is_compute_he else employee['he100'] if is_overtime else 0,
                    'attendance_line_ids': [(0, 0, {
                        'employee_id': line['employee_id'],
                        'work_location_id': line['work_location_id'],
                        'fecha': line['fecha'],
                        'day_name': line['day_name'],
                        'horario': line['horario_asis'],
                        'mar_hora_ing': line['mar_hora_ing'],
                        'mar_hora_sal': line['mar_hora_sal'],
                        'mar_duration_ref': line['mar_duration_ref'],
                        'worked_hours': line['worked_hours'],
                        'state': line['state'],
                        'incos': line['incos'],
                        'dlab': line['dlab'],
                        'dlabn': line['dlabn'],
                        'htd': line['htd'],
                        'htn': line['htn'],
                        'dom': line['dom'],
                        'fer': line['fer'],
                        'fal': line['fal'],
                        'tar': line['tar'],
                        'dmed': line['dmed'],
                        'dpat': line['dpat'],
                        'lcgh': line['lcgh'],
                        'lsgh': line['lsgh'],
                        'dvac': line['dvac'],
                        'smar': line['smar'],
                        'senf': line['senf'],
                        'he25': 0 if not record.is_compute_he else line['he25'] if is_overtime else 0,
                        'he35': 0 if not record.is_compute_he else line['he35'] if is_overtime else 0,
                        'he100': 0 if not record.is_compute_he else line['he100'] if is_overtime else 0,
                    }) for line in res_asistencia ]
                }
                # print('val',vals)
                self.env['hr.tareaje.manager.line'].create(data)
        return self.env['popup.it'].get_message('Se proceso exitosamente')


class HrtareajeManagerLine(models.Model):
    _name = "hr.tareaje.manager.line"
    _description = "Asistencia Tareaje"
    _rec_name = "employee_id"
    _order = "employee_id"

    employee_id = fields.Many2one('hr.employee', string="Empleado")
    incos = fields.Float(string='Inconsistencia')
    dlab = fields.Float(string='DLAB')
    dlabn = fields.Float(string='DLABN')
    htd = fields.Float(string='HTD')
    htn = fields.Float(string='HTN')
    dom = fields.Float(string='DOM')
    fer = fields.Float(string='FER')
    fal = fields.Float(string='FAL')
    tar = fields.Float(string='TAR')
    dmed = fields.Float(string='DMED')
    dpat = fields.Float(string='DPAT')
    lcgh = fields.Float(string='LCGH')
    lsgh = fields.Float(string='LSGH')
    dvac = fields.Float(string='DVAC')
    smar = fields.Float(string='SMAR')
    senf = fields.Float(string='SENF')
    he25 = fields.Float(string='HE25')
    he35 = fields.Float(string='HE35')
    he100 = fields.Float(string='HE100')

    tareaje_id = fields.Many2one('hr.tareaje.manager', ondelete='cascade')
    attendance_line_ids = fields.One2many('hr.tareaje.manager.line.attendance', 'tareaje_line_id', string='Detalle Asistencias')
    company_id = fields.Many2one('res.company',string=u'Compañia', default=lambda self: self.env.company,readonly=True)

    def view_detail(self):
        return {
            'name': 'Asistencia Tareaje',
            'domain': [('tareaje_line_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'res_model': 'hr.tareaje.manager.line.attendance',
            'view_mode': 'tree',
            'view_type': 'form',
            'views': [(False, 'tree')],
            'target': '_blank',
        }

class HrtareajeManagerLineAttendance(models.Model):
    _name = "hr.tareaje.manager.line.attendance"
    _description = "Detalle Asistencia Tareaje"
    _rec_name = "employee_id"
    _order = "fecha desc"

    employee_id = fields.Many2one('hr.employee', string="Empleado")
    work_location_id = fields.Many2one('hr.work.location','Establecimiento') #service_location_id
    # calendar_line_id = fields.Many2one('hr.assistance.planning.line','Linea de calendario')

    fecha = fields.Date('Fecha')
    # check_in = fields.Datetime(string="Check In")
    # check_out = fields.Datetime(string="Check Out")
    day_name = fields.Char('Día')
    horario = fields.Char('Horario')

    state = fields.Selection([
		('ok',u'Asistió'),
		('no_ok','Falta'),
		('vacaciones','Vacaciones'),
		('descanso','Día de descanso'),
		('justificada','Justificada'),
		('descansotrab','Descanso trabajado')
		],string="Estado")

    worked_hours = fields.Float(string='Horas Lab')
    mar_duration_ref = fields.Float(string='Horas Ref')
    mar_hora_ing = fields.Float('Marc Ingreso')
    mar_hora_sal = fields.Float('Marc Salida')
    incos = fields.Float(string='Incons')
    dlab = fields.Float(string='DLAB')
    dlabn = fields.Float(string='DLABN')
    htd = fields.Float(string='HTD')
    htn = fields.Float(string='HTN')
    dom = fields.Float(string='DOM')
    fer = fields.Float(string='FER')
    fal = fields.Float(string='FAL')
    tar = fields.Float(string='TAR')
    dmed = fields.Float(string='DMED')
    dpat = fields.Float(string='DPAT')
    lcgh = fields.Float(string='LCGH')
    lsgh = fields.Float(string='LSGH')
    dvac = fields.Float(string='DVAC')
    smar = fields.Float(string='SMAR')
    senf = fields.Float(string='SENF')
    he25 = fields.Float(string='HE25')
    he35 = fields.Float(string='HE35')
    he100 = fields.Float(string='HE100')

    hours_compensate = fields.Float(string='Horas a Comp')

    tareaje_line_id = fields.Many2one('hr.tareaje.manager.line', ondelete='cascade')

    company_id = fields.Many2one('res.company',string=u'Compañia', default=lambda self: self.env.company,readonly=True)