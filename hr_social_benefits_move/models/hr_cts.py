# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *

class HrCts(models.Model):
	_inherit = 'hr.cts'

	account_move_id = fields.Many2one('account.move', string='Asiento Contable', readonly=True)

	def action_open_asiento(self):
		self.ensure_one()
		return {
			"type": "ir.actions.act_window",
			"res_model": "account.move",
			"views": [[False, "tree"], [False, "form"]],
			"domain": [['id', '=', self.account_move_id.id]],
			"name": "Asiento de CTS",
		}

	def compute_provision_cts(self):
		# HISTORICO CTS
		year = int(self.fiscal_year_id.name)
		if self.type == '11':
			date_from_cts = datetime.strptime('01/05/%d' % year, '%d/%m/%Y').date()
			date_to_cts = datetime.strptime('31/10/%d' % year, '%d/%m/%Y').date()
		if self.type == '05':
			date_from_cts = datetime.strptime('01/11/%d' % (year - 1), '%d/%m/%Y').date()
			date_to_cts = datetime.strptime('30/04/%d' % year, '%d/%m/%Y').date()

		sql_cts = """
	select
		he.id as employee_id,
	--    hpr.date_start,
		'Provision de CTS'::text as description,
		sum(round(hpcl.provisiones_cts::numeric, 2)) as amount
	from hr_provisiones_cts_line hpcl
			 inner join hr_provisiones hpro ON hpro.id = hpcl.provision_id
			 inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
			 left join hr_contract hc on hc.id = hpcl.contract_id
			 left join hr_employee he on he.id = hc.employee_id
	where hpro.company_id = {company}
	  and hpr.date_start between '{date_from}' and '{date_to}'
	--   and he.id = 421
	group by
		he.id
		""".format(
			date_from=date_from_cts,
			date_to=date_to_cts,
			company=self.company_id.id
		)
		# print(sql_cts)
		self._cr.execute(sql_cts)
		data_cts = self._cr.dictfetchall()

		for record in self.line_ids:
			for prov_cts in data_cts:
				if record.employee_id.id == prov_cts['employee_id']:
					record.prov_acumulado = prov_cts['amount']
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
				 hcl.id,
				 {cts_haber} as account_id,
				 'Provision de CTS'::text as description,
				 round(hcl.prov_acumulado::numeric, 2) as debit,
				 he.user_partner_id as partner_id
			 from hr_cts_line hcl
	                  inner join hr_cts hcts ON hcts.id = hcl.cts_id
	                  left join hr_contract hc on hc.id = hcl.contract_id
	                  left join hr_employee he on he.id = hc.employee_id
	         where hcts.company_id = {company}
	           and hcts.id = {cts_id}
	           and hcl.prov_acumulado is not null
	     ) lo
	group by
	    lo.account_id,
	    lo.description,
	    lo.partner_id

	union all
	select T.account_id,
	       T.description,
	       T.analytic_account_id,
	       CASE WHEN sum(T.monto_cts) > 0 THEN round(sum(T.monto_cts)::numeric, 2) ELSE 0 END AS debit,
	       CASE WHEN sum(T.monto_cts) > 0 THEN 0 ELSE round(abs(sum(T.monto_cts))::numeric, 2) END AS credit,
	       null::integer as partner_id
	from (
	         SELECT distinct
				 prm.account_debit AS account_id,
				 hc.id as contract_id,
	             prm.description as description,
	             hadl.analytic_id as analytic_account_id,
	             (hcl.total_cts - coalesce(hcl.prov_acumulado,0)) * (hadl.percent::numeric * 0.01) AS monto_cts
	         FROM hr_cts_line hcl
	                  inner join hr_cts hcts ON hcts.id = hcl.cts_id
	                  inner join hr_contract hc on hc.id = hcl.contract_id
	                  inner join hr_analytic_distribution had on had.id = hc.distribution_id
	                  inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
	                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='CTS' and company_id = {company})
	         where hcts.company_id = {company}
	           and hcts.id = {cts_id}
	     )T
	where T.monto_cts <> 0
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
	             hcl.id,
	             prm.account_credit as account_id,
	             'CTS a Pagar'::text as description,
	             round(hcl.cts_soles::numeric, 2) as credit,
	             he.user_partner_id as partner_id
	         from hr_cts_line hcl
	                  inner join hr_cts hcts ON hcts.id = hcl.cts_id
	                  left join hr_contract hc on hc.id = hcl.contract_id
	                  left join hr_employee he on he.id = hc.employee_id
	                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_CTS' and company_id = {company})
	         where hcts.company_id = {company}
	           and hcts.id = {cts_id}
	           and hcl.cts_soles is not null
	         union all
	         select distinct
	             hcl.id,
	             prm.account_credit as account_id,
	             'Descuento por Adelantos'::text as description,
	             round(hcl.advance_amount::numeric, 2) as credit,
	             he.user_partner_id as partner_id
	         from hr_cts_line hcl
	                  inner join hr_cts hcts ON hcts.id = hcl.cts_id
	                  left join hr_contract hc on hc.id = hcl.contract_id
	                  left join hr_employee he on he.id = hc.employee_id
	                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADELANTO' and company_id = {company})
	         where hcts.company_id = {company}
	           and hcts.id = {cts_id}
	           and hcl.advance_amount is not null
	         union all
	         select distinct
	             hcl.id,
	             prm.account_credit as account_id,
	             'Descuento por Prestamos'::text as description,
	             round(hcl.loan_amount::numeric, 2) as credit,
	             he.user_partner_id as partner_id
	         from hr_cts_line hcl
	                  inner join hr_cts hcts ON hcts.id = hcl.cts_id
	                  left join hr_contract hc on hc.id = hcl.contract_id
	                  left join hr_employee he on he.id = hc.employee_id
	                  LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='PREST' and company_id = {company})
	         where hcts.company_id = {company}
	           and hcts.id = {cts_id}
	           and hcl.loan_amount is not null
	         --union all
	         --select distinct
	         --    hcl.id,
	         --    prm.account_credit as account_id,
	         --    'Descuento Retencion Judicial'::text as description,
	         --    round(hcl.ret_jud_amount::numeric, 2) as credit,
	         --    he.user_partner_id as partner_id
	         --from hr_cts_line hcl
	         --         inner join hr_cts hcts ON hcts.id = hcl.cts_id
	         --         left join hr_contract hc on hc.id = hcl.contract_id
	         --         left join hr_employee he on he.id = hc.employee_id
	         --         LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='RET_JUD' and company_id = {company})
	         --where hcts.company_id = {company}
	         --  and hcts.id = {cts_id}
	         --  and hcl.ret_jud_amount is not null
	     ) lo
	where lo.credit <> 0
	group by
	    lo.account_id,
	    lo.description,
	    lo.partner_id
							""".format(
			cts_haber= MainParameter.cts_haber.id,
			cts_id=self.id,
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
			'res_model': 'hr.cts.move.wizard',
			'views': [(self.env.ref('hr_social_benefits_move.hr_cts_move_wizard_form').id, 'form')],
			'context': {'default_credit': total_credit,
						'default_debit': total_debit,
						'cts_id': self.id,
						'move_lines': move_lines},
			'target': 'new'
		}

class HrCtsLine(models.Model):
	_inherit = 'hr.cts.line'

	prov_acumulado = fields.Float(string='Prov Acum')