# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import *
from calendar import *
from dateutil.relativedelta import relativedelta
import base64

class HrLiquidation(models.Model):
    _inherit = 'hr.liquidation'

    liq_move_ids = fields.One2many('hr.liquidation.move', 'liquidation_id',string='Asientos Contables')
    move_count = fields.Integer(compute='_compute_move_count')

    def _compute_move_count(self):
        for move in self:
            move.move_count = len(move.liq_move_ids.filtered(lambda line: line.preserve_record).account_move_id.ids)

    def action_open_asiento(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.liq_move_ids.filtered(lambda line: line.preserve_record).account_move_id.ids]],
            "name": "Asiento de Liquidacion",
        }

    def get_liq_move_lines(self):
        MonthLot = self.payslip_run_id
        Employees = MonthLot.slip_ids.filtered(lambda slip: slip.contract_id.labor_regime in ['general', 'small', 'micro'] and
                                                            slip.contract_id.situation_id.code == '0' and
                                                            slip.date_from <= slip.contract_id.date_end and
                                                            slip.date_to >= slip.contract_id.date_end).mapped('employee_id')
        self.employee_ids = [(6, 0, Employees.ids)]

        for Employee in Employees:
            Contract = MonthLot.mapped('slip_ids').filtered(lambda slip: slip.employee_id == Employee).contract_id
            admission_date = self.env['hr.contract'].get_first_contract(Employee, Contract).date_start
            vals = {'liquidation_id': self.id,
                    'employee_id': Employee.id,
                    'contract_id': Contract.id,
                    'admission_date': admission_date,
                    'cessation_date': Contract.date_end}
            self.env['hr.liquidation.move'].create(vals)

    def get_liquidation(self):
        super(HrLiquidation,self).get_liquidation()
        self.env['hr.liquidation.move'].search([('liquidation_id','=',self.id),('preserve_record','=',False)]).unlink()
        self.get_liq_move_lines()

        preservados = self.env['hr.liquidation.move'].search([('liquidation_id', '=', self.id), ('preserve_record', '=', True)])
        empleados_pre = []
        for j in preservados:
            if j.employee_id.id not in empleados_pre:
                empleados_pre.append(j.employee_id.id)
        eliminar = []
        for l in self.liq_move_ids:
            if l.employee_id.id in empleados_pre:
                if l.preserve_record == False:
                    eliminar.append(l)
        for l in eliminar:
            l.unlink()
        return self.env['popup.it'].get_message('Se calculo exitosamente')

    def compute_provision_liqui(self):
        # HISTORICO CTS
        for line_cts in self.cts_line_ids:
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
          and he.id = {employee_id}
        group by
            he.id
            """.format(
                date_from=line_cts.compute_date,
                date_to=line_cts.cessation_date,
                employee_id=line_cts.employee_id.id,
                company=self.company_id.id
            )
            # print(sql_cts)
            self._cr.execute(sql_cts)
            data_cts = self._cr.dictfetchall()

            for prov_cts in data_cts:
                if line_cts.employee_id.id == prov_cts['employee_id']:
                    line_cts.prov_acumulado = prov_cts['amount']

        # HISTORICO GRATIFICACION
        for line_grati in self.gratification_line_ids:
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
          and he.id = {employee_id}
        group by
            he.id
            """.format(
                date_from=line_grati.compute_date,
                date_to=line_grati.cessation_date,
                employee_id=line_grati.employee_id.id,
                company=self.company_id.id
            )
            self._cr.execute(sql_grat)
            data_grat = self._cr.dictfetchall()

            for prov_grat in data_grat:
                if line_grati.employee_id.id == prov_grat['employee_id']:
                    line_grati.prov_acumulado = prov_grat['amount']

        # HISTORICO VACACIONES
        for line_vaca in self.vacation_line_ids:
            sql_vac = """
        select
        	he.id as employee_id,
        --    hpr.date_start,
        	'Provision de Vacaciones'::text as description,
        	sum(round(hpvl.provisiones_vaca::numeric, 2)) as amount
        from hr_provisiones_vaca_line hpvl
        		 inner join hr_provisiones hpro ON hpro.id = hpvl.provision_id
        		 inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
        		 left join hr_contract hc on hc.id = hpvl.contract_id
        		 left join hr_employee he on he.id = hc.employee_id
        where hpro.company_id = {company}
          and hpr.date_start between '{date_from}' and '{date_to}'
          and he.id = {employee_id}
        group by
        	he.id
        	""".format(
                date_from=line_vaca.compute_date,
                date_to=line_vaca.cessation_date,
                employee_id=line_vaca.employee_id.id,
                company=self.company_id.id
            )
            self._cr.execute(sql_vac)
            data_vac = self._cr.dictfetchall()

            for prov_vac in data_vac:
                if line_vaca.employee_id.id == prov_vac['employee_id']:
                    line_vaca.prov_acumulado = prov_vac['amount']

        return self.env['popup.it'].get_message('Se obtuvo el acumulado de provisiones de manera correcta')

