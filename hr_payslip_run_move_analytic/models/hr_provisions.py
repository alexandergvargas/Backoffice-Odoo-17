# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class HrProvisiones(models.Model):
	_inherit = 'hr.provisiones'

	main_parameter_id = fields.Many2one('hr.main.parameter', ondelete='cascade')
	gratification_sr_id = fields.Many2one(related='main_parameter_id.gratification_sr_id', store=True)
	bonification_sr_id = fields.Many2one(related='main_parameter_id.bonification_sr_id', store=True)
	cts_sr_id = fields.Many2one(related='main_parameter_id.cts_sr_id', store=True)
	vacation_sr_id = fields.Many2one(related='main_parameter_id.vacation_sr_id', store=True)

	@api.model
	def default_get(self, fields):
		# self._cr.execute('truncate table hr_plame_wizard restart identity')
		res = super(HrProvisiones, self).default_get(fields)
		parameters = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		res.update({'main_parameter_id': parameters.id})
		return res

	def get_move_lines(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if MainParameter.detallar_provision:
			# CONSULTA PARA DETALLAR POR TRABAJADOR
			sql_provision="""
					union all
					select 
					lo.account_id,
					lo.description,
					lo.analytic_account_id,
					sum(lo.debit) as debit,
					sum(lo.credit) as credit,
					lo.partner_id
					from (
						select distinct
							hpcl.id,
							prm.account_credit as account_id,
							'Provision de CTS a Pagar'::text as description,
							0 as analytic_account_id,
							0::numeric as debit,
							round(hpcl.provisiones_cts::numeric, 2) as credit,
							he.user_partner_id as partner_id
							from hr_provisiones_cts_line hpcl
							inner join hr_provisiones hpro ON hpro.id = hpcl.provision_id
							inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
							left join hr_contract hc on hc.id = hpcl.contract_id
							left join hr_employee he on he.id = hc.employee_id
							LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_CTS' and company_id = {company})
							where hpro.company_id = {company}
							and hpr.id = {payslip_run_id}
							and hpro.id = {provision_id}
						union all
						select distinct
							hpgl.id,
							prm.account_credit as account_id,
							'Provision de Gratificacion a Pagar'::text as description,
							0 as analytic_account_id,
							0::numeric as debit,
							round(hpgl.provisiones_grati::numeric, 2) as credit,
							he.user_partner_id as partner_id
							from hr_provisiones_grati_line hpgl
							inner join hr_provisiones hpro ON hpro.id = hpgl.provision_id
							inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
							left join hr_contract hc on hc.id = hpgl.contract_id
							left join hr_employee he on he.id = hc.employee_id
							LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_GRA' and company_id = {company})
							where hpro.company_id = {company}
							and hpr.id = {payslip_run_id}
							and hpro.id = {provision_id}
						union all
						select distinct
							hpgl.id,
							prm.account_credit as account_id,
							'Provision de Gratificacion a Pagar'::text as description,
							0 as analytic_account_id,
							0::numeric as debit,
							round(hpgl.boni_grati::numeric, 2) as credit,
							he.user_partner_id as partner_id
							from hr_provisiones_grati_line hpgl
							inner join hr_provisiones hpro ON hpro.id = hpgl.provision_id
							inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
							left join hr_contract hc on hc.id = hpgl.contract_id
							left join hr_employee he on he.id = hc.employee_id
							LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_GRA' and company_id = {company})
							where hpro.company_id = {company}
							and hpr.id = {payslip_run_id}
							and hpro.id = {provision_id}
						union all
						select distinct
							hpvl.id,
							prm.account_credit as account_id,
							'Provision de Vacaciones a Pagar'::text as description,
							0 as analytic_account_id,
							0::numeric as debit,
							round(hpvl.provisiones_vaca::numeric, 2) as credit,
							he.user_partner_id as partner_id
							from hr_provisiones_vaca_line hpvl
							inner join hr_provisiones hpro ON hpro.id = hpvl.provision_id
							inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
							left join hr_contract hc on hc.id = hpvl.contract_id
							left join hr_employee he on he.id = hc.employee_id
							LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_VAC' and company_id = {company})
							where hpro.company_id = {company}
							and hpr.id = {payslip_run_id}
							and hpro.id = {provision_id}
					) lo
					group by 
					lo.account_id,
					lo.description,
					lo.analytic_account_id,
					lo.partner_id 
			""".format(
			company = self.company_id.id,
			payslip_run_id = self.payslip_run_id.id,
			provision_id = self.id)
		else:
			# CONSULTA PARA RESUMIR LA CTA X PAGAR
			sql_provision="""
					union all
					select 
					lo.account_id,
					lo.description,
					lo.analytic_account_id,
					sum(lo.debit) as debit,
					sum(lo.credit) as credit,
					null::integer as partner_id
					from (
						select distinct
							hpcl.id,
							prm.account_credit as account_id,
							'Provision de CTS a Pagar'::text as description,
							0 as analytic_account_id,
							0::numeric as debit,
							round(hpcl.provisiones_cts::numeric, 2) as credit
							from hr_provisiones_cts_line hpcl
							inner join hr_provisiones hpro ON hpro.id = hpcl.provision_id
							inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
							LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_CTS' and company_id = {company})
							where hpro.company_id = {company}
							and hpr.id = {payslip_run_id}
							and hpro.id = {provision_id}
						union all
						select distinct
							hpgl.id,
							prm.account_credit as account_id,
							'Provision de Gratificacion a Pagar'::text as description,
							0 as analytic_account_id,
							0::numeric as debit,
							round(hpgl.provisiones_grati::numeric, 2) as credit
							from hr_provisiones_grati_line hpgl
							inner join hr_provisiones hpro ON hpro.id = hpgl.provision_id
							inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
							LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_GRA' and company_id = {company})
							where hpro.company_id = {company}
							and hpr.id = {payslip_run_id}
							and hpro.id = {provision_id}
						union all
						select distinct
							hpgl.id,
							prm.account_credit as account_id,
							'Provision de Gratificacion a Pagar'::text as description,
							0 as analytic_account_id,
							0::numeric as debit,
							round(hpgl.boni_grati::numeric, 2) as credit
							from hr_provisiones_grati_line hpgl
							inner join hr_provisiones hpro ON hpro.id = hpgl.provision_id
							inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
							LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_GRA' and company_id = {company})
							where hpro.company_id = {company}
							and hpr.id = {payslip_run_id}
							and hpro.id = {provision_id}
						union all
						select distinct
							hpvl.id,
							prm.account_credit as account_id,
							'Provision de Vacaciones a Pagar'::text as description,
							0 as analytic_account_id,
							0::numeric as debit,
							round(hpvl.provisiones_vaca::numeric, 2) as credit
							from hr_provisiones_vaca_line hpvl
							inner join hr_provisiones hpro ON hpro.id = hpvl.provision_id
							inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
							LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_VAC' and company_id = {company})
							where hpro.company_id = {company}
							and hpr.id = {payslip_run_id}
							and hpro.id = {provision_id}
					) lo
					group by 
					lo.account_id,
					lo.description,
					lo.analytic_account_id
			""".format(
			company = self.company_id.id,
			payslip_run_id = self.payslip_run_id.id,
			provision_id = self.id)

		# CONSULTA PARA OBTENER LA CUENTA DE GASTO
		sql = """
			select T.account_id,
        	'Provision de CTS'::text as description,
        	T.analytic_account_id,
        	round(sum(T.debit)::numeric, 2) as debit,
        	0::numeric as credit,
        	null::integer as partner_id
        	from (
            	SELECT
                    hsrl.account_id AS account_id,
					hsrl.account_analityc as analytic_account_id,
					hpcl.provisiones_cts * (hadl.percent::numeric * 0.01) AS debit
				   FROM hr_provisiones_cts_line hpcl
					INNER JOIN hr_provisiones hpro ON hpro.id = hpcl.provision_id
					INNER JOIN hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
					inner join hr_contract hc on hc.id = hpcl.contract_id
					inner join hr_analytic_distribution had on had.id = hc.distribution_id
					inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
				    LEFT JOIN hr_salary_rule_line hsrl ON hpro.cts_sr_id = hsrl.salary_id AND hadl.analytic_id = hsrl.account_analityc
					where hpro.company_id = {company}
					and hpr.id = {payslip_run_id}
					and hpro.id = {provision_id}
				)T
			group by T.account_id,T.analytic_account_id
					
			union all 
			select T.account_id,
        	'Provision de Gratificacion'::text as description,
        	T.analytic_account_id,
        	round(sum(T.debit)::numeric, 2) as debit,
        	0::numeric as credit,
        	null::integer as partner_id
        	from (
            	SELECT
                    hsrl.account_id AS account_id,
					hsrl.account_analityc as analytic_account_id,
					hpgl.provisiones_grati * (hadl.percent::numeric * 0.01) AS debit
				   FROM hr_provisiones_grati_line hpgl
					INNER JOIN hr_provisiones hpro ON hpro.id = hpgl.provision_id
					INNER JOIN hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
					inner join hr_contract hc on hc.id = hpgl.contract_id
					inner join hr_analytic_distribution had on had.id = hc.distribution_id
					inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
				    LEFT JOIN hr_salary_rule_line hsrl ON hpro.gratification_sr_id = hsrl.salary_id AND hadl.analytic_id = hsrl.account_analityc
					where hpro.company_id = {company}
					and hpr.id = {payslip_run_id}
					and hpro.id = {provision_id}
				)T
			group by T.account_id,T.analytic_account_id
			
			union all 
			select T.account_id,
        	'Provision del Bono Extraordinario'::text as description,
        	T.analytic_account_id,
        	round(sum(T.debit)::numeric, 2) as debit,
        	0::numeric as credit,
        	null::integer as partner_id
        	from (
            	SELECT
                    hsrl.account_id AS account_id,
					hsrl.account_analityc as analytic_account_id,
					hpgl.boni_grati * (hadl.percent::numeric * 0.01) AS debit
				   FROM hr_provisiones_grati_line hpgl
					INNER JOIN hr_provisiones hpro ON hpro.id = hpgl.provision_id
					INNER JOIN hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
					inner join hr_contract hc on hc.id = hpgl.contract_id
					inner join hr_analytic_distribution had on had.id = hc.distribution_id
					inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
				    LEFT JOIN hr_salary_rule_line hsrl ON hpro.bonification_sr_id = hsrl.salary_id AND hadl.analytic_id = hsrl.account_analityc
					where hpro.company_id = {company}
					and hpr.id = {payslip_run_id}
					and hpro.id = {provision_id}
				)T
			group by T.account_id,T.analytic_account_id
			
			union all 
			select T.account_id,
        	'Provision de Vacaciones'::text as description,
        	T.analytic_account_id,
        	round(sum(T.debit)::numeric, 2) as debit,
        	0::numeric as credit,
        	null::integer as partner_id
        	from (
            	SELECT
                    hsrl.account_id AS account_id,
					hsrl.account_analityc as analytic_account_id,
					hpvl.provisiones_vaca * (hadl.percent::numeric * 0.01) AS debit
				   FROM hr_provisiones_vaca_line hpvl
					INNER JOIN hr_provisiones hpro ON hpro.id = hpvl.provision_id
					INNER JOIN hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
					inner join hr_contract hc on hc.id = hpvl.contract_id
					inner join hr_analytic_distribution had on had.id = hc.distribution_id
					inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
				    LEFT JOIN hr_salary_rule_line hsrl ON hpro.vacation_sr_id = hsrl.salary_id AND hadl.analytic_id = hsrl.account_analityc
					where hpro.company_id = {company}
					and hpr.id = {payslip_run_id}
					and hpro.id = {provision_id}
				)T
			group by T.account_id,T.analytic_account_id
			{sql_provision}
			""".format(
			company = self.company_id.id,
			payslip_run_id = self.payslip_run_id.id,
			provision_id = self.id,
			sql_provision = sql_provision
			)
		# print("sql",sql)
		self._cr.execute(sql)
		move_lines = self._cr.dictfetchall()
		return move_lines
