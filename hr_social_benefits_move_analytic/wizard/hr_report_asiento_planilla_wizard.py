# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrReportAsientoPlanillaWizard(models.TransientModel):
	_name = 'hr.report.asiento.planilla.wizard'
	_description = 'Hr Report Asiento Planilla Wizard'

	name = fields.Char()
	type_report =  fields.Selection([('plani','Planilla'),
									 ('grati','Gratificacion'),
									 ('cts','CTS')], default='plani',string=u'Tipo de Reporte', required=True)
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo')
	gratification_id = fields.Many2one('hr.gratification', string='Periodo')
	cts_id = fields.Many2one('hr.cts', string='Periodo')
	employees_ids = fields.Many2many('hr.employee', 'report_asiento_planilla_employee_rel', 'employee_id', 'report_id', 'Empleados')
	allemployees = fields.Boolean('Todos los Empleados', default=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],default='pantalla',string=u'Mostrar en', required=True)

	company_id = fields.Many2one('res.company', string=u'Compañia', required=True, default=lambda self: self.env.company, readonly=True)

	# METODOS PARA ANALISIS DE ASIENTOS DE PLANILLAS
	@api.onchange('allemployees')
	def onchange_allemployees(self):
		if self.allemployees == False:
			employee_ids = []
			if self.type_report == 'plani':
				for employe in self.payslip_run_id.slip_ids:
					employee_ids.append(employe.employee_id.id)
			elif self.type_report == 'grati':
				for employe in self.gratification_id.line_ids:
					employee_ids.append(employe.employee_id.id)
			elif self.type_report == 'cts':
				for employe in self.cts_id.line_ids:
					employee_ids.append(employe.employee_id.id)
			# print("employee_ids",employee_ids)
			domain = {"employees_ids": [("id", "in", employee_ids)]}
			return {"domain": domain}

	def get_all(self):
		# self.domain_dates()
		# print(self._get_sql(0))
		if self.type_report == 'plani':
			self.env.cr.execute("""
						DROP VIEW IF EXISTS hr_report_asiento_planilla;
						CREATE OR REPLACE view hr_report_asiento_planilla as (""" + self._get_sql(0) + """)""")
			if self.type_show == 'pantalla':
				return {
					'name': 'Reporte Asiento Planilla Detallado',
					'type': 'ir.actions.act_window',
					'res_model': 'hr.report.asiento.planilla',
					'view_mode': 'tree,pivot',
					'views': [(False, 'tree'), (False, 'pivot')],
				}
			option = 0
			if self.type_show == 'excel':
				return self.get_excel(option)

		elif self.type_report == 'grati':
			self.env.cr.execute("""
						DROP VIEW IF EXISTS hr_report_asiento_planilla;
						CREATE OR REPLACE view hr_report_asiento_planilla as (""" + self._get_sql_grati(0) + """)""")
			if self.type_show == 'pantalla':
				return {
					'name': 'Reporte Asiento Planilla Detallado',
					'type': 'ir.actions.act_window',
					'res_model': 'hr.report.asiento.planilla',
					'view_mode': 'tree,pivot',
					'views': [(False, 'tree'), (False, 'pivot')],
				}
			option = 0
			if self.type_show == 'excel':
				return self.get_excel(option)

		elif self.type_report == 'cts':
			self.env.cr.execute("""
						DROP VIEW IF EXISTS hr_report_asiento_planilla;
						CREATE OR REPLACE view hr_report_asiento_planilla as (""" + self._get_sql_cts(0) + """)""")
			if self.type_show == 'pantalla':
				return {
					'name': 'Reporte Asiento Planilla Detallado',
					'type': 'ir.actions.act_window',
					'res_model': 'hr.report.asiento.planilla',
					'view_mode': 'tree,pivot',
					'views': [(False, 'tree'), (False, 'pivot')],
				}
			option = 0
			if self.type_show == 'excel':
				return self.get_excel(option)

	def get_journals(self):
		# self.domain_dates()
		if self.allemployees == False:
			if self.type_report == 'plani':
				self.env.cr.execute("""
							DROP VIEW IF EXISTS hr_report_asiento_planilla;
							CREATE OR REPLACE view hr_report_asiento_planilla as (""" + self._get_sql(1) + """)""")
				if self.type_show == 'pantalla':
					return {
						'name': 'Reporte Asiento Planilla Detallado',
						'type': 'ir.actions.act_window',
						'res_model': 'hr.report.asiento.planilla',
						'view_mode': 'tree,pivot',
						'views': [(False, 'tree'), (False, 'pivot')],
					}
				option = 1
				if self.type_show == 'excel':
					return self.get_excel(option)

			elif self.type_report == 'grati':
				self.env.cr.execute("""
							DROP VIEW IF EXISTS hr_report_asiento_planilla;
							CREATE OR REPLACE view hr_report_asiento_planilla as (""" + self._get_sql_grati(1) + """)""")
				# print("self._get_sql_grati(1)",self._get_sql_grati(1))
				if self.type_show == 'pantalla':
					return {
						'name': 'Reporte Asiento Planilla Detallado',
						'type': 'ir.actions.act_window',
						'res_model': 'hr.report.asiento.planilla',
						'view_mode': 'tree,pivot',
						'views': [(False, 'tree'), (False, 'pivot')],
					}
				option = 1
				if self.type_show == 'excel':
					return self.get_excel(option)

			elif self.type_report == 'cts':
				self.env.cr.execute("""
							DROP VIEW IF EXISTS hr_report_asiento_planilla;
							CREATE OR REPLACE view hr_report_asiento_planilla as (""" + self._get_sql_cts(1) + """)""")
				if self.type_show == 'pantalla':
					return {
						'name': 'Reporte Asiento Planilla Detallado',
						'type': 'ir.actions.act_window',
						'res_model': 'hr.report.asiento.planilla',
						'view_mode': 'tree,pivot',
						'views': [(False, 'tree'), (False, 'pivot')],
					}
				option = 1
				if self.type_show == 'excel':
					return self.get_excel(option)
		else:
			raise UserError('Debe escoger al menos un Empleado.')

	def _get_sql(self, option):
		sql_employees = "and he.id in (%s) " % (','.join(str(i) for i in self.employees_ids.ids)) if option == 1 else ""
		sql_payslips = "and hp.id in (%s)" % (','.join(str(i) for i in self.payslip_run_id.slip_ids.ids))

		struct_id = self.env['hr.payroll.structure'].search([('schedule_pay', '=', 'monthly'), ('active', '=', True), ('company_id', '=', self.env.company.id)],limit=1).id
		SalaryRules = self.env['hr.salary.rule'].search([('is_detail_cta', '=', True), ('struct_id', '=', struct_id)],order='sequence')
		if SalaryRules:
			# print("SalaryRules.mapped('code')",len(SalaryRules.mapped('code')))
			if len(SalaryRules.mapped('code')) == 1:
				codes = str(tuple(SalaryRules.mapped('code')))
				codes = "%s" % (codes.replace(',)', ')'))
				codes_afp = "('COMFI','COMMIX','SEGI','A_JUB' %s" % (codes.replace('(', ','))
				codes_afp = "%s" % (codes_afp.replace(',)', ')'))
			else:
				codes = str(tuple(SalaryRules.mapped('code')))
				codes_afp = "('COMFI','COMMIX','SEGI','A_JUB' %s" % (codes.replace('(', ','))
		else:
			codes = "('')"
			codes_afp = "('COMFI','COMMIX','SEGI','A_JUB')"
		# print("codes",codes)
		# print("codes_afp",codes_afp)

		sql = """SELECT row_number() OVER () AS id, T.* FROM (
select
        T.cta_code,
        T.cta_description,
        CASE WHEN T.check_moorage THEN T.cc_code ELSE null::text END AS cc_code,
        CASE WHEN T.check_moorage THEN T.cc_description ELSE null::text END AS cc_description,
        T.partner_vat,
        T.partner_name,
        T.glosa,
        CASE WHEN T.code_salario in ('FAL','TAR','LSGH','SUSP') THEN 0 ELSE round(T.total::numeric, 2) END AS debit,
        CASE WHEN T.code_salario in ('FAL','TAR','LSGH','SUSP') THEN round(T.total::numeric, 2) ELSE 0 END AS credit
    from(
    select
    aa.code AS cta_code,
    aa.name->>'en_US' AS cta_description,
    aa.check_moorage AS check_moorage,
    aaa.code AS cc_code,
    aaa.name->>'en_US' AS cc_description,
    rp.vat as partner_vat,
    rp.name as partner_name,
    hpl.name as glosa,
    hsr.code as code_salario,
    hpl.slip_id,
    hpl.salary_rule_id,
    hpl.employee_id,
    he.work_location_id,
    hsrl.account_id as account_id,
    hsrl.account_analityc as analytic_account_id,
    round((hpl.total* hadl.percent * 0.01)::numeric, 2) AS total
from hr_payslip_line hpl
inner join hr_payslip hp on hp.id = hpl.slip_id
inner join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
left join hr_contract hc on hpl.contract_id = hc.id
left join hr_employee he on hpl.employee_id = he.id

left join hr_analytic_distribution had on had.id = hc.distribution_id
left join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
left join hr_salary_rule_line hsrl ON hpl.salary_rule_id = hsrl.salary_id AND hadl.analytic_id = hsrl.account_analityc
left join account_analytic_account aaa on aaa.id = hadl.analytic_id
left join account_account aa on hsrl.account_id = aa.id
left join res_partner rp on he.user_partner_id = rp.id
where hpl.total <> 0
	and hsr.code not in ('GRA','BON9','CTS','GRA_TRU','BON9_TRU','CTS_TRU','VATRU','INDEM')
    {sql_employees}
    {sql_payslips}
order by hsr.sequence
)T
where T.cta_code is not null

union all
select distinct
        aa.code as cta_code,
        aa.name->>'en_US' as cta_description,
        CASE WHEN aa.check_moorage THEN aaa.code ELSE null::text END AS cc_code,
        CASE WHEN aa.check_moorage THEN aaa.name->>'en_US' ELSE null::text END AS cc_description,
        rp.vat as partner_vat,
        rp.name as partner_name,
        hsr.name->>'en_US' as glosa,
        0::numeric as debit,
        CASE WHEN aa.check_moorage THEN round((prm.total * hadl.percent * 0.01)::numeric, 2) ELSE round(prm.total-coalesce(Z.retirement_fund,0)::numeric, 2) END AS credit
        from payslip_run_move prm
        inner join hr_payslip hp on hp.id = prm.slip_id
        inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
        inner join hr_contract hc on hc.id = prm.contract_id
        left join hr_employee he on he.id = hc.employee_id
        left join hr_analytic_distribution had on had.id = hc.distribution_id
        left join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
        left join account_analytic_account aaa on aaa.id = hadl.analytic_id
        left join account_account aa on prm.account_credit = aa.id
        left join res_partner rp on he.user_partner_id = rp.id
        
        left join (select prm.slip_id,
                prm.total,
                prm.total*hp.retirement_fund/100 as retirement_fund,
                CASE WHEN hp.is_afp = True
                    THEN CASE WHEN hp.commision_type = 'flow'
                        THEN prm.total*hp.fixed_commision/100
                        ELSE 0 END
                    ELSE 0 END AS fixed_commision,
                CASE WHEN hp.is_afp = True
                    THEN CASE WHEN hp.commision_type = 'mixed'
                        THEN prm.total*hp.mixed_commision/100
                        ELSE 0 END
                    ELSE 0 END AS mixed_commision,
                CASE WHEN hp.is_afp = True THEN prm.total*hp.prima_insurance/100 ELSE 0 END as prima_insurance
        from payslip_run_move prm
        inner join hr_payslip hp on hp.id = prm.slip_id
        where prm.salary_rule_id = (select id from hr_salary_rule where code='VATRU' and company_id = {company})
         and prm.payslip_run_id = {payslip_run_id}
         and prm.company_id = {company}
         and prm.total <> 0 )Z on Z.slip_id = prm.slip_id and (select id from hr_salary_rule where code='ONP' and company_id = {company}) = prm.salary_rule_id
        
        where hsr.code not in {codes_afp} and
        prm.payslip_run_id = {payslip_run_id} and
        prm.company_id = {company} and
        prm.account_credit is not null and
        prm.total <> 0
        and hsr.code not in ('GRA','BON9','CTS','VAC','GRA_TRU','BON9_TRU','CTS_TRU','VATRU','ADE_GRA','ADE_CTS','DES_BBSS')
        {sql_employees}
        {sql_payslips}

union all
select distinct
        aa.code as cta_code,
        aa.name->>'en_US' as cta_description,
        null::text as cc_code,
        null::text as cc_description,
        rp.vat as partner_vat,
        rp.name as partner_name,
        hsr.name->>'en_US' as glosa,
        0::numeric as debit,
        case when hsr.code in {codes} 
        	then abs(prm.total + round(coalesce(X.credit,0)::numeric, 2) - round(coalesce(Y.credit,0)::numeric, 2) - round((coalesce(Z.total,0)-coalesce(Z.retirement_fund,0)
                                -coalesce(Z.fixed_commision,0)-coalesce(Z.mixed_commision,0)-coalesce(Z.prima_insurance,0))::numeric, 2))
            else 0 end credit
        from payslip_run_move prm
        inner join hr_payslip hp on hp.id = prm.slip_id
        inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
        inner join hr_contract hc on hc.id = prm.contract_id
        left join hr_employee he on he.id = hc.employee_id
        left join account_account aa on aa.id = prm.account_credit
        left join res_partner rp on rp.id = he.user_partner_id
        
        left join (select prm.slip_id,
                prm.total,
                prm.total*hp.retirement_fund/100 as retirement_fund,
                CASE WHEN hp.is_afp = True
                    THEN CASE WHEN hp.commision_type = 'flow'
                        THEN prm.total*hp.fixed_commision/100
                        ELSE 0 END
                    ELSE 0 END AS fixed_commision,
                CASE WHEN hp.is_afp = True
                    THEN CASE WHEN hp.commision_type = 'mixed'
                        THEN prm.total*hp.mixed_commision/100
                        ELSE 0 END
                    ELSE 0 END AS mixed_commision,
                CASE WHEN hp.is_afp = True THEN prm.total*hp.prima_insurance/100 ELSE 0 END as prima_insurance
        from payslip_run_move prm
        inner join hr_payslip hp on hp.id = prm.slip_id
        where prm.salary_rule_id = (select id from hr_salary_rule where code='VATRU' and company_id = {company})
         and prm.payslip_run_id = {payslip_run_id}
         and prm.company_id = {company}
         and prm.total <> 0 )Z on Z.slip_id = prm.slip_id and (select id from hr_salary_rule where code='NETREMU' and company_id = {company}) = prm.salary_rule_id
        
        left join (select
                hlec.employee_id,
                hp.id as slip_id,
               coalesce(hlec.expenses,0) as credit
               from hr_liquidation_extra_concepts hlec
                        inner join hr_liquidation hl ON hl.id = hlec.liquidation_id
                        left join hr_payslip hp on (hp.employee_id = hlec.employee_id and hp.payslip_run_id= hl.payslip_run_id)
               where hl.company_id = {company}
                 and hl.payslip_run_id = {payslip_run_id}
                 and hlec.expenses is not null
                 and hlec.expenses <> 0
        )X on X.slip_id = prm.slip_id and (select id from hr_salary_rule where code='NETREMU' and company_id = {company}) = prm.salary_rule_id
        
        left join (select distinct
                                hec.employee_id,
                                hp.id as slip_id,
                                hsr.name->>'en_US' as description,
                               hsr.id as salary_rule_id,
                               CASE WHEN hecl.type = 'in' THEN round(hecl.amount::numeric, 2) ELSE 0 END  AS debit,
                               CASE WHEN hecl.type = 'out' THEN round(hecl.amount::numeric, 2) ELSE 0 END AS credit
               from hr_extra_concept_line hecl
                        inner join hr_liquidation_extra_concepts hec on hec.id = hecl.extra_concept_id
                        inner join hr_liquidation hl ON hl.id = hec.liquidation_id
                        inner join hr_payslip_input_type hpit on hpit.id = hecl.name_input_id
                        inner join hr_salary_rule hsr on hsr.code = hpit.code
                        left join hr_payslip hp on (hp.employee_id = hec.employee_id and hp.payslip_run_id= hl.payslip_run_id)
               where hl.company_id = {company}
                 and hl.payslip_run_id = {payslip_run_id}
                 and hecl.amount is not null
                 and hecl.amount <> 0
               )Y on Y.slip_id = prm.slip_id and Y.salary_rule_id = prm.salary_rule_id
        
        where hsr.code in {codes} and
        prm.payslip_run_id = {payslip_run_id} and
        prm.company_id = {company} and
        prm.account_credit is not null and
        prm.total <> 0
        and hsr.code not in ('GRA','BON9','CTS','VATRU','GRA_TRU','BON9_TRU','CTS_TRU','ADE_GRA','ADE_CTS','DES_BBSS')
        {sql_employees}
        {sql_payslips}

union all
select distinct
    aa.code as cta_code,
    aa.name->>'en_US' as cta_description,
    null::text as cc_code,
    null::text as cc_description,
    rp.vat as partner_vat,
    rp.name as partner_name,
    hm.name as glosa,
    0::numeric as debit,
    abs(round((sum(prm.total)-coalesce(Z.retirement_fund,0)-coalesce(Z.fixed_commision,0)-coalesce(Z.mixed_commision,0)-coalesce(Z.prima_insurance,0))::numeric, 2)) as credit
    from payslip_run_move prm
    inner join hr_payslip hp on hp.id = prm.slip_id
    inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
    inner join hr_contract hc on hc.id = prm.contract_id
    left join hr_employee he on he.id = hc.employee_id
    inner join hr_membership hm on hm.id = hc.membership_id
    left join account_account aa on aa.id = hm.account_id
    left join res_partner rp on rp.id = he.user_partner_id
    
    left join (select prm.slip_id,
            prm.total,
            prm.total*hp.retirement_fund/100 as retirement_fund,
            CASE WHEN hp.commision_type = 'flow' THEN prm.total*hp.fixed_commision/100 ELSE 0 END AS fixed_commision,
            CASE WHEN hp.commision_type = 'mixed' THEN prm.total*hp.mixed_commision/100 ELSE 0 END AS mixed_commision,
            prm.total*hp.prima_insurance/100 as prima_insurance
    from payslip_run_move prm
    inner join hr_payslip hp on hp.id = prm.slip_id
    where prm.salary_rule_id = (select id from hr_salary_rule where code='VATRU' and company_id = {company})
     and prm.payslip_run_id = {payslip_run_id}
     and prm.company_id = {company}
     and hp.is_afp = True
     and prm.total <> 0)Z on Z.slip_id = prm.slip_id
    
    where hsr.code in ('COMFI','COMMIX','SEGI','A_JUB') and
    prm.payslip_run_id = {payslip_run_id} and
    prm.company_id = {company} and
    hm.account_id is not null and
    prm.total <> 0
    {sql_employees}
    {sql_payslips}
    group by aa.code,
             aa.name,
             rp.vat,
             rp.name,
             hm.name,
             Z.retirement_fund,Z.fixed_commision,Z.mixed_commision,Z.prima_insurance
    ) T
    where T.debit!=0 or T.credit!=0
    order by T.partner_name,T.credit,T.glosa
				""".format(
				payslip_run_id = self.payslip_run_id.id,
				company = self.company_id.id,
				codes_afp = codes_afp,
				codes = codes,
				sql_payslips = sql_payslips,
				sql_employees = sql_employees
		)
		return sql

	def _get_sql_grati(self, option):
		sql_employees = "and he.id in (%s) " % (','.join(str(i) for i in self.employees_ids.ids)) if option == 1 else ""

		sql = """SELECT row_number() OVER () AS id, T.* FROM (
select
    T.cta_code,
    T.cta_description,
    null::text AS cc_code,
    null::text AS cc_description,
    T.partner_vat,
    T.partner_name,
    T.glosa,
    sum(T.debit) as debit,
    0::numeric as credit
from (
         select distinct
             hgl.id,
             aa.code AS cta_code,
             aa.name->>'en_US' AS cta_description,
             rp.vat as partner_vat,
             rp.name as partner_name,
             'Provision de Gratificacion'::text as glosa,
             round(hgl.prov_acumulado::numeric, 2) as debit
         from hr_gratification_line hgl
                  inner join hr_gratification hg ON hg.id = hgl.gratification_id
                  left join hr_contract hc on hc.id = hgl.contract_id
                  left join hr_employee he on he.id = hc.employee_id
                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_GRA' and company_id = {company})
                  left join account_account aa on prm.account_credit = aa.id
                  left join res_partner rp on he.user_partner_id = rp.id
         where hg.company_id = {company}
           and hg.id = {gratification_id}
           and hgl.prov_acumulado is not null
           {sql_employees}
     ) T
group by
    T.cta_code,
    T.cta_description,
    T.partner_vat,
    T.partner_name,
    T.glosa


union all
select
    T.cta_code,
    T.cta_description,
    CASE WHEN T.check_moorage THEN T.cc_code ELSE null::text END AS cc_code,
    CASE WHEN T.check_moorage THEN T.cc_description ELSE null::text END AS cc_description,
    T.partner_vat,
    T.partner_name,
    T.glosa,
    CASE WHEN sum(T.monto_grat) > 0 THEN round(sum(T.monto_grat)::numeric, 2) ELSE 0 END AS debit,
    CASE WHEN sum(T.monto_grat) > 0 THEN 0 ELSE round(sum(abs(T.monto_grat))::numeric, 2) END AS credit
from (
         SELECT
             aa.code AS cta_code,
             aa.name->>'en_US' AS cta_description,
             aa.check_moorage AS check_moorage,
             aaa.code AS cc_code,
             aaa.name->>'en_US' AS cc_description,
             rp.vat as partner_vat,
             rp.name as partner_name,
             hsr.name->>'en_US' as glosa,
             (hgl.total - coalesce(hgl.prov_acumulado,0)) * (hadl.percent::numeric * 0.01) AS monto_grat
         FROM hr_gratification_line hgl
                  inner join hr_gratification hg ON hg.id = hgl.gratification_id
                  inner join hr_contract hc on hc.id = hgl.contract_id
                  inner join hr_employee he on he.id = hc.employee_id
                  inner join hr_analytic_distribution had on had.id = hc.distribution_id
                  inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
                  left join hr_salary_rule_line hsrl ON (select id from hr_salary_rule where code='GRA' and company_id = {company}) = hsrl.salary_id
             												AND hadl.analytic_id = hsrl.account_analityc
                  inner join hr_salary_rule hsr on hsr.id = hsrl.salary_id
                  left join account_analytic_account aaa on aaa.id = hsrl.account_analityc
                  left join account_account aa on hsrl.account_id = aa.id
                  left join res_partner rp on he.user_partner_id = rp.id
         where hg.company_id = {company}
           and hg.id = {gratification_id}
           {sql_employees}
     )T
where T.monto_grat <> 0
group by T.cta_code,
         T.cta_description,
         T.check_moorage,
         T.cc_code,
         T.cc_description,
         T.partner_vat,
         T.partner_name,
         T.glosa

union all
select
    T.cta_code,
    T.cta_description,
    null::text AS cc_code,
    null::text AS cc_description,
    T.partner_vat,
    T.partner_name,
    T.glosa,
    0::numeric as debit,
    sum(T.credit) as credit
from (
         select distinct
             hgl.id,
             aa.code AS cta_code,
             aa.name->>'en_US' AS cta_description,
             rp.vat as partner_vat,
             rp.name as partner_name,
             'Gratificacion a Pagar'::text as glosa,
             round(hgl.total::numeric, 2) as credit
         from hr_gratification_line hgl
                  inner join hr_gratification hg ON hg.id = hgl.gratification_id
                  left join hr_contract hc on hc.id = hgl.contract_id
                  left join hr_employee he on he.id = hc.employee_id
                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='GRA' and company_id = {company})
                  left join account_account aa on prm.account_debit = aa.id
                  left join res_partner rp on he.user_partner_id = rp.id
         where hg.company_id = {company}
           and hg.id = {gratification_id}
           and hgl.total is not null
           {sql_employees}
         union all
         select distinct
             hgl.id,
             aa.code AS cta_code,
             aa.name->>'en_US' AS cta_description,
             rp.vat as partner_vat,
             rp.name as partner_name,
             'Descuento por Adelantos'::text as glosa,
             round(hgl.advance_amount::numeric, 2) as credit
         from hr_gratification_line hgl
                  inner join hr_gratification hg ON hg.id = hgl.gratification_id
                  left join hr_contract hc on hc.id = hgl.contract_id
                  left join hr_employee he on he.id = hc.employee_id
                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADELANTO' and company_id = {company})
                  left join account_account aa on prm.account_credit = aa.id
                  left join res_partner rp on he.user_partner_id = rp.id
         where hg.company_id = {company}
           and hg.id = {gratification_id}
           and hgl.advance_amount is not null
           {sql_employees}
         union all
         select distinct
             hgl.id,
             aa.code AS cta_code,
             aa.name->>'en_US' AS cta_description,
             rp.vat as partner_vat,
             rp.name as partner_name,
             'Descuento por Prestamos'::text as glosa,
             round(hgl.loan_amount::numeric, 2) as credit
         from hr_gratification_line hgl
                  inner join hr_gratification hg ON hg.id = hgl.gratification_id
                  left join hr_contract hc on hc.id = hgl.contract_id
                  left join hr_employee he on he.id = hc.employee_id
                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='PREST' and company_id = {company})
                  left join account_account aa on prm.account_credit = aa.id
                  left join res_partner rp on he.user_partner_id = rp.id
         where hg.company_id = {company}
           and hg.id = {gratification_id}
           and hgl.loan_amount is not null
           {sql_employees}
--         union all
--         select distinct
--             hgl.id,
--             aa.code AS cta_code,
--             aa.name->>'en_US' AS cta_description,
--             rp.vat as partner_vat,
--             rp.name as partner_name,
--             'Descuento Retencion Judicial'::text as glosa,
--             round(hgl.ret_jud_amount::numeric, 2) as credit
--         from hr_gratification_line hgl
--                  inner join hr_gratification hg ON hg.id = hgl.gratification_id
--                  left join hr_contract hc on hc.id = hgl.contract_id
--                  left join hr_employee he on he.id = hc.employee_id
--                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='RET_JUD' and company_id = {company})
--                  left join account_account aa on prm.account_credit = aa.id
--                  left join res_partner rp on he.user_partner_id = rp.id
--         where hg.company_id = {company}
--           and hg.id = {gratification_id}
--           and hgl.ret_jud_amount is not null
--           {sql_employees}
     ) T
where T.credit <> 0
group by
    T.cta_code,
    T.cta_description,
    T.partner_vat,
    T.partner_name,
    T.glosa

    ) T
    where T.debit!=0 or T.credit!=0
    order by T.partner_name,T.credit,T.glosa
				""".format(
			gratification_id=self.gratification_id.id,
			company=self.company_id.id,
			sql_employees = sql_employees
		)
		return sql

	def _get_sql_cts(self, option):
		sql_employees = "and he.id in (%s) " % (','.join(str(i) for i in self.employees_ids.ids)) if option == 1 else ""

		sql = """SELECT row_number() OVER () AS id, T.* FROM (
select
    T.cta_code,
    T.cta_description,
    null::text AS cc_code,
    null::text AS cc_description,
    T.partner_vat,
    T.partner_name,
    T.glosa,
    sum(T.debit) as debit,
    0::numeric as credit
from (
         select distinct
             hcl.id,
             aa.code AS cta_code,
             aa.name->>'en_US' AS cta_description,
             rp.vat as partner_vat,
             rp.name as partner_name,
             'Provision de CTS'::text as glosa,
             round(hcl.prov_acumulado::numeric, 2) as debit
         from hr_cts_line hcl
	        inner join hr_cts hcts ON hcts.id = hcl.cts_id
	        left join hr_contract hc on hc.id = hcl.contract_id
	        left join hr_employee he on he.id = hc.employee_id
	        LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_CTS' and company_id = {company})
	        left join account_account aa on prm.account_credit = aa.id
            left join res_partner rp on he.user_partner_id = rp.id
	         where hcts.company_id = {company}
	           and hcts.id = {cts_id}
	           and hcl.prov_acumulado is not null
           {sql_employees}
     ) T
group by
    T.cta_code,
    T.cta_description,
    T.partner_vat,
    T.partner_name,
    T.glosa

union all
select
    T.cta_code,
    T.cta_description,
    CASE WHEN T.check_moorage THEN T.cc_code ELSE null::text END AS cc_code,
    CASE WHEN T.check_moorage THEN T.cc_description ELSE null::text END AS cc_description,
    T.partner_vat,
    T.partner_name,
    T.glosa,
    CASE WHEN sum(T.monto_cts) > 0 THEN round(sum(T.monto_cts)::numeric, 2) ELSE 0 END AS debit,
    CASE WHEN sum(T.monto_cts) > 0 THEN 0 ELSE round(sum(abs(T.monto_cts))::numeric, 2) END AS credit
from (
         SELECT
             aa.code AS cta_code,
             aa.name->>'en_US' AS cta_description,
             aa.check_moorage AS check_moorage,
             aaa.code AS cc_code,
             aaa.name->>'en_US' AS cc_description,
             rp.vat as partner_vat,
             rp.name as partner_name,
             hsr.name->>'en_US' as glosa,
             (hcl.total_cts - coalesce(hcl.prov_acumulado,0)) * (hadl.percent::numeric * 0.01) AS monto_cts
         FROM hr_cts_line hcl
	              inner join hr_cts hcts ON hcts.id = hcl.cts_id
	              inner join hr_contract hc on hc.id = hcl.contract_id
                  inner join hr_employee he on he.id = hc.employee_id
                  inner join hr_analytic_distribution had on had.id = hc.distribution_id
	              inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
	              left join hr_salary_rule_line hsrl ON (select id from hr_salary_rule where code='CTS' and company_id = {company}) = hsrl.salary_id
	                                                        AND hadl.analytic_id = hsrl.account_analityc
	              inner join hr_salary_rule hsr on hsr.id = hsrl.salary_id
                  left join account_analytic_account aaa on aaa.id = hsrl.account_analityc
                  left join account_account aa on hsrl.account_id = aa.id
                  left join res_partner rp on he.user_partner_id = rp.id
         where hcts.company_id = {company}
	           and hcts.id = {cts_id}
           {sql_employees}
     )T
where T.monto_cts <> 0
group by T.cta_code,
         T.cta_description,
         T.check_moorage,
         T.cc_code,
         T.cc_description,
         T.partner_vat,
         T.partner_name,
         T.glosa

union all
select
    T.cta_code,
    T.cta_description,
    null::text AS cc_code,
    null::text AS cc_description,
    T.partner_vat,
    T.partner_name,
    T.glosa,
    0::numeric as debit,
    sum(T.credit) as credit
from (
         select distinct
             hcl.id,
             aa.code AS cta_code,
             aa.name->>'en_US' AS cta_description,
             rp.vat as partner_vat,
             rp.name as partner_name,
             'CTS a Pagar'::text as glosa,
             round(hcl.cts_soles::numeric, 2) as credit
         from hr_cts_line hcl
	            inner join hr_cts hcts ON hcts.id = hcl.cts_id
	            left join hr_contract hc on hc.id = hcl.contract_id
	            left join hr_employee he on he.id = hc.employee_id
	            LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='CTS' and company_id = {company})
                  left join account_account aa on prm.account_debit = aa.id
                  left join res_partner rp on he.user_partner_id = rp.id
         where hcts.company_id = {company}
	           and hcts.id = {cts_id}
	           and hcl.cts_soles is not null
           		{sql_employees}
         union all
         select distinct
             hcl.id,
             aa.code AS cta_code,
             aa.name->>'en_US' AS cta_description,
             rp.vat as partner_vat,
             rp.name as partner_name,
             'Descuento por Adelantos'::text as glosa,
             round(hcl.advance_amount::numeric, 2) as credit
         from hr_cts_line hcl
	            inner join hr_cts hcts ON hcts.id = hcl.cts_id
	            left join hr_contract hc on hc.id = hcl.contract_id
	            left join hr_employee he on he.id = hc.employee_id
	            LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADELANTO' and company_id = {company})
                  left join account_account aa on prm.account_credit = aa.id
                  left join res_partner rp on he.user_partner_id = rp.id
         where hcts.company_id = {company}
	           and hcts.id = {cts_id}
	           and hcl.advance_amount is not null
           {sql_employees}
         union all
         select distinct
             hcl.id,
             aa.code AS cta_code,
             aa.name->>'en_US' AS cta_description,
             rp.vat as partner_vat,
             rp.name as partner_name,
             'Descuento por Prestamos'::text as glosa,
             round(hcl.loan_amount::numeric, 2) as credit
         from hr_cts_line hcl
	            inner join hr_cts hcts ON hcts.id = hcl.cts_id
	            left join hr_contract hc on hc.id = hcl.contract_id
	            left join hr_employee he on he.id = hc.employee_id
	            LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='PREST' and company_id = {company})
                  left join account_account aa on prm.account_credit = aa.id
                  left join res_partner rp on he.user_partner_id = rp.id
         where hcts.company_id = {company}
	           and hcts.id = {cts_id}
	           and hcl.loan_amount is not null
           		{sql_employees}
--         union all
--         select distinct
--             hcl.id,
--             aa.code AS cta_code,
--             aa.name->>'en_US' AS cta_description,
--             rp.vat as partner_vat,
--             rp.name as partner_name,
--             'Descuento Retencion Judicial'::text as glosa,
--             round(hcl.ret_jud_amount::numeric, 2) as credit
--         from hr_cts_line hcl
--	            inner join hr_cts hcts ON hcts.id = hcl.cts_id
--	            left join hr_contract hc on hc.id = hcl.contract_id
--	            left join hr_employee he on he.id = hc.employee_id
--	            LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='RET_JUD' and company_id = {company})
--                  left join account_account aa on prm.account_credit = aa.id
--                  left join res_partner rp on he.user_partner_id = rp.id
--         where hcts.company_id = {company}
--	           and hcts.id = {cts_id}
--	           and hcl.ret_jud_amount is not null
--           		{sql_employees}
     ) T
where T.credit <> 0
group by
    T.cta_code,
    T.cta_description,
    T.partner_vat,
    T.partner_name,
    T.glosa

    ) T
    where T.debit!=0 or T.credit!=0
    order by T.partner_name,T.credit,T.glosa
				""".format(
			cts_id=self.cts_id.id,
			company=self.company_id.id,
			sql_employees = sql_employees
		)
		return sql

	def get_excel(self, option):
		import io
		from xlsxwriter.workbook import Workbook
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		directory = MainParameter.dir_create_file

		if not directory:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		workbook = Workbook(directory + 'Reporte_Asiento_Detallado.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Reporte Asiento Detallado")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(0, 0, 0, 7, "Empresa: %s" % self.company_id.partner_id.name or '', formats['especial2'])
		worksheet.merge_range(1, 0, 1, 7, "RUC: %s" % self.company_id.partner_id.vat or '', formats['especial2'])
		worksheet.merge_range(2, 0, 2, 7, "Direccion: %s" % self.company_id.partner_id.street or '', formats['especial2'])

		if self.type_report == 'plani':
			nombre = self.payslip_run_id.name
			voucher = self.payslip_run_id.account_move_id.name
			fecha = self.payslip_run_id.account_move_id.date
			usuario_creo = self.payslip_run_id.account_move_id.create_uid.name
			usuario_mod = self.payslip_run_id.account_move_id.write_uid.name
			self._cr.execute(self._get_sql(option))
			data = self._cr.dictfetchall()
		elif self.type_report == 'grati':
			nombre = self.gratification_id.name
			voucher = self.gratification_id.account_move_id.name
			fecha = self.gratification_id.account_move_id.date
			usuario_creo = self.gratification_id.account_move_id.create_uid.name
			usuario_mod = self.gratification_id.account_move_id.write_uid.name
			self._cr.execute(self._get_sql_grati(option))
			data = self._cr.dictfetchall()
		elif self.type_report == 'cts':
			nombre = self.cts_id.name
			voucher = self.cts_id.account_move_id.name
			fecha = self.cts_id.account_move_id.date
			usuario_creo = self.cts_id.account_move_id.create_uid.name
			usuario_mod = self.cts_id.account_move_id.write_uid.name
			self._cr.execute(self._get_sql_cts(option))
			data = self._cr.dictfetchall()

		worksheet.merge_range(4, 1, 4, 8,"*** REPORTE ASIENTO DETALLADO %s ***" % nombre or '',formats['especial5'])


		x, y = 6, 6

		# print("data", data)

		# estilo personalizado
		boldbord = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		boldbord.set_border(style=1)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		# boldbord.set_align('bottom')
		boldbord.set_text_wrap()
		boldbord.set_font_size(8)
		boldbord.set_bg_color('#99CCFF')

		dateformat = workbook.add_format({'num_format': 'dd-mm-yyyy'})
		dateformat.set_align('center')
		dateformat.set_align('vcenter')
		# dateformat.set_border(style=1)
		dateformat.set_font_size(8)
		dateformat.set_font_name('Times New Roman')

		formatLeft = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': 8})
		numberdos = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		numberdos.set_font_size(8)
		styleFooterSum = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': 9, 'top': 1,
			 'bottom': 2})
		styleFooterSum.set_bottom(6)

		worksheet.write(x, 0, 'Asiento', boldbord)
		worksheet.write(x, 1, 'Cuenta', boldbord)
		worksheet.write(x, 2, 'Descripcion Cuenta', boldbord)
		worksheet.write(x, 3, 'Debe', boldbord)
		worksheet.write(x, 4, 'Haber', boldbord)
		worksheet.write(x, 5, 'Codigo C. Costo', boldbord)
		worksheet.write(x, 6, 'Descripcion C. Costo', boldbord)
		worksheet.write(x, 7, 'DNI Trabajador', boldbord)
		worksheet.write(x, 8, 'Nombre Trabajador', boldbord)
		worksheet.write(x, 9, 'Glosa', boldbord)
		worksheet.write(x, 10, 'Fecha Contable', boldbord)
		worksheet.write(x, 11, 'Usuario Creo', boldbord)
		worksheet.write(x, 12, 'Usuario Modifico', boldbord)

		x += 1

		cont = 0
		cuenta = ''
		totals = [0] * 2
		limiter = 3

		for c, line in enumerate(data, 1):
			if cont == 0:
				cuenta = line['partner_name']
				# print("cuenta",cuenta)
				cont += 1
				worksheet.merge_range(x,0,x,4, 'Empleado: ' + str(cuenta) if line['partner_name'] else '',formats['especial2'])
				x += 1

			if cuenta != line['partner_name']:
				worksheet.write(x, limiter-1, 'Total ', formats['especial2'])
				for total in totals:
					worksheet.write(x, limiter, total, styleFooterSum)
					limiter += 1

				x += 1
				totals = [0] * 2
				limiter = 3

				cuenta = line['partner_name']
				worksheet.merge_range(x,0,x,4, 'Empleado: ' + str(cuenta) if line['partner_name'] else '',formats['especial2'])
				x += 1

			# employee = self.env['hr.employee'].browse(line['employee_id'])
			worksheet.write(x, 0, voucher if voucher else '', formatLeft)
			worksheet.write(x, 1, line['cta_code'] if line['cta_code'] else '', formatLeft)
			worksheet.write(x, 2, line['cta_description'] if line['cta_description'] else '', formatLeft)
			worksheet.write(x, 3, line['debit'] if line['debit'] else 0.0, numberdos)
			worksheet.write(x, 4, line['credit'] if line['credit'] else 0.0, numberdos)
			worksheet.write(x, 5, line['cc_code'] if line['cc_code'] else '', formatLeft)
			worksheet.write(x, 6, line['cc_description'] if line['cc_description'] else '', formatLeft)
			worksheet.write(x, 7, line['partner_vat'] if line['partner_vat'] else '', formatLeft)
			worksheet.write(x, 8, line['partner_name'] if line['partner_name'] else '', formatLeft)
			worksheet.write(x, 9, line['glosa'] if line['glosa'] else '', formatLeft)
			worksheet.write(x, 10, fecha if fecha else '', dateformat)
			worksheet.write(x, 11, usuario_creo if usuario_creo else '', formatLeft)
			worksheet.write(x, 12, usuario_mod if usuario_mod else '', formatLeft)

			totals[0] += line['debit']
			totals[1] += line['credit']

			x += 1

		# x += 1
		worksheet.write(x, limiter - 1, 'Total ', formats['especial2'])
		for total in totals:
			worksheet.write(x, limiter, total, styleFooterSum)
			limiter += 1

		widths = [12, 14, 28, 12, 12, 14, 30, 14, 28, 25, 14, 14]
		worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()
		f = open(directory + 'Reporte_Asiento_Detallado.xlsx', 'rb')
		return self.env['popup.it'].get_file('Asiento Detallado %s.xlsx' % nombre,base64.encodebytes(b''.join(f.readlines())))

