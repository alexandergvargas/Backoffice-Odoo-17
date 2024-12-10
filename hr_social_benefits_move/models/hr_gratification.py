# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *

class HrGratification(models.Model):
	_inherit = 'hr.gratification'

	account_move_id = fields.Many2one('account.move', string='Asiento Contable', readonly=True)

	def action_open_asiento(self):
		self.ensure_one()
		return {
			"type": "ir.actions.act_window",
			"res_model": "account.move",
			"views": [[False, "tree"], [False, "form"]],
			"domain": [['id', '=', self.account_move_id.id]],
			"name": "Asiento de Gratificaciones",
		}

	def compute_provision_grati(self):
		# HISTORICO GRATIFICACION
		year = int(self.fiscal_year_id.name)
		if self.type == '07':
			date_from_grat = datetime.strptime('01/01/%d' % year, '%d/%m/%Y').date()
			date_to_grat = datetime.strptime('30/06/%d' % year, '%d/%m/%Y').date()
		if self.type == '12':
			date_from_grat = datetime.strptime('01/07/%d' % year, '%d/%m/%Y').date()
			date_to_grat = datetime.strptime('31/12/%d' % year, '%d/%m/%Y').date()

		sql_grat = """
			select
				he.id as employee_id,
			--    hpr.date_start,
				'Provision de Gratificacion'::text as description,
				sum(round((hpgl.provisiones_grati + hpgl.boni_grati)::numeric, 2)) as amount
			from hr_provisiones_grati_line hpgl
					 inner join hr_provisiones hpro ON hpro.id = hpgl.provision_id
					 inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
					 left join hr_contract hc on hc.id = hpgl.contract_id
					 left join hr_employee he on he.id = hc.employee_id
			where hpro.company_id = {company}
			  and hpr.date_start between '{date_from}' and '{date_to}'
			--   and he.id = 421
			group by
				he.id
				""".format(
			date_from=date_from_grat,
			date_to=date_to_grat,
			company=self.company_id.id
		)
		self._cr.execute(sql_grat)
		data_grat = self._cr.dictfetchall()

		for record in self.line_ids:
			for prov_grat in data_grat:
				if record.employee_id.id == prov_grat['employee_id']:
					record.prov_acumulado = prov_grat['amount']

		return self.env['popup.it'].get_message('Se obtuvo el acumulado de provisiones de manera correcta')

	def get_move_lines(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		sql = """
select
    lo.account_id,
    lo.description,
    null::integer as analytic_account_id,
    sum(lo.debit) as debit,
    0::numeric as credit,
    lo.partner_id
from (
         select distinct
             hgl.id,
             {grati_haber} as account_id,
             'Provision de Gratificacion'::text as description,
             round(hgl.prov_acumulado::numeric, 2) as debit,
             he.user_partner_id as partner_id
         from hr_gratification_line hgl
                  inner join hr_gratification hg ON hg.id = hgl.gratification_id
                  left join hr_contract hc on hc.id = hgl.contract_id
                  left join hr_employee he on he.id = hc.employee_id
         where hg.company_id = {company}
           and hg.id = {gratification_id}
           and hgl.prov_acumulado is not null
     ) lo
group by
    lo.account_id,
    lo.description,
    lo.partner_id

union all
	select T.account_id,
	       T.description,
	       T.analytic_account_id,
	       CASE WHEN sum(T.monto_grat) > 0 THEN round(sum(T.monto_grat)::numeric, 2) ELSE 0 END AS debit,
	       CASE WHEN sum(T.monto_grat) > 0 THEN 0 ELSE round(abs(sum(T.monto_grat))::numeric, 2) END AS credit,
	       null::integer as partner_id
	from (
	         SELECT distinct
				 prm.account_debit AS account_id,
				 hc.id as contract_id,
	             prm.description as description,
	             hadl.analytic_id as analytic_account_id,
	             (hgl.total - coalesce(hgl.prov_acumulado,0)) * (hadl.percent::numeric * 0.01) AS monto_grat
	         FROM hr_gratification_line hgl
	              inner join hr_gratification hg ON hg.id = hgl.gratification_id
                  inner join hr_contract hc on hc.id = hgl.contract_id
                  inner join hr_employee he on he.id = hc.employee_id
                  inner join hr_analytic_distribution had on had.id = hc.distribution_id
                  inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='GRA' and company_id = {company})
	         where hg.company_id = {company}
               and hg.id = {gratification_id}
	     )T
	where T.monto_grat <> 0
	group by T.account_id,T.description, T.analytic_account_id

union all
select
    lo.account_id,
    lo.description,
    null::integer as analytic_account_id,
    0::numeric as debit,
    sum(lo.credit) as credit,
    lo.partner_id
from (
         select distinct
             hgl.id,
             prm.account_credit as account_id,
             'Gratificacion a Pagar'::text as description,
             round(hgl.total::numeric, 2) as credit,
             he.user_partner_id as partner_id
         from hr_gratification_line hgl
                  inner join hr_gratification hg ON hg.id = hgl.gratification_id
                  left join hr_contract hc on hc.id = hgl.contract_id
                  left join hr_employee he on he.id = hc.employee_id
                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_GRA' and company_id = {company})
         where hg.company_id = {company}
           and hg.id = {gratification_id}
           and hgl.total is not null
         
         union all
         select distinct
             hgl.id,
             prm.account_credit as account_id,
             'Descuento por Adelantos'::text as description,
             round(hgl.advance_amount::numeric, 2) as credit,
             he.user_partner_id as partner_id
         from hr_gratification_line hgl
                  inner join hr_gratification hg ON hg.id = hgl.gratification_id
                  left join hr_contract hc on hc.id = hgl.contract_id
                  left join hr_employee he on he.id = hc.employee_id
                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADELANTO' and company_id = {company})
         where hg.company_id = {company}
           and hg.id = {gratification_id}
           and hgl.advance_amount is not null
         
         union all
         select distinct
             hgl.id,
             prm.account_credit as account_id,
             'Descuento por Prestamos'::text as description,
             round(hgl.loan_amount::numeric, 2) as credit,
             he.user_partner_id as partner_id
         from hr_gratification_line hgl
                  inner join hr_gratification hg ON hg.id = hgl.gratification_id
                  left join hr_contract hc on hc.id = hgl.contract_id
                  left join hr_employee he on he.id = hc.employee_id
                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='PREST' and company_id = {company})
         where hg.company_id = {company}
           and hg.id = {gratification_id}
           and hgl.loan_amount is not null
           
         --union all
         --select distinct
         --    hgl.id,
         --    prm.account_credit as account_id,
         --    'Descuento Retencion Judicial'::text as description,
         --    round(hgl.ret_jud_amount::numeric, 2) as credit,
         --    he.user_partner_id as partner_id
         --from hr_gratification_line hgl
         --         inner join hr_gratification hg ON hg.id = hgl.gratification_id
         --         left join hr_contract hc on hc.id = hgl.contract_id
         --         left join hr_employee he on he.id = hc.employee_id
         --         LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='RET_JUD' and company_id = {company})
         --where hg.company_id = {company}
         --  and hg.id = {gratification_id}
         --  and hgl.ret_jud_amount is not null
     ) lo
where lo.credit <> 0
group by
    lo.account_id,
    lo.description,
    lo.partner_id
						""".format(
			grati_haber=MainParameter.grati_haber.id,
			gratification_id=self.id,
			company=self.company_id.id
		)
		self._cr.execute(sql)
		move_lines = self._cr.dictfetchall()
		# print("move_lines",move_lines)
		return move_lines


	def get_move_wizard(self):
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		if self.account_move_id:
			raise UserError('Elimine el Asiento Actual para generar uno nuevo')
		move_lines = self.get_move_lines()
		total_debit = total_credit = 0
		for line in move_lines:
			total_debit += line['debit']
			total_credit += line['credit']
		return {
			'name': 'Generar Asiento Contable',
			'type': 'ir.actions.act_window',
			'res_model': 'hr.gratification.move.wizard',
			'views': [(self.env.ref('hr_social_benefits_move.hr_gratification_move_wizard_form').id, 'form')],
			'context': {'default_credit': total_credit,
						'default_debit': total_debit,
						'gratification_id': self.id,
						'move_lines': move_lines},
			'target': 'new'
		}

class HrGratificationLine(models.Model):
	_inherit = 'hr.gratification.line'

	prov_acumulado = fields.Float(string='Prov Acum')