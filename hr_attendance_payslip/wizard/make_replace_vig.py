# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import tools
from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, date, timedelta

class make_replace_vig(models.TransientModel):
	_name='make.replace.vig'
	_description='Reemplazar vigilante'

	
	attendance_id = fields.Many2one('hr.attendance','Asistencia')
	calendar_line_id=fields.Many2one('resource.calendar.line.it','Asistencia Planificada')
	service_location_id=fields.Many2one('partner.service.location','Establecimiento',related='calendar_line_id.service_location_id')
	employee_id = fields.Many2one('hr.employee','Vigilante',related='calendar_line_id.employee_id')
	horario=fields.Char('Horario',related='calendar_line_id.horario')
	fecha=fields.Date('Fecha',related='calendar_line_id.fecha')
	puesto=fields.Integer('Puesto',related='calendar_line_id.puesto')

	employee_replace_id = fields.Many2one('hr.employee','Vigilante de reemplazo')
	motive=fields.Selection([
		('vacaciones','Vacaciones'),
		('descanso','Día de descanso'),
		('no_ok','Falta'),
		],'Motivo',default='no_ok')

	def makerepla(self):
		self.calendar_line_id.employee_replace_id=self.employee_replace_id.id
		self.calendar_line_id.motive_replace=self.motive
		vals=self.calendar_line_id.calendar_id.prepare_line_values(self.calendar_line_id.puesto,0,self.employee_replace_id.id,self.fecha)
		linea=False
		if vals:
			vals.update({'line_origin':self.calendar_line_id.id})
			linea=self.env['resource.calendar.line.it'].create(vals)
		return linea
		


