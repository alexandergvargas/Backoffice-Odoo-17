# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import api, fields, models, tools, SUPERUSER_ID, Command
from datetime import timedelta, datetime

class HrAssistancePlanning(models.Model):
	_name='hr.assistance.planning'
	_description='Planificación de asistencia'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	name = fields.Char('Nombre Planificación')
	calendar_id = fields.Many2one('resource.calendar','Horario de Trabajo')
	type_workday = fields.Selection([
		('horario','Normal'),
		('atipico','Atipico'),
		],'Tipo de Jornada',default='horario')

	number_assists = fields.Selection([('one', '1 Turno/2 Marcaciones'),('two', '2 Turnos/4 Marcaciones')], default='one',string='Cant Marcaciones')
	activity1_id = fields.Many2one('attendance.activity', string='Tipo 1er Turno')
	activity2_id = fields.Many2one('attendance.activity', string='Tipo 2do Turno')

	days_work = fields.Integer(string='Cant Dias Trabajo')
	days_rest = fields.Integer(string='Cant Dias Descanso')

	date_ini = fields.Date('Fecha Inicio')
	date_end = fields.Date('Fecha Final', compute='compute_date_end', store=True)

	h_ini = fields.Float('Hora Ingreso')
	h_end = fields.Float('Hora Salida')
	duration = fields.Float('Duracion Asistencia', compute='compute_duration', store=True)

	ref_ini = fields.Float('Ref Ingreso')
	ref_end = fields.Float('Ref Salida')
	duration_ref = fields.Float('Duracion Refrigerio', compute='compute_duration_ref', store=True)

	workday_mo = fields.Boolean('Lunes')
	workday_tu = fields.Boolean('Martes')
	workday_we = fields.Boolean('Miércoles')
	workday_th = fields.Boolean('Jueves')
	workday_fr = fields.Boolean('Viernes')
	workday_sa = fields.Boolean(u'Sábado')
	workday_su = fields.Boolean('Domingo')

	line_ids = fields.One2many('hr.assistance.planning.line','assistance_planning_id','Detalle Planificacion',copy=False)
	line_employee_ids = fields.One2many('hr.assistance.planning.employee','assistance_employee_id','Detalle Empleados')
	state = fields.Selection([('draft','Borrador'),
							('prepare',u'En Proceso'),
							('done','Hecho')],'Estado',default='draft',copy=False)

	company_id = fields.Many2one('res.company',u'Compañía',required=True, default=lambda self: self.env.company,readonly=True)

	@api.onchange('calendar_id')
	def onchange_calendar_id(self):
		if self.calendar_id:
			sql = """
			select T.name,
				   T.dayofweek,
				   T.hour_from as h_ini,
				   case when T.hour_to_tarde is null then T.hour_to else T.hour_to_tarde end as h_end,
				   case when T.hour_from_tarde is null then null else T.hour_to end as ref_ini,
				   case when T.hour_from_tarde is null then null else T.hour_from_tarde end as ref_end,
				   T.day_period,
				   T.calendar_id,
				   T.lunch_time,
				   T.code
			from (
			select rca.name,
				   rca.dayofweek,
				   rca.hour_from,
				   rca.hour_to,
				   A.hour_from_tarde,
				   A.hour_to_tarde,
				   rca.day_period,
				   rca.calendar_id,
				   rca.lunch_time,
				   hwet.code
			from resource_calendar_attendance rca
				left join hr_work_entry_type hwet on hwet.id = rca.work_entry_type_id
				left join (
				select
				   rca.dayofweek,
				   rca.hour_from as hour_from_tarde,
				   rca.hour_to as hour_to_tarde
				from resource_calendar_attendance rca
				where rca.calendar_id = {calendar_id}
				and rca.day_period = 'afternoon'
			)A on A.dayofweek = rca.dayofweek
			where rca.calendar_id = {calendar_id}
			and rca.day_period = 'morning'
			and hwet.code = 'DOM'
			order by rca.sequence
			)T
				""".format(
			calendar_id=self.calendar_id.id
			)
			self._cr.execute(sql)
			data = self._cr.dictfetchall()
			# print("data",data)
			self.workday_mo = self.workday_tu = self.workday_we = self.workday_th = self.workday_fr = self.workday_sa = self.workday_su = False
			for rec in data:
				self.h_ini = rec['h_ini']
				self.h_end = rec['h_end']
				self.ref_ini = rec['ref_ini']
				self.ref_end = rec['ref_end']
				# self.duration_ref = rec['lunch_time']
				if rec['dayofweek']=='0':
					self.workday_mo = True
				elif rec['dayofweek']=='1':
					self.workday_tu = True
				elif rec['dayofweek']=='2':
					self.workday_we = True
				elif rec['dayofweek']=='3':
					self.workday_th = True
				elif rec['dayofweek']=='4':
					self.workday_fr = True
				elif rec['dayofweek']=='5':
					self.workday_sa = True
				elif rec['dayofweek']=='6':
					self.workday_su = True
			self.type_workday = 'horario'

	@api.depends('type_workday','date_ini')
	def compute_date_end(self):
		for rec in self:
			if rec.date_ini and rec.type_workday == 'atipico':
				rec.date_end = rec.date_ini + timedelta(days=rec.days_rest+rec.days_work-1)

	@api.depends('h_ini', 'h_end')
	def compute_duration(self):
		for rec in self:
			rec.duration = abs(rec.h_end - rec.h_ini)

	@api.depends('ref_ini', 'ref_end')
	def compute_duration_ref(self):
		for rec in self:
			rec.duration_ref = abs(rec.ref_end - rec.ref_ini)

	def return_unpublish(self):
		self.state = 'prepare'
		self.line_ids.action_unpublish()

	def action_publish(self):
		if len(self.line_ids)>0:
			self.state='done'
			self.line_ids.action_send()
		else:
			raise UserError(u'Primero debe darle clic al boton (Planificar Asistencia)')

	def reopen(self):
		ids=''
		if len(self.line_ids)>0:
			for l in self.line_ids:
				ids = ids + str(l.id)+','
			ids = ids[:-1]
			cadsql='select * from hr_attendance where calendar_line_id in ('+ids+')'
			self.env.cr.execute(cadsql)
			c = self.env.cr.dictfetchall()
			if len(c)>0:
				raise UserError(u'No se puede cancelar debido a que ya tiene asistencias asignadas a la planificación')
		self.line_ids.unlink()
		self.line_employee_ids.unlink()
		self.state='draft'

	# BOTON PARA TRAER EMPLEADOS
	def get_employees_planning(self):
		wizard = self.env['hr.employee.planning.wizard'].create({
			'assistance_planning_id': self.id,
			'company_id':self.company_id.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_hr_employee_planning_wizard' % module)
		return {
			'name': u'Seleccionar Empleados',
			'res_id': wizard.id,
			'view_mode': 'form',
			'res_model': 'hr.employee.planning.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	# BOTON PARA PLANIFICAR LAS ASISTENCIAS
	def prepare_line_values(self, dia, h_ini, h_end, activity_id, employee_id=False, datefix=False):
		vals={}
		fecha = datefix
		if datefix == False:
			fecha = self.date_ini + timedelta(days=dia)

		is_day_rest = False
		if self.type_workday == 'horario':
			if fecha.weekday() == 0 and self.workday_mo:
				is_day_rest = True
			if fecha.weekday() == 1 and self.workday_tu:
				is_day_rest = True
			if fecha.weekday() == 2 and self.workday_we:
				is_day_rest = True
			if fecha.weekday() == 3 and self.workday_th:
				is_day_rest = True
			if fecha.weekday() == 4 and self.workday_fr:
				is_day_rest = True
			if fecha.weekday() == 5 and self.workday_sa:
				is_day_rest = True
			if fecha.weekday() == 6 and self.workday_su:
				is_day_rest = True
		else:
			date_ini_rest = self.date_ini + timedelta(days=self.days_work)
			if fecha >= date_ini_rest:
				is_day_rest = True

		horas_ini = int(h_ini)
		minutos_ini = (h_ini * 60) % 60
		h_ini = "%02d:%02d:00" % (horas_ini, minutos_ini)
		horas_end = int(h_end)
		minutos_end = (h_end * 60) % 60
		h_end = "%02d:%02d:00" % (horas_end, minutos_end)

		hora_ini_line = fecha.strftime('%Y-%m-%d') + ' ' + h_ini
		hora_end_line = fecha.strftime('%Y-%m-%d') + ' ' + h_end
		hora_ini_line = datetime.strptime(hora_ini_line, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5)
		hora_end_line = datetime.strptime(hora_end_line, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5)
		# print("hora_ini_line",hora_ini_line)
		# print("hora_end_line",hora_end_line)

		vals.update({'assistance_planning_id': self.id})
		vals.update({'resource_id': employee_id.resource_id.id})
		vals.update({'work_location_id': employee_id.work_location_id.id})
		vals.update({'employee_id': employee_id.id})
		vals.update({'start_datetime': hora_ini_line})
		vals.update({'end_datetime': hora_end_line})
		vals.update({'role_id': activity_id.id})
		vals.update({'is_day_rest': is_day_rest})
		vals.update({'lunch_time': is_day_rest})
		vals.update({'was_copied': True})
		# print("vals funcion",vals)
		return vals

	def rangos_se_superponen(self,rango1_inicio, rango1_fin, rango2_inicio, rango2_fin):
		if rango1_inicio <= rango1_fin and rango2_inicio <= rango2_fin:
			return rango1_inicio <= rango2_fin and rango1_fin >= rango2_inicio
		elif rango1_inicio > rango1_fin and rango2_inicio <= rango2_fin:
			return (rango1_inicio <= rango2_fin and rango1_fin <= rango2_fin) or \
				   (rango1_inicio >= rango2_inicio and rango1_fin >= rango2_inicio)
		elif rango1_inicio <= rango1_fin and rango2_inicio > rango2_fin:
			return (rango2_inicio <= rango1_fin and rango2_fin <= rango1_fin) or \
				   (rango2_inicio >= rango1_inicio and rango2_fin >= rango1_inicio)
		else:
			return rango1_inicio >= rango2_inicio and rango1_fin <= rango2_fin

	def make_detail(self):
		usados=[]
		for l in self.line_employee_ids:
			if l.employee_id.id == False:
				raise UserError('No se puede generar, falta seleccionar un empleado')

			if l.employee_id.id in usados:
				raise UserError('No se puede repetir al empleado %s'% l.employee_id.name)
			else:
				usados.append(l.employee_id.id)

		self.line_ids.unlink()

		for l in self.line_employee_ids:
			dias = self.date_end-self.date_ini
			for j in range(0, dias.days+1):
				nextdate = self.date_ini+timedelta(days=j)
				existe = self.env['hr.assistance.planning.line'].search([('fecha','=',nextdate),('employee_id','=',l.employee_id.id),('state','=','published')])
				# print("existe",existe)
				for l2 in existe:
					hora_ini_line = timedelta(hours=self.h_ini)
					hora_end_line = timedelta(hours=self.h_end)
					if self.rangos_se_superponen(self.h_ini, self.h_end, hora_ini_line, hora_end_line):
						raise UserError('El empleado: %s ya se encuentra registrado para la fecha %s en otra planificacion llamada %s'
										%(l.employee_id.name,str(l2.fecha.strftime('%d/%m/%Y')),l2.assistance_planning_id.name))
				if self.number_assists == 'one':
					vals = self.prepare_line_values(j, self.h_ini, self.h_end, self.activity1_id, l.employee_id)
					if vals:
						self.env['hr.assistance.planning.line'].create(vals)
				else:
					vals1 = self.prepare_line_values(j, self.h_ini, self.ref_ini, self.activity1_id, l.employee_id)
					if vals1:
						self.env['hr.assistance.planning.line'].create(vals1)

					vals2 = self.prepare_line_values(j, self.ref_end, self.h_end, self.activity2_id, l.employee_id)
					if vals2:
						self.env['hr.assistance.planning.line'].create(vals2)
				# print("vals",vals)

			line_employee = self.env['hr.assistance.planning.employee'].search([('assistance_employee_id','=',self.id),('employee_id','=',l.employee_id.id)], limit=1)
			if line_employee:
				line_employee.count_lines = True if len(self.line_ids)>0 else False
			self.state='prepare'
		return self.env['popup.it'].get_message('Se planifico la asistencia exitosamente')


class HrAssistancePlanningEmployee(models.Model):
	_name='hr.assistance.planning.employee'
	_description='registro de asistencia empleados'

	assistance_employee_id = fields.Many2one('hr.assistance.planning','Planificacion',ondelete='cascade')
	count_lines = fields.Boolean("Contador", default=False)
	employee_id = fields.Many2one('hr.employee','Empleado')
	calendar_id = fields.Many2one('resource.calendar','Horario de Trabajo')
	work_location_id = fields.Many2one('hr.work.location','Establecimiento')
	company_id=fields.Many2one('res.company',u'Compañía',required=True, default=lambda self: self.env.company,readonly=True)

	def view_detail(self):
		self.env.cr.execute("""
							SELECT distinct hapl.id as id FROM hr_assistance_planning_line hapl
							 WHERE hapl.assistance_planning_id = %d
							   and hapl.employee_id = %d
							   and hapl.company_id=%d
                            """ % (self.assistance_employee_id.id,
								self.employee_id.id,self.env.company.id))
		res = self.env.cr.dictfetchall()
		elem = []
		for key in res:
			elem.append(key['id'])

		return {
			'name': 'Detalle',
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'hr.assistance.planning.line',
			# 'view_mode': 'tree',
			# 'view_type': 'tree',
			# 'view_id': self.env.ref('hr_assistance_planning.view_hr_assistance_planning_line_tree').id,
			'views': [(False, 'list'), (False, 'gantt'), (False, 'pivot')],
			'target': '_blank',
		}