class HrLiquidationMove(models.Model):
    _name = 'hr.liquidation.move'
    _description = 'Hr Liquidation Move'

    liquidation_id = fields.Many2one('hr.liquidation', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    contract_id = fields.Many2one('hr.contract', string='Contrato')
    identification_id = fields.Char(related='employee_id.identification_id', string='Nro Documento')
    admission_date = fields.Date(string='Fecha de Ingreso')
    cessation_date = fields.Date(string='Fecha de Cese')
    account_move_id = fields.Many2one('account.move', string='Asiento Contable', readonly=True)

    preserve_record = fields.Boolean('No Recalcular')

    def get_move_lines(self):
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
             prm.account_credit as account_id,
             'Provision de CTS'::text as description,
             round(hcl.prov_acumulado::numeric, 2) as debit,
             he.user_partner_id as partner_id
         from hr_cts_line hcl
            inner join hr_liquidation hl ON hl.id = hcl.liquidation_id
            left join hr_contract hc on hc.id = hcl.contract_id
            left join hr_employee he on he.id = hc.employee_id
            LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_CTS' and company_id = {company_id})
                where hl.company_id = {company_id}
                  and hl.id = {liquidation_id}
                  and hcl.employee_id = {employee_id}
                  and hcl.prov_acumulado is not null
                  and hcl.prov_acumulado <> 0
         
         union all
         select distinct
             hgl.id,
             prm.account_credit as account_id,
             'Provision de Gratificacion'::text as description,
             round(hgl.prov_acumulado::numeric, 2) as debit,
             he.user_partner_id as partner_id
         from hr_gratification_line hgl
            inner join hr_liquidation hl ON hl.id = hgl.liquidation_id
            left join hr_contract hc on hc.id = hgl.contract_id
            left join hr_employee he on he.id = hc.employee_id
            LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_GRA' and company_id = {company_id})
                where hl.company_id = {company_id}
                  and hl.id = {liquidation_id}
                  and hgl.employee_id = {employee_id}
                  and hgl.prov_acumulado is not null
                  and hgl.prov_acumulado <> 0
         
         union all
         select distinct
             hlvl.id,
             prm.account_credit as account_id,
             'Provision de Vacaciones'::text as description,
             round(hlvl.prov_acumulado::numeric, 2) as debit,
             he.user_partner_id as partner_id
         from hr_liquidation_vacation_line hlvl
            inner join hr_liquidation hl ON hl.id = hlvl.liquidation_id
            left join hr_contract hc on hc.id = hlvl.contract_id
            left join hr_employee he on he.id = hc.employee_id
            LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='ADE_VAC' and company_id = {company_id})
                where hl.company_id = {company_id}
                  and hl.id = {liquidation_id}
                  and hlvl.employee_id = {employee_id}
                  and hlvl.prov_acumulado is not null
                  and hlvl.prov_acumulado <> 0
     ) lo
group by
    lo.account_id,
    lo.description,
    lo.partner_id

