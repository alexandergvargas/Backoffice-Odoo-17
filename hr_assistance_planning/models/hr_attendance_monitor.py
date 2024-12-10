# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, Command
from odoo.exceptions import UserError

class hr_attendance_monitor(models.Model):
	_name = 'hr.attendance.monitor'
	_description = 'Hr Monitor de asistencia'
	_order = 'employee_id, fecha desc'
	_auto = False

	employee_id = fields.Many2one('hr.employee','Empleado')
	work_location_id = fields.Many2one('hr.work.location','Establecimiento') #service_location_id
	type_document_id = fields.Many2one('hr.type.document','T. D.')
	identification_id = fields.Char(u'Nro Ident')
	fecha = fields.Date('Fecha')
	day_name = fields.Char('Día')

	horario_asis = fields.Char('Horario Lab')
	hora_ing = fields.Float('Hora Ingreso')
	hora_sal = fields.Float('Hora Salida')
	mar_hora_ing = fields.Float('Marc Ingreso')
	mar_hora_sal = fields.Float('Marc Salida')
	duration_asis = fields.Float('Horas Lab')

	horario_ref = fields.Char('Horario Ref')
	ref_ing = fields.Float('Refrigerio Ingreso')
	ref_sal = fields.Float('Refrigerio Salida')
	mar_ref_ing = fields.Float('Marc Ref Ingreso')
	mar_ref_sal = fields.Float('Marc Ref Salida')
	duration_ref = fields.Float('Duracion Ref')
	mar_duration_ref = fields.Float('Durac Mar Ref')

	state = fields.Selection([
		('ok',u'Asistió'),
		('no_ok','Falta'),
		('vacaciones','Vacaciones'),
		('descanso','Día de descanso'),
		('justificada','Justificada'),
		('descansotrab','Descanso trabajado')
	],string="Estado")
	cant_dia = fields.Integer('Cant Dias')
	leave_id = fields.Many2one('hr.leave','Registro de ausencia')
	work_entry_type_id = fields.Many2one('hr.work.entry.type','Tipo de Entrada')
	feriado = fields.Boolean('Feriado')
	company_id = fields.Many2one('res.company',u'Compañía')

	def get_sql_attendance(self):
		sql ="""
	select row_number() OVER () AS id,
		T.employee_id,
		T.work_location_id,
		T.type_document_id,
		T.identification_id,
		T.fecha,
		T.day_name,
		for_hora_ing ||' - '|| for_hora_sal as horario_asis,
		T.hora_ing,
		T.hora_sal,
		T.mar_hora_ing,
		T.mar_hora_sal,
		CASE WHEN T.mar_hora_ing > 0 and T.mar_hora_sal > 0 THEN abs(T.mar_hora_sal - T.mar_hora_ing) ELSE 0 END as duration_asis,
		for_ref_ing ||' - '|| for_ref_sal as horario_ref,
		T.ref_ing,
		T.ref_sal,
		T.mar_ref_ing,
		T.mar_ref_sal,
		CASE WHEN T.ref_ing > 0 and T.ref_sal > 0 THEN abs(T.ref_sal - T.ref_ing) ELSE T.lunch_time END as duration_ref,
		CASE WHEN T.mar_ref_ing > 0 and T.mar_ref_sal > 0 THEN abs(T.mar_ref_sal - T.mar_ref_ing) ELSE T.lunch_time END as mar_duration_ref,
		CASE WHEN T.mar_hora_ing > 0 and T.mar_hora_sal > 0
			THEN
				CASE WHEN T.is_day_rest
					THEN
						'descansotrab'
					ELSE
						'ok'
					END
			ELSE
				CASE WHEN T.leave_id is not null
					THEN
						CASE WHEN T.code = '23'
							THEN
								'vacaciones'
							ELSE
								'justificada'
							END
					ELSE
						CASE WHEN T.is_day_rest
							THEN
								'descanso'
							ELSE
								'no_ok'
							END	
					END
			END as state,
		T.cant_dia,	
		T.leave_id,
		T.work_entry_type_id,
		T.feriado,
		T.company_id
		from (
			select
				hapl.employee_id,
				hapl.work_location_id,
				he.type_document_id as type_document_id,
				he.identification_id as identification_id,
				hapl.fecha,
				hapl.day_name,
				hapl.is_day_rest,
				hapl.lunch_time,
				extract(hour from (hapl.start_datetime::timestamp - '5 hr'::INTERVAL)) ||':'|| extract(minute from (hapl.start_datetime::timestamp - '5 hr'::INTERVAL)) as for_hora_ing,
				CASE WHEN Z.hora_sal is null THEN
					null
					ELSE extract(hour from (hapl.end_datetime::timestamp - '5 hr'::INTERVAL)) ||':'|| extract(minute from (hapl.end_datetime::timestamp - '5 hr'::INTERVAL)) end as for_ref_ing,
				Z.for_ref_sal,
				CASE WHEN Z.hora_sal is null THEN
					extract(hour from (hapl.end_datetime::timestamp - '5 hr'::INTERVAL)) ||':'|| extract(minute from (hapl.end_datetime::timestamp - '5 hr'::INTERVAL))
					else Z.for_hora_sal END as for_hora_sal,
				coalesce((((DATE_PART('hour', (hapl.start_datetime::timestamp - '5 hr'::INTERVAL)) * 60 +
							DATE_PART('minute', (hapl.start_datetime::timestamp - '5 hr'::INTERVAL))) * 60 +
						   DATE_PART('second', (hapl.start_datetime::timestamp - '5 hr'::INTERVAL)))/3600.0),0) as hora_ing,
				CASE WHEN Z.hora_sal is null THEN
					coalesce((((DATE_PART('hour', (hapl.end_datetime::timestamp - '5 hr'::INTERVAL)) * 60 +
							DATE_PART('minute', (hapl.end_datetime::timestamp - '5 hr'::INTERVAL))) * 60 +
						   DATE_PART('second', (hapl.end_datetime::timestamp - '5 hr'::INTERVAL)))/3600.0),0)
					ELSE Z.hora_sal END as hora_sal,
				coalesce((((DATE_PART('hour', (ha.check_in::timestamp - '5 hr'::INTERVAL)) * 60 +
							DATE_PART('minute', (ha.check_in::timestamp - '5 hr'::INTERVAL))) * 60 +
						   DATE_PART('second', (ha.check_in::timestamp - '5 hr'::INTERVAL)))/3600.0),0) as mar_hora_ing,
				CASE WHEN Z.mar_hora_sal is null THEN
					coalesce((((DATE_PART('hour', (ha.check_out::timestamp - '5 hr'::INTERVAL)) * 60 +
							DATE_PART('minute', (ha.check_out::timestamp - '5 hr'::INTERVAL))) * 60 +
						   DATE_PART('second', (ha.check_out::timestamp - '5 hr'::INTERVAL)))/3600.0),0)
					ELSE Z.mar_hora_sal END as mar_hora_sal,
				CASE WHEN Z.hora_sal is null THEN
					null
					ELSE coalesce((((DATE_PART('hour', (hapl.end_datetime::timestamp - '5 hr'::INTERVAL)) * 60 +
							DATE_PART('minute', (hapl.end_datetime::timestamp - '5 hr'::INTERVAL))) * 60 +
						   DATE_PART('second', (hapl.end_datetime::timestamp - '5 hr'::INTERVAL)))/3600.0),0)  END as ref_ing,
				Z.ref_sal,		   
				CASE WHEN Z.mar_hora_sal is null THEN
					null
					ELSE coalesce((((DATE_PART('hour', (ha.check_out::timestamp - '5 hr'::INTERVAL)) * 60 +
							DATE_PART('minute', (ha.check_out::timestamp - '5 hr'::INTERVAL))) * 60 +
						   DATE_PART('second', (ha.check_out::timestamp - '5 hr'::INTERVAL)))/3600.0),0) END as mar_ref_ing,
				Z.mar_ref_sal,
				abs(extract (day from (hapl.end_datetime::timestamp - '5 hr'::INTERVAL)) -
                extract (day from (hapl.start_datetime::timestamp - '5 hr'::INTERVAL))) as cant_dia,		   
				A.leave_id,
				A.work_entry_type_id,
				hst.code,
				case when hhd.date_from is not null then true else false end as feriado,
				hapl.company_id as company_id
			from hr_assistance_planning_line hapl
				inner join hr_employee he on he.id = hapl.employee_id
				left join hr_attendance ha on ha.calendar_line_id = hapl.id
				left join attendance_activity aa on aa.id = hapl.role_id
				left join (
					select
						hapl.employee_id,
						hapl.fecha,
						extract(hour from (hapl.start_datetime::timestamp - '5 hr'::INTERVAL)) ||':'|| extract(minute from (hapl.start_datetime::timestamp - '5 hr'::INTERVAL)) as for_ref_sal,
						extract(hour from (hapl.end_datetime::timestamp - '5 hr'::INTERVAL)) ||':'|| extract(minute from (hapl.end_datetime::timestamp - '5 hr'::INTERVAL)) as for_hora_sal,
						coalesce((((DATE_PART('hour', (hapl.start_datetime::timestamp - '5 hr'::INTERVAL)) * 60 +
									DATE_PART('minute', (hapl.start_datetime::timestamp - '5 hr'::INTERVAL))) * 60 +
								   DATE_PART('second', (hapl.start_datetime::timestamp - '5 hr'::INTERVAL)))/3600.0),0) as ref_sal,
						coalesce((((DATE_PART('hour', (hapl.end_datetime::timestamp - '5 hr'::INTERVAL)) * 60 +
									DATE_PART('minute', (hapl.end_datetime::timestamp - '5 hr'::INTERVAL))) * 60 +
								   DATE_PART('second', (hapl.end_datetime::timestamp - '5 hr'::INTERVAL)))/3600.0),0) as hora_sal,
						coalesce((((DATE_PART('hour', (ha.check_in::timestamp - '5 hr'::INTERVAL)) * 60 +
									DATE_PART('minute', (ha.check_in::timestamp - '5 hr'::INTERVAL))) * 60 +
								   DATE_PART('second', (ha.check_in::timestamp - '5 hr'::INTERVAL)))/3600.0),0) as mar_ref_sal,
						coalesce((((DATE_PART('hour', (ha.check_out::timestamp - '5 hr'::INTERVAL)) * 60 +
									DATE_PART('minute', (ha.check_out::timestamp - '5 hr'::INTERVAL))) * 60 +
								   DATE_PART('second', (ha.check_out::timestamp - '5 hr'::INTERVAL)))/3600.0),0) as mar_hora_sal,
						hapl.company_id as company_id
					from hr_assistance_planning_line hapl
						left join hr_attendance ha on ha.calendar_line_id = hapl.id
						left join attendance_activity aa on aa.id = hapl.role_id
					where hapl.state in ('published')
						 and aa.name not in ('Turno Mañana','Turno Noche')
						 order by hapl.employee_id, hapl.fecha
					)Z on hapl.employee_id = Z.employee_id and hapl.fecha = Z.fecha
				left join (
					select distinct hwe.work_entry_type_id,
						   hwe.employee_id,
						   hwe.leave_id,
						   to_char(hwe.date_start::TIMESTAMP - '5 hr'::INTERVAL , 'yyyy/mm/dd'::text) as date_start
					from hr_work_entry hwe
					where hwe.leave_id is not null
						  and hwe.state in ('draft','validated')
					)A on A.employee_id = hapl.employee_id and A.date_start = to_char(hapl.fecha, 'yyyy/mm/dd'::text)
				left join hr_leave hl on hl.id = A.leave_id
				left join hr_suspension_type hst on hst.id = hl.work_suspension_id
				left join resource_calendar_leaves hhd on hapl.fecha = hhd.date_from
			where hapl.state in ('published')
				 and aa.name in ('Turno Mañana','Turno Noche')
				 order by hapl.employee_id, hapl.fecha
        )T
		"""
		# print("sql",sql)
		return sql

	def init(self):
		sql = self.get_sql_attendance()
		# print(sql)
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''CREATE OR REPLACE VIEW %s AS (%s)''' % (self._table, sql))
		# self.env.cr.execute("""DROP TABLE IF EXISTS hr_attendance_monitor;""")
		# self.env.cr.execute("""CREATE TABLE hr_attendance_monitor as (""" + cadsql + """)""")
		# self.env.cr.execute("""DELETE FROM hr_attendance_monitor""")
		# self.env.cr.execute("""
		# 			INSERT INTO hr_attendance_monitor (calendar_line_id,attendance_id,service_location_id,
		# 			employee_id,type_document_id,identification_id,employee_replace_id,fecha,
		# 			check_in,check_out,state,have_leave,leave_id,feriado,semana,company_id)
		# 			("""+cadsql+""");
		# 			""")

	def set_justificante(self):
		contract=self.employee_id.contract_id.id
		return {
			'res_model': 'hr.leave',
			'type': 'ir.actions.act_window',
			'context': {'default_employee_id':self.employee_id.id,
						'default_contract_id':contract,
						'default_request_date_from':self.fecha,
						'default_request_date_to':self.fecha,
						},
			'view_mode': 'form',
			'view_type': 'form',
			'view_id': self.env.ref("hr_leave.view_hr_leave_all_susp_form").id,
			'target': 'new'
		}

	def show_leave(self):
		return {
			'res_model': 'hr.leave',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'view_type': 'form',
			'view_id': self.env.ref("hr_leave.view_hr_leave_all_susp_form").id,
			'res_id':self.leave_id.id,
			'target': 'new'
		}