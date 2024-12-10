# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
from odoo.exceptions import UserError

class HrSubsidiesLot(models.Model):
	_name = 'hr.subsidies.lot'
	_description = 'Hr Subsidies Lot'
	_rec_name = 'periodo_id'

	# name = fields.Char()
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True)
	# payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo', required=True)
	periodo_id = fields.Many2one('hr.period', string='Periodo')
	line_ids = fields.One2many('hr.subsidies', 'subsidies_lot_id', string='Calculo de Subsidios')
	state = fields.Selection([('draft', 'Borrador'), ('done', 'Hecho')], default='draft', string='Estado')

	subsidies_count = fields.Integer(compute='_compute_subsidies_count', string='Cantidad')

	def _compute_subsidies_count(self):
		for subsidie in self:
			subsidie.subsidies_count = len(subsidie.line_ids)

	def action_open_subsidies(self):
		self.ensure_one()
		return {
			"type": "ir.actions.act_window",
			"res_model": "hr.subsidies",
			"views": [[False, "tree"], [False, "form"]],
			"domain": [['id', 'in', self.line_ids.ids]],
			"name": "Subsidios",
		}

	def turn_done(self):
		self.state = 'done'
		return self.env['popup.it'].get_message('Se cerro exitosamente')

	def turn_draft(self):
		self.state = 'draft'

	def get_subsidies(self):
		self.env['hr.subsidies'].search([('subsidies_lot_id','=',self.id),('preserve_record','=',False)]).unlink()

		suspension_type_ids = self.env['hr.suspension.type'].search([('code', 'in', ('22','21'))]).ids

		# print("suspension_type_id",suspension_type_ids)

		leave_subsidies = self.env['hr.leave'].search([('request_date_from', '>=', self.periodo_id.date_start),
														   ('request_date_from', '<=',self.periodo_id.date_end),
														   ('work_suspension_id', 'in', suspension_type_ids)])

		# print("leave_subsidies",leave_subsidies)
		for Employee in leave_subsidies:
			if Employee.employee_id.contract_id.situation_id.code == '0':
				continue
			else:
				vals = {
					'subsidies_lot_id': self.id,
					'type': 'maternity' if Employee.work_suspension_id.code == '22' else 'illness',
					'leave_id': Employee.id,
					'employee_id': Employee.employee_id.id,
					'date_start': Employee.request_date_from,
					'date_end': Employee.request_date_to,
					# 'preserve_record': True,
				}
				self.env['hr.subsidies'].create(vals)

		preservados = self.env['hr.subsidies'].search([('subsidies_lot_id', '=', self.id), ('preserve_record', '=', True)])
		empleados_pre = []
		# print("preservados",preservados)
		for j in preservados:
			if j.employee_id.id not in empleados_pre:
				empleados_pre.append(j.employee_id.id)
		eliminar = []
		for l in self.line_ids:
			if l.employee_id.id in empleados_pre:
				if l.preserve_record == False:
					eliminar.append(l)
		for l in eliminar:
			l.unlink()
		return self.env['popup.it'].get_message('Se calculo exitosamente')