union all
select T.account_id,
       T.description,
       T.analytic_account_id,
       CASE WHEN (T.monto_grat-coalesce(T.monto_prov,0)) > 0 THEN round((T.monto_grat-coalesce(T.monto_prov,0))::numeric, 2) ELSE 0 END AS debit,
       CASE WHEN (T.monto_grat-coalesce(T.monto_prov,0)) > 0 THEN 0 ELSE abs(round((T.monto_grat-coalesce(T.monto_prov,0))::numeric, 2)) END AS credit,
       null::integer as partner_id
from (
         SELECT
             hsrl.account_id AS account_id,
             hsr.name->>'en_US' as description,
             hsrl.account_analityc as analytic_account_id,
             hgl.total * (hadl.percent::numeric * 0.01) AS monto_grat,
             hgl.prov_acumulado * (hadl.percent::numeric * 0.01) as monto_prov
         FROM hr_gratification_line hgl
            inner join hr_liquidation hl ON hl.id = hgl.liquidation_id
            inner join hr_contract hc on hc.id = hgl.contract_id
            inner join hr_analytic_distribution had on had.id = hc.distribution_id
            inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
            LEFT JOIN hr_salary_rule_line hsrl ON (select id from hr_salary_rule where code='GRA_TRU' and company_id = {company_id}) = hsrl.salary_id
                                                        AND hadl.analytic_id = hsrl.account_analityc
            inner join hr_salary_rule hsr on hsr.id = hsrl.salary_id
         where hl.company_id = {company_id}
           and hl.id = {liquidation_id}
           and hgl.employee_id = {employee_id}
     )T
where (T.monto_grat-coalesce(T.monto_prov,0)) <> 0

union all
select T.account_id,
       T.description,
       T.analytic_account_id,
       CASE WHEN (T.monto_cts-coalesce(T.monto_prov,0)) > 0 THEN round((T.monto_cts-coalesce(T.monto_prov,0))::numeric, 2) ELSE 0 END AS debit,
       CASE WHEN (T.monto_cts-coalesce(T.monto_prov,0)) > 0 THEN 0 ELSE abs(round((T.monto_cts-coalesce(T.monto_prov,0))::numeric, 2)) END AS credit,
       null::integer as partner_id
from (
         SELECT
             hsrl.account_id AS account_id,
             hsr.name->>'en_US' as description,
             hsrl.account_analityc as analytic_account_id,
             hcl.total_cts * (hadl.percent::numeric * 0.01) AS monto_cts,
             hcl.prov_acumulado * (hadl.percent::numeric * 0.01) as monto_prov
         FROM hr_cts_line hcl
            inner join hr_liquidation hl ON hl.id = hcl.liquidation_id
            inner join hr_contract hc on hc.id = hcl.contract_id
            inner join hr_analytic_distribution had on had.id = hc.distribution_id
            inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
            LEFT JOIN hr_salary_rule_line hsrl ON (select id from hr_salary_rule where code='CTS_TRU' and company_id = {company_id}) = hsrl.salary_id
                                                        AND hadl.analytic_id = hsrl.account_analityc
            inner join hr_salary_rule hsr on hsr.id = hsrl.salary_id
        where hl.company_id = {company_id}
           and hl.id = {liquidation_id}
           and hcl.employee_id = {employee_id}
     )T
where (T.monto_cts-coalesce(T.monto_prov,0)) <> 0

union all
select T.account_id,
       T.description,
       T.analytic_account_id,
       CASE WHEN (T.monto_vaca-coalesce(T.monto_prov,0)) > 0 THEN round((T.monto_vaca-coalesce(T.monto_prov,0))::numeric, 2) ELSE 0 END AS debit,
       CASE WHEN (T.monto_vaca-coalesce(T.monto_prov,0)) > 0 THEN 0 ELSE abs(round((T.monto_vaca-coalesce(T.monto_prov,0))::numeric, 2)) END AS credit,
       null::integer as partner_id
