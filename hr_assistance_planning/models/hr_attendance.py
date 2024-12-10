# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta,time

class hr_attendance(models.Model):
	_inherit='hr.attendance'

	# in_latitude = fields.Float('Ingreso Latitud')
	# in_longitude = fields.Float('Ingreso Longitud')
	# out_latitude = fields.Float('Salida Latitud')
	# out_longitude = fields.Float('Salida Longitud')
	# map_in = fields.Char('GoogleMap Ing.', compute="get_map_in")
	# map_out = fields.Char('GoogleMap Sal.', compute="get_map_out")

	work_location_id = fields.Many2one('hr.work.location','Establecimiento') #service_location_id
	calendar_line_id = fields.Many2one('hr.assistance.planning.line','Linea de calendario')
	department_id = fields.Many2one('hr.department','Departamento',related='employee_id.department_id',store=True)

	activity_id = fields.Many2one('attendance.activity', string='Tipos de Asistencia',
                                  help='Este campo permite definir los tipos de turnos (por ejemplo, turno mañana, turno tarde, etc.)')
	# in_activity_id = fields.Many2one('attendance.activity', string='Tipos de Asistencia Entrada',
    #                               help='Este campo permite definir los tipos de turnos (por ejemplo, turno mañana, turno tarde, etc.)')
	# out_activity_id = fields.Many2one('attendance.activity', string='Tipos de Asistencia Salida',
    #                               help='Este campo permite definir los tipos de turnos (por ejemplo, turno mañana, turno tarde, etc.)')

	# def get_map_in(self):
	# 	for i in self:
	# 		i.map_in = "https://maps.google.com/?q="+str(i.in_latitude)+ "," + str(i.in_longitude)
	#
	# def get_map_out(self):
	# 	for i in self:
	# 		i.map_out = "https://maps.google.com/?q="+str(i.out_latitude)+ "," + str(i.out_longitude)

	def elemento_mas_cercano(self, lista, objetivo):
		# Comprobar si la lista está vacía
		if not lista:
			return None

		# Convertir el objetivo a tipo datetime si es necesario
		if not isinstance(objetivo, datetime):
			objetivo = datetime.strptime(objetivo, "%H:%M:%S")

		# Inicializar el elemento más cercano y la diferencia mínima
		elemento_mas_cercano = lista[0]
		diferencia_minima = abs(lista[0][0] - objetivo)
		idc=lista[0][1]
		# Recorrer la lista y encontrar el elemento más cercano
		for elemento in lista:
			diferencia_actual = abs(elemento[0] - objetivo)
			if diferencia_actual < diferencia_minima:
				diferencia_minima = diferencia_actual
				elemento_mas_cercano = elemento
				idc=elemento[1]

		return elemento_mas_cercano

	@api.model
	def create(self,vals):
		fecha = fields.Datetime.now() - timedelta(hours=5)
		# print(fecha)

		# print("vals", vals)
		if vals['in_mode'] in ('kiosk','systray'):
			c = self.env['hr.assistance.planning.line'].search([('employee_id','=',vals['employee_id']),('state','=','published'),('fecha','=',fecha.date())])
			# print("vals if", vals)
		else:
			c = self.env['hr.assistance.planning.line'].search([('employee_id','=',vals['employee_id']),('role_id','=',vals['activity_id']),('state','=','published'),('fecha','=',fecha.date())],limit=1)
			# print("vals elif", vals)
		if len(c)>0:
			line_calendar=c[0]
		tlista=[]

		if len(c)>0:
			for l in c:
				ahora = l.horario.split('-')

				if ':' in ahora[0]:
					h = ahora[0].split(':')[0].strip()
					m = ahora[0].split(':')[1].strip()
					fmins = float(m)/60
					hini = float(h)+fmins
				else:
					hini = float(l.horario.split('-')[0].strip())
				if ':' in ahora[1]:
					h = ahora[0].split(':')[0].strip()
					m = ahora[0].split(':')[1].strip()
					fmins = float(m)/60
					hend = float(h)+fmins
				else:
					hend = float(l.horario.split('-')[0].strip())

				h = hini
				td = timedelta(hours=h)
				dc = datetime.strptime(str(td), "%H:%M:%S")
				tlista.append((dc,l.id))
			dc1 = str(fecha.time())
			dc1 = datetime.strptime(dc1, "%H:%M:%S")
			d = self.elemento_mas_cercano(tlista,dc1)
			# print("d",d)
			if len(d)>0:
				line_calendar=self.env['hr.assistance.planning.line'].browse(d[1])
				if line_calendar:

					vals.update(
						{
							'work_location_id':line_calendar.work_location_id.id,
							'calendar_line_id':line_calendar.id,
							'activity_id':line_calendar.role_id.id,
						}
					)
			# print("vals",vals)
		return super(hr_attendance,self).create(vals)