# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	def get_sql(self):
		struct_id = self.env['hr.payroll.structure'].search([('schedule_pay', '=', 'monthly'),('active', '=',True),('company_id', '=', self.env.company.id)],limit=1).id
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
		    lo.description::varchar,
		    CASE WHEN lo.check_moorage THEN lo.analytic_account_id ELSE null::integer END AS analytic_account_id,
		    lo.account_id as account_id,
		    CASE WHEN lo.code in ('FAL','TAR','LSGH','SUSP') THEN 0 ELSE round(sum(lo.total)::numeric, 2) END AS debit,
		    CASE WHEN lo.code in ('FAL','TAR','LSGH','SUSP') THEN round(sum(lo.total)::numeric, 2) ELSE 0 END AS credit,
		    lo.partner_id
		    from (
				select
				prm.sequence,
				prm.salary_rule_id,
				hsr.name->>'en_US' as description,
				hsr.code,
				aaa.id as analytic_account_id,
				prm.account_debit as account_id,
				aa.check_moorage AS check_moorage,
				round((prm.total * hadl.percent * 0.01)::numeric, 2) AS total,
				null::integer as partner_id
				from payslip_run_move prm
				inner join hr_payslip hp on hp.id = prm.slip_id
				inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
				inner join hr_contract hc on hc.id = prm.contract_id
				left join hr_employee he on he.id = hc.employee_id
				left join hr_analytic_distribution had on had.id = hc.distribution_id
				left join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
				left join account_analytic_account aaa on aaa.id = hadl.analytic_id
				left join account_account aa on prm.account_debit = aa.id
				where prm.total <> 0 and
				hp.payslip_run_id = {payslip_run_id} and
				hp.company_id = {company}
				and hsr.code not in ('GRA','BON9','CTS','GRA_TRU','BON9_TRU','CTS_TRU','VATRU','SMAR','SENF','INDEM')
				
				union all
				select
				prm.sequence,
				prm.salary_rule_id,
				hsr.name->>'en_US' as description,
				hsr.code,
				null::integer as analytic_account_id,
				prm.account_debit as account_id,
				aa.check_moorage AS check_moorage,
				round((prm.total)::numeric, 2) AS total,
				he.user_partner_id as partner_id
				from payslip_run_move prm
				inner join hr_payslip hp on hp.id = prm.slip_id
				inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
				inner join hr_contract hc on hc.id = prm.contract_id
				left join hr_employee he on he.id = hc.employee_id
				left join account_account aa on prm.account_debit = aa.id
				left join res_partner rp on he.user_partner_id = rp.id
				where prm.total <> 0 and
				hp.payslip_run_id = {payslip_run_id} and
				hp.company_id = {company}
				and hsr.code in ('SMAR','SENF')
		    ) lo
		    where lo.account_id is not null
		    group by
		    lo.sequence,
		    lo.salary_rule_id,
		    lo.description,
		    lo.code,
		    lo.analytic_account_id,
		    lo.account_id,
		    lo.check_moorage,
		    lo.partner_id

		union all
		select
		    lo.sequence,
		    lo.salary_rule_id,
		    lo.description::varchar,
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
		        CASE WHEN aa.check_moorage THEN aaa.id ELSE null::integer END AS analytic_account_id,
		        prm.account_credit as account_id,
		        0::numeric as debit,
		        CASE WHEN aa.check_moorage THEN round((prm.total * hadl.percent * 0.01)::numeric, 2) ELSE round(prm.total-coalesce(Z.retirement_fund,0)::numeric, 2) END AS credit,
		        null::integer as partner_id
		        from payslip_run_move prm
		        inner join hr_payslip hp on hp.id = prm.slip_id
		        inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
		        inner join hr_contract hc on hc.id = prm.contract_id
		        left join hr_employee he on he.id = hc.employee_id
		        left join hr_analytic_distribution had on had.id = hc.distribution_id
		        left join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
		        left join account_analytic_account aaa on aaa.id = hadl.analytic_id
		        left join account_account aa on prm.account_credit = aa.id

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

		        union all
		        select
		        null::integer as id,
		        prm.sequence,
		        prm.salary_rule_id,
		        hsr.name->>'en_US' as description,
		        null::integer as analytic_account_id,
		        prm.account_credit as account_id,
		        0::numeric as debit,
		        case when hsr.code in {codes} 
		        	then abs(prm.total + round(coalesce(X.credit,0)::numeric, 2) - round(coalesce(Y.credit,0)::numeric, 2) - round((coalesce(Z.total,0)-coalesce(Z.retirement_fund,0)
		                                -coalesce(Z.fixed_commision,0)-coalesce(Z.mixed_commision,0)-coalesce(Z.prima_insurance,0))::numeric, 2))
		            else 0 end credit,
		        he.user_partner_id as partner_id
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
		               where hsr.company_id = {company}
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
		    ) lo
		    group by
		    lo.sequence,
		    lo.salary_rule_id,
		    lo.description,
		    lo.analytic_account_id,
		    lo.account_id,
		    lo.partner_id

		union all
		select
			58 as sequence,
			null::integer as salary_rule_id,
			T.description::varchar,
			null::integer as analytic_account_id,
			T.account_id,
			0::numeric as debit,
			sum(T.credit) as credit,
			null::integer as partner_id
		from (
		select distinct
		    hc.membership_id,
		    hm.name::varchar as description,
		    hm.account_id as account_id,
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
		    group by hc.membership_id,hm.name, hm.account_id,Z.retirement_fund,Z.fixed_commision,Z.mixed_commision,Z.prima_insurance
		    )T
		group by
			T.description,
			T.account_id
							)T
							where T.debit!=0 or T.credit!=0
							order by T.sequence
						)
					""".format(
				payslip_run_id=self.id,
				company=self.env.company.id,
				codes_afp=codes_afp,
				codes=codes
			)
		# print("sql",sql)
		return sql