from (
         SELECT
             hsrl.account_id AS account_id,
             hsr.name->>'en_US' as description,
             hsrl.account_analityc as analytic_account_id,
             hlvl.total_vacation * (hadl.percent::numeric * 0.01) AS monto_vaca,
             hlvl.prov_acumulado * (hadl.percent::numeric * 0.01) as monto_prov
         FROM hr_liquidation_vacation_line hlvl
            inner join hr_liquidation hl ON hl.id = hlvl.liquidation_id
            inner join hr_contract hc on hc.id = hlvl.contract_id
            inner join hr_analytic_distribution had on had.id = hc.distribution_id
            inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
            LEFT JOIN hr_salary_rule_line hsrl ON (select id from hr_salary_rule where code='VATRU' and company_id = {company_id}) = hsrl.salary_id
                                                        AND hadl.analytic_id = hsrl.account_analityc
            inner join hr_salary_rule hsr on hsr.id = hsrl.salary_id
         where hl.company_id = {company_id}
           and hl.id = {liquidation_id}
           and hlvl.employee_id = {employee_id}
     )T
where (T.monto_vaca-coalesce(T.monto_prov,0)) <> 0

union all
select
    lo.account_id,
    'Liquidaciones por Pagar'::text as description,
    null::integer as analytic_account_id,
    0::numeric as debit,
    coalesce(abs(round((lo.credit+lo.monto_otros)::numeric, 2)),0) as credit,
    lo.partner_id
from ( select T.account_id,
              sum(T.credit) as credit,
              T.partner_id,
              (select coalesce(hlec.income-hlec.expenses,0) as credit
               from hr_liquidation_extra_concepts hlec
                        inner join hr_liquidation hl ON hl.id = hlec.liquidation_id
               where hl.company_id = {company_id}
                 and hl.id = {liquidation_id}
                 and hlec.employee_id = {employee_id}) as monto_otros
       from (
                select distinct
                    hgl.id,
                    prm.account_credit as account_id,
                    round(hgl.total_grat::numeric, 2) as credit,
                    he.user_partner_id as partner_id
                from hr_gratification_line hgl
                         inner join hr_liquidation hl ON hl.id = hgl.liquidation_id
                         left join hr_contract hc on hc.id = hgl.contract_id
                         left join hr_employee he on he.id = hc.employee_id
                         LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='GRA_TRU' and company_id = {company_id})
                where hl.company_id = {company_id}
                  and hl.id = {liquidation_id}
                  and hgl.employee_id = {employee_id}
                  and hgl.total_grat is not null
                  and hgl.total_grat <> 0
                
                union all
                select distinct
                    hgl.id,
                    prm.account_credit as account_id,
                    round(hgl.bonus_essalud::numeric, 2) as credit,
                    he.user_partner_id as partner_id
                from hr_gratification_line hgl
                         inner join hr_liquidation hl ON hl.id = hgl.liquidation_id
                         left join hr_contract hc on hc.id = hgl.contract_id
                         left join hr_employee he on he.id = hc.employee_id
                         LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='BON9_TRU' and company_id = {company_id})
                where hl.company_id = {company_id}
                  and hl.id = {liquidation_id}
                  and hgl.employee_id = {employee_id}
                  and hgl.bonus_essalud is not null
                  and hgl.bonus_essalud <> 0
                
                union all
                select distinct
                    hcl.id,
                    prm.account_credit as account_id,
                    round(hcl.total_cts::numeric, 2) as credit,
                    he.user_partner_id as partner_id
                from hr_cts_line hcl
                         inner join hr_liquidation hl ON hl.id = hcl.liquidation_id
                         left join hr_contract hc on hc.id = hcl.contract_id
                         left join hr_employee he on he.id = hc.employee_id
                         LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='CTS_TRU' and company_id = {company_id})
                where hl.company_id = {company_id}
                  and hl.id = {liquidation_id}
                  and hcl.employee_id = {employee_id}
                  and hcl.total_cts is not null
                  and hcl.total_cts <> 0
                
                union all
                select distinct
                    hlvl.id,
                    prm.account_credit as account_id,
                    round(hlvl.total::numeric, 2) as credit,
                    he.user_partner_id as partner_id
                from hr_liquidation_vacation_line hlvl
                         inner join hr_liquidation hl ON hl.id = hlvl.liquidation_id
                         left join hr_contract hc on hc.id = hlvl.contract_id
                         left join hr_employee he on he.id = hc.employee_id
                         LEFT JOIN payslip_run_move prm ON prm.salary_rule_id = (select id from hr_salary_rule where code='VATRU' and company_id = {company_id})
                where hl.company_id = {company_id}
                  and hl.id = {liquidation_id}
                  and hlvl.employee_id = {employee_id}
                  and hlvl.total is not null
                  and hlvl.total <> 0
            )T
       group by
           T.account_id,
           T.partner_id
     ) lo