class HrSubsidies(models.Model):
	_name = 'hr.subsidies'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Hr Subsidies'
	_rec_name = 'employee_id'

	# name = fields.Char()
	subsidies_lot_id = fields.Many2one('hr.subsidies.lot', ondelete='cascade')
	type = fields.Selection([('maternity', 'Subsidio por Maternidad'),
							 ('illness', 'Subsidio por Enfermedad')], string='Tipo de Subsidio', required=True, default='maternity')
	# leave_type_id = fields.Many2one('hr.leave.type', string="Tipo de Subsidio", required=True)
	leave_id = fields.Many2one('hr.leave', 'Ausencia', Tracking=True)

	employee_id = fields.Many2one('hr.employee', string='Empleado', Tracking=True)
	date_start = fields.Date(string='Fecha de Inicio', Tracking=True)
	date_end = fields.Date(string='Fecha Final', Tracking=True)
	subsidies_line_ids = fields.One2many('hr.subsidies.line', 'subsidies_id')
	subsidies_total_ids = fields.One2many('hr.subsidies.total', 'subsidies_id')
	subsidies_periodo_ids = fields.One2many('hr.subsidies.periodo', 'subsidies_id')
	state = fields.Selection([
		('draft', 'Borrador'),
		('close', 'Hecho'),
	], string='Estado', index=True, readonly=True, copy=False, default='draft')

	is_compute_20_days = fields.Boolean(string='Computar 20 dias', default=False)

	preserve_record = fields.Boolean('No Recalcular')
	company_id = fields.Many2one('res.company', string='Compañia',readonly=True, default=lambda self: self.env.company.id)

	def set_draft(self):
		self.subsidies_line_ids.unlink()
		self.subsidies_total_ids.unlink()
		self.subsidies_periodo_ids.unlink()
		self.state = 'draft'

	@api.ondelete(at_uninstall=False)
	def _unlink_if_draft_or_cancel(self):
		if any(self.filtered(lambda subsidies: subsidies.state not in ('draft'))):
			raise UserError(_('¡No puede eliminar este subsidio ya que no esta en estado borrador!'))
		
	# @api.onchange('employee_id', 'type')
	# def _onchange_update_date_start_end(self):
	# 	for hsi in self:
	# 		if hsi.employee_id:
	# 			if hsi.type == 'maternity':
	# 				hr = fields.Datetime.now()
	# 				company = self.env.company.id
	# 				query = f"""
	# 					SELECT hl.id
	# 						FROM hr_leave hl
	# 							LEFT JOIN hr_suspension_type hst on hst.id = hl.work_suspension_id
	# 								WHERE hl.employee_id = {hsi.employee_id.id}
	# 										AND hst.code = '22'
	# 										AND hl.company_id = {company} order by request_date_from desc limit 1
	#
	# 				"""
	# 				self._cr.execute(query)
	# 				results = self._cr.fetchall()
	# 				if not results or results[0][0] is None:
	# 					hsi.leave_id = False
	# 				else:
	# 					val = "\n".join([f"{row[0]}" for row in results])
	# 					hsi.leave_id = int(val)
	# 			else:
	# 				hr = fields.Datetime.now()
	# 				company = self.env.company.id
	# 				query = f"""
	# 					SELECT hl.id
	# 						FROM hr_leave hl
	# 							LEFT JOIN hr_suspension_type hst on hst.id = hl.work_suspension_id
	# 								WHERE hl.employee_id = {hsi.employee_id.id}
	# 										AND hst.code = '21'
	# 										AND hl.company_id = {company} order by request_date_from desc limit 1
	#
	# 				"""
	# 				self._cr.execute(query)
	# 				results = self._cr.fetchall()
	# 				if not results or results[0][0] is None:
	# 					hsi.leave_id = False
	# 				else:
	# 					val = "\n".join([f"{row[0]}" for row in results])
	# 					hsi.leave_id = int(val)
	# 		else:
	# 			hsi.leave_id = False

	# @api.onchange('leave_id')
	# def _onchange_leave_id_it(self):
	# 	for hsi in self:
	# 		if hsi.leave_id:
	# 			hsi.date_start = hsi.leave_id.request_date_from
	# 			hsi.date_end = hsi.leave_id.request_date_to
	# 		else:
	# 			hsi.date_start = False
	# 			hsi.date_end = False

	def _get_sql_salary(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_maternidad_values()
		sql_comi = "case when T.salary_rule_id in (%s) then sum(T.total) else 0 end  as comi, " % (','.join(str(i) for i in MainParameter.commission_sr_ids.ids))
		sql_otros = "case when T.salary_rule_id in (%s) then sum(T.total) else 0 end  as o_ing, " % (','.join(str(i) for i in MainParameter.otros_sr_ids.ids))
		sql_lacks = "case when T.salary_rule_id in (%s) then sum(T.total) else 0 end  as fal " % (','.join(str(i) for i in MainParameter.lack_sr_ids.ids))
		struct_id=self.env['hr.payroll.structure'].search([('schedule_pay', '=', 'monthly'),('active', '=',True),('company_id', '=', self.env.company.id)],limit=1).id
		sql = """
			select      
			T.employee_id,
			T.periodo,
			T.code,
			sum(T.bas) AS bas,
			sum(T.vac) AS vac,
			sum(T.af) AS af,
			sum(T.comi) AS comi,
			sum(T.hext) AS hext,
			sum(T.o_ing) AS o_ing,
			sum(T.fal) AS fal,
			sum(T.bas)+sum(T.vac)+sum(T.af)+sum(T.comi)+sum(T.hext)+sum(T.o_ing)-sum(T.fal) AS total
			FROM 
				(
				select      
				T.employee_id,
				T.periodo,
				T.code,
				T.salary_rule_id,
				case when T.salary_rule_id in ({basic_sr_id}) then sum(T.total) else 0 end  as bas,
				case when T.salary_rule_id in ({vacation_sr_id}) then sum(T.total) else 0 end  as vac,
				case when T.salary_rule_id in ({household_allowance_sr_id}) then sum(T.total) else 0 end  as af,
				{sql_comi}
				case when T.salary_rule_id in ({extra_hours_sr_id}) then sum(T.total) else 0 end  as hext,
				{sql_otros}
				{sql_lacks}
				from (	SELECT	
						he.id as employee_id,
						he.name,
						hper.id as periodo,
						hper.code,
						hp.date_from,
						hp.date_to,
						hsr.id as salary_rule_id,
						sum(hpl.total) as total
						from hr_payslip hp 
						inner join hr_payslip_line hpl on hpl.slip_id = hp.id
						inner join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
						inner join hr_employee he on he.id = hp.employee_id
						inner join hr_payslip_run hpr on hpr.id = hp.payslip_run_id
						inner join hr_period hper on hper.id = hpr.periodo_id
						where hsr.active = true
						and hpl.total <> 0
						and hsr.company_id = {company}
						and hsr.struct_id = {struct_id}
						and he.id = {employee_id}
						and (hp.date_from between '{date_from}' and '{date_to}')
						group by he.id,he.name,hper.id,hper.code,hp.date_from,hp.date_to,hsr.id,hsr.sequence
						order by hp.date_from, hsr.sequence
				)T
				group by T.employee_id, T.periodo,T.code, T.salary_rule_id
			)T
			group by T.employee_id, T.periodo, T.code
			order by T.code
			""".format(
				basic_sr_id = MainParameter.basic_sr_id.id,
				vacation_sr_id = MainParameter.vacation_sr_id.id,
				household_allowance_sr_id = MainParameter.household_allowance_sr_id.id,
				sql_comi = sql_comi,
				extra_hours_sr_id = MainParameter.extra_hours_sr_id.id,
				sql_otros = sql_otros,
				sql_lacks = sql_lacks,
				company = self.company_id.id,
				struct_id = struct_id,
				employee_id = self.employee_id.id,
				date_from = "%s/%s/01" % ((self.date_start - relativedelta(months=12)).year, (self.date_start - relativedelta(months=12)).month),
				date_to = (self.date_start - relativedelta(months=1)).strftime('%Y/%m/%d')
		)
		return sql

	def _get_sql_wd_dmed(self):
		struct_id=self.env['hr.payroll.structure'].search([('schedule_pay', '=', 'monthly'),('active', '=',True),('company_id', '=', self.env.company.id)],limit=1).id
		sql = """
		SELECT
		he.id as employee_id,
		he.name,
		hper.id as periodo,
		hwet.code as code,
		hwet.id as wd_type_id,
		hpwd.number_of_days as wd_total_dias
		from hr_payslip hp 
		inner join hr_employee he on he.id = hp.employee_id 
		inner join hr_payslip_run hpr on hpr.id = hp.payslip_run_id
		inner join hr_period hper on hper.id = hpr.periodo_id
		left join hr_payslip_worked_days hpwd on hpwd.payslip_id=hp.id
		left join hr_work_entry_type hwet on hwet.id=hpwd.work_entry_type_id
		where hp.company_id = {company}
		and hp.struct_id = {struct_id}
		and(hpwd.number_of_days <> 0 or hpwd.number_of_hours <> 0)
		and he.id = {employee_id}
		and hwet.code = 'DMED'
		and hp.date_from >= '{date_from}'
		""" .format(
			company = self.company_id.id,
			struct_id = struct_id,
			employee_id = self.employee_id.id,
			date_from = "%s/01/01" % ((self.date_start).year)
		)
		return sql
	
	def get_information(self):
		# print("%s/%s/01" % ((self.date_start - relativedelta(months=12)).year, (self.date_start - relativedelta(months=12)).month))
		# print("date_from",(self.date_start - relativedelta(months=12)).strftime('%Y/%m/%d'))
		if self.type == 'illness':
			log = ''
			self.env.cr.execute(self._get_sql_wd_dmed())
			res_wds_dm = self.env.cr.dictfetchall()
			dias_cont= (self.date_end-self.date_start).days + 1
			sum_dmed = dias_cont
			# print("sum_dmed",sum_dmed)
			for line in res_wds_dm:
				sum_dmed+= line['wd_total_dias']
				log += '%d dias de %s en la Planilla %s \n' % (int(line['wd_total_dias']),line['code'],line['periodo'])

			if not self.is_compute_20_days:
				if sum_dmed <= 20:
					log += '%d dias de contingencia\n' %(int(dias_cont))
					if log:
						return self.env['popup.it'].get_message('Este trabajador aun no supero los primeros 20 dias para el calculo del subsidio:\n\n' + log + '\n Total dias = %d' %(int(sum_dmed)))

		self.env.cr.execute(self._get_sql_salary())
		record = self.env.cr.dictfetchall()
		# print("record",record)

		for res in record:
			data = {
				'subsidies_id': self.id,
				'periodo_id': res['periodo'],
				'wage': res['bas'],
				'vacation': res['vac'],
				'household_allowance': res['af'],
				'commission': res['comi'],
				'extra_hours': res['hext'],
				'others_income': res['o_ing'],
				'lacks': res['fal'],
				'total': res['total'],
			}
			# print("data",data)
			self.env['hr.subsidies.line'].create(data)
		self.state = 'close'
		return {
			'effect': {
				'fadeout': 'slow',
				'message': "Generacion exitosa",
				'type': 'rainbow_man',
			}
		}

	def get_calculation(self):

		for x in self.subsidies_periodo_ids:
			if x.validation == 'paid out':
				raise UserError(_('¡No puede Recalcular por que ya ha sido importado desde la planilla mensual, \nprimero debe cambiar al estado no pagado los subsidios por periodos'))

		self.subsidies_total_ids.unlink()
		self.subsidies_periodo_ids.unlink()

		amount = 0
		for line in self.subsidies_line_ids:
			amount += line.total

		dias_total_sub = 30*len(self.subsidies_line_ids) if len(self.subsidies_line_ids) != 0 else 1
		dias_total = (self.date_end-self.date_start).days + 1
		if self.type == 'maternity':
			dias_sub = dias_total
			date_start = self.date_start
		else:
			dias_cont= (self.date_end-self.date_start).days
			if not self.is_compute_20_days:
				self.env.cr.execute(self._get_sql_wd_dmed())
				res_wds_dm = self.env.cr.dictfetchall()
				for line in res_wds_dm:
					dias_cont+= line['wd_total_dias']
				dias_sub = dias_cont -19
				dias_total = dias_cont+1
			else:
				dias_sub = dias_cont + 1
				dias_total = dias_cont + 21
				# print("dias_sub",dias_sub)
			date_start = self.date_end - relativedelta(days=dias_sub-1)
		# print("longitud",len(self.subsidies_line_ids))
		data_total = {
			'subsidies_id': self.id,
			'total_rem': amount,
			'sub_dia': amount/dias_total_sub,
			'days_total': dias_total,
			'days': dias_sub,
			'total_sub': round(amount/dias_total_sub,2)*dias_sub,
		}
		self.env['hr.subsidies.total'].create(data_total)

		dias_periodo = 0
		year_1 = date_start.year
		year_2 = self.date_end.year
		if year_1 == year_2:
			nro_meses = (self.date_end.month-date_start.month) + 1
		else:
			nro_meses = (13 - date_start.month) + self.date_end.month
		date = date_start
		# print("date",date)
		# print("nro_meses",nro_meses)
		for c, fee in enumerate(range(nro_meses), 1):
			last_day = calendar.monthrange(date.year,date.month)[1]
			# print("last_day",last_day)
			if c == 1 and c != nro_meses:
				# print("c pri",c)
				dias_periodo = last_day - date_start.day + 1
			elif c == nro_meses:
				# print("c ult",c)
				date = self.date_end
				if self.type == 'illness':
					if c == 1:
						dias_periodo = self.date_end.day - date_start.day +1
						# print("date_start.day",date_start.day +1)
					else:
						dias_periodo = self.date_end.day
					# print("dias_periodo",dias_periodo)
				else:
					dias_periodo = self.date_end.day
			else:
				# print("c",c)
				date = date
				dias_periodo = last_day
			# print("date",date)
			# print("dias_periodo",dias_periodo)
			periodo=self.env['hr.period'].search([('date_start', '<=', date),('date_end', '>=',date)],limit=1).id
			date = date + relativedelta(months=1)

			self.env['hr.subsidies.periodo'].create({
				'subsidies_id':self.id,
				'periodo_id': periodo,
				'days': dias_periodo,
				'sub_dia': amount/dias_total_sub,
				'total_sub': round(amount/dias_total_sub,2)*dias_periodo,
			})
		# record.state = 'verify'
		return self.env['popup.it'].get_message('Se calculo Correctamente')

class HrSubsidiesLine(models.Model):
	_name = 'hr.subsidies.line'
	_description = 'Subsidies Line'

	subsidies_id = fields.Many2one('hr.subsidies', ondelete='cascade')
	# employee_id = fields.Many2one('hr.employee', string='Empleado')
	# contract_id = fields.Many2one('hr.contract', string='Contrato')
	# identification_id = fields.Char(related='employee_id.identification_id', string='Nro Documento')
	periodo_id = fields.Many2one('hr.period', string='Periodo')
	wage = fields.Float(string='Basico')
	vacation = fields.Float(string='Vacaciones')
	household_allowance = fields.Float(string='Asignacion Familiar')
	commission = fields.Float(string='Comisiones')
	extra_hours = fields.Float(string='Horas Extras')
	others_income = fields.Float(string='Otros Ingresos')
	lacks = fields.Float(string='Dscto Inasistencias')
	total = fields.Float(string='Base Imponible', compute="get_total", store=True)

	@api.depends('wage', 'vacation','household_allowance','commission','extra_hours','others_income','lacks')
	def get_total(self):
		for i in self:
			i.total = i.wage + i.vacation + i.household_allowance + i.commission + i.extra_hours + i.others_income - i.lacks


class HrSubsidiesTotal(models.Model):
	_name = 'hr.subsidies.total'
	_description = 'Subsidies Total'

	subsidies_id = fields.Many2one('hr.subsidies', ondelete='cascade')
	total_rem = fields.Float(string='Total Rem')
	sub_dia = fields.Float(string='Sub por Dia')
	days_total = fields.Integer(string="Total Dias")
	days = fields.Integer(string="Dias sub")
	total_sub = fields.Float(string='Total subsidio')


class HrSubsidiesPeriodo(models.Model):
	_name = 'hr.subsidies.periodo'
	_description = 'Subsidies Periodo'

	subsidies_id = fields.Many2one('hr.subsidies', ondelete='cascade')
	employee_id = fields.Many2one(related='subsidies_id.employee_id', store=True)
	# maternidad_input_id = fields.Many2one(related='subsidies_id.maternidad_input_id', store=True)
	periodo_id = fields.Many2one('hr.period', string='Periodo')
	days = fields.Integer(string="Dias")
	sub_dia = fields.Float(string='Sub por Dia')
	total_sub = fields.Float(string='Total subsidio')
	validation = fields.Selection([('not payed', 'NO PAGADO'), ('paid out', 'PAGADO')], string='Validacion', default='not payed')

	main_parameter_id = fields.Many2one('hr.main.parameter', ondelete='cascade')
	maternidad_input_id = fields.Many2one(related='main_parameter_id.maternidad_input_id', store=True)
	# maternidad_wd_id = fields.Many2one(related='main_parameter_id.maternidad_wd_id', store=True)
	enfermedad_input_id = fields.Many2one(related='main_parameter_id.enfermedad_input_id', store=True)
	# enfermedad_wd_id = fields.Many2one(related='main_parameter_id.enfermedad_wd_id', store=True)

	@api.model
	def default_get(self, fields):
		# self._cr.execute('truncate table hr_plame_wizard restart identity')
		res = super(HrSubsidiesPeriodo, self).default_get(fields)
		parameters = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		res.update({'main_parameter_id': parameters.id})
		return res

	def turn_paid_out(self):
		for record in self:
			record.validation = 'paid out'

	def set_not_payed(self):
		for record in self:
			record.validation = 'not payed'
