# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	def get_sql(self):
		struct_id=self.env['hr.payroll.structure'].search([('schedule_pay', '=', 'monthly'),('active', '=',True),('company_id', '=', self.env.company.id)],limit=1).id
		SalaryRules = self.env['hr.salary.rule'].search([('is_detail_cta', '=', True), ('struct_id', '=', struct_id)], order='sequence')
		if SalaryRules:
			# print("SalaryRules.mapped('code')",len(SalaryRules.mapped('code')))
			if len(SalaryRules.mapped('code')) == 1:
				codes = str(tuple(SalaryRules.mapped('code')))
				codes = "%s" %(codes.replace(',)',')'))
				codes_afp = "('COMFI','COMMIX','SEGI','A_JUB' %s" %(codes.replace('(',','))
				codes_afp = "%s" %(codes_afp.replace(',)',')'))
			else:
				codes = str(tuple(SalaryRules.mapped('code')))
				codes_afp = "('COMFI','COMMIX','SEGI','A_JUB' %s" %(codes.replace('(',','))
		else:
			codes = "('')"
			codes_afp = "('COMFI','COMMIX','SEGI','A_JUB')"
		# print("codes",codes)
		# print("codes_afp",codes_afp)
		sql = """
				DROP VIEW IF EXISTS hr_payslip_run_move;
				CREATE OR REPLACE VIEW hr_payslip_run_move AS
				(
					SELECT row_number() OVER () AS id, T.* FROM (
	select
    lo.sequence,
	lo.salary_rule_id,
    lo.description,
    CASE WHEN lo.check_moorage THEN lo.analytic_account_id ELSE null::integer END AS analytic_account_id,
    lo.account_id as account_id,
    CASE WHEN lo.code in ('FAL','TAR','LSGH','SUSP') THEN 0 ELSE round(sum(lo.total)::numeric, 2) END AS debit,
    CASE WHEN lo.code in ('FAL','TAR','LSGH','SUSP') THEN round(sum(lo.total)::numeric, 2) ELSE 0 END AS credit,
    null::integer as partner_id
    from (
    select
	    hsr.sequence,
	    hpl.salary_rule_id,
	    hsr.name->>'en_US' as description,
	    hsr.code,
	    hsrl.account_analityc as analytic_account_id,
		hsrl.account_id as account_id,
		aa.check_moorage AS check_moorage,
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
    where hpl.total <> 0 and
	    hp.payslip_run_id = {payslip_run_id} and
	    hp.company_id = {company}
    ) lo
	where lo.account_id is not null
	group by
	lo.sequence,
	lo.salary_rule_id,
	lo.description,
	lo.code,
	lo.analytic_account_id,
	lo.account_id,
	lo.check_moorage

    union all

    select
    lo.sequence,
    lo.salary_rule_id,
    lo.description,
    lo.analytic_account_id,
    lo.account_id as account_id,
    sum(lo.debit) as debit,
    sum(lo.credit) as credit,
    lo.partner_id
    from (
        select distinct
        hp.id,
        prm.sequence,
        prm.salary_rule_id,
        hsr.name->>'en_US' as description,
        CASE WHEN aa.check_moorage THEN aaa.id ELSE 0 END AS analytic_account_id,
        prm.account_credit as account_id,
        0::numeric as debit,
        CASE WHEN aa.check_moorage THEN round((prm.total * hadl.percent * 0.01)::numeric, 2) ELSE round(prm.total::numeric, 2) END AS credit,
        null::integer as partner_id
        from payslip_run_move prm
        inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
        inner join hr_payslip hp on hp.id = prm.slip_id
        inner join hr_contract hc on hc.id = hp.contract_id
        inner join hr_analytic_distribution had on had.id = hc.distribution_id
        inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
        inner join account_analytic_account aaa on aaa.id = hadl.analytic_id
        left join account_account aa on prm.account_credit = aa.id
        where hsr.code not in {codes_afp} and
        prm.payslip_run_id = {payslip_run_id} and
        prm.company_id = {company} and
        prm.account_credit is not null

        union all

        select
        null::integer as id,
        prm.sequence,
        prm.salary_rule_id,
        hsr.name->>'en_US' as description,
        null::integer as analytic_account_id,
        prm.account_credit as account_id,
        0::numeric as debit,
        case when hsr.code in {codes} then prm.total else 0 end credit,
        hr_employee.user_partner_id as partner_id
        from payslip_run_move prm
        inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
        left join hr_contract on prm.contract_id = hr_contract.id
        left join hr_employee on hr_contract.employee_id =  hr_employee.id
        where hsr.code in {codes} and
        prm.payslip_run_id = {payslip_run_id} and
        prm.company_id = {company} and
        prm.account_credit is not null

    ) lo
    group by
    lo.sequence,
    lo.salary_rule_id,
    lo.description,
    lo.analytic_account_id,
    lo.account_id,
    lo.partner_id

    union all
    select distinct
    58 as sequence,
    null::integer as salary_rule_id,
    hm.name::varchar as description,
    null::integer as analytic_account_id,
    hm.account_id as account_id,
    0::numeric as debit,
    round(sum(prm.total)::numeric, 2) as credit,
    null::integer as partner_id
    from payslip_run_move prm
    inner join hr_payslip hp on hp.id = prm.slip_id
    inner join hr_contract hc on hc.id = hp.contract_id
    inner join hr_membership hm on hm.id = hc.membership_id
    inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
    where hsr.code in ('COMFI','COMMIX','SEGI','A_JUB') and
    prm.payslip_run_id = {payslip_run_id} and
    prm.company_id = {company} and
    hm.account_id is not null
    group by hm.name, hm.account_id
					)T
					where T.debit!=0 or T.credit!=0
				)
			""".format(
				payslip_run_id = self.id,
				company = self.env.company.id,
				codes_afp = codes_afp,
				codes = codes
		)
		# print("sql",sql)
		return sql