where coalesce(lo.credit+lo.monto_otros,0) <> 0

union all
select distinct
    hm.account_id,
    hm.name as description,
    null::integer as analytic_account_id,
    0::numeric as debit,
    round((hlvl.onp+hlvl.afp_jub+hlvl.afp_si+hlvl.afp_mixed_com+hlvl.afp_fixed_com)::numeric, 2) as credit,
    he.user_partner_id as partner_id
from hr_liquidation_vacation_line hlvl
         inner join hr_liquidation hl ON hl.id = hlvl.liquidation_id
         left join hr_contract hc on hc.id = hlvl.contract_id
         left join hr_employee he on he.id = hc.employee_id
         inner join hr_membership hm on hm.id = hc.membership_id
where hl.company_id = {company_id}
  and hl.id = {liquidation_id}
  and hlvl.employee_id = {employee_id}
  and (hlvl.onp+hlvl.afp_jub+hlvl.afp_si+hlvl.afp_mixed_com+hlvl.afp_fixed_com) <> 0

union all
select distinct
    CASE WHEN hecl.type= 'in' THEN hsrl.account_id ELSE prm.account_credit END AS account_id,
    hsr.name->>'en_US' as description,
    CASE WHEN hecl.type= 'in' THEN hsrl.account_analityc ELSE null::integer END AS analytic_account_id,
    CASE WHEN hecl.type= 'in' THEN round((hecl.amount * hadl.percent * 0.01)::numeric, 2) ELSE 0 END AS debit,
    CASE WHEN hecl.type= 'out' THEN round(hecl.amount::numeric, 2) ELSE 0 END AS credit,
    he.user_partner_id as partner_id
from hr_extra_concept_line hecl
         inner join hr_liquidation_extra_concepts hec on hec.id = hecl.extra_concept_id
         inner join hr_liquidation hl ON hl.id = hec.liquidation_id
         inner join hr_payslip_input_type hpit on hpit.id = hecl.name_input_id
         inner join hr_salary_rule hsr on hsr.code = hpit.code
         left JOIN payslip_run_move prm ON prm.salary_rule_id = hsr.id
         left join hr_employee he on he.id = hec.employee_id
         inner join hr_contract hc on hc.id = he.contract_id
         inner join hr_analytic_distribution had on had.id = hc.distribution_id
         inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
         LEFT JOIN hr_salary_rule_line hsrl on hsr.id = hsrl.salary_id AND hadl.analytic_id = hsrl.account_analityc
where hsr.company_id = {company_id}
  and hl.id = {liquidation_id}
  and hec.employee_id = {employee_id}
  and hecl.amount is not null
  and hecl.amount <> 0
						""".format(
            employee_id = self.employee_id.id,
            liquidation_id = self.liquidation_id.id,
            company_id = self.env.company.id
        )
        self._cr.execute(sql)
        move_lines = self._cr.dictfetchall()
        # print("move_lines",move_lines)
        return move_lines

    def get_liquidation_move_wizard(self):
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
            'res_model': 'hr.liquidation.move.wizard',
            'views': [(self.env.ref('hr_social_benefits_move_analytic.hr_liquidation_move_wizard_form').id, 'form')],
            'context': {'default_credit': total_credit,
                        'default_debit': total_debit,
                        'liqui_move_id': self.id,
                        'move_lines': move_lines},
            'target': 'new'
        }

class HrLiquidationVacationLine(models.Model):
    _inherit = 'hr.liquidation.vacation.line'

    prov_acumulado = fields.Float(string='Prov Acum')