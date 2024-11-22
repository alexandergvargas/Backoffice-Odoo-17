# -*- coding: utf-8 -*-
from psycopg2 import sql
from odoo import api, tools, fields, models


class TimesheetsAnalysisReport(models.Model):
    _inherit = "timesheets.analysis.report"

    crm_id = fields.Many2one("crm.lead", string="Oportunidad", readonly=True)

    @api.model
    def _select(self):
        return """
               SELECT
                   A.id AS id,
                   A.name AS name,
                   A.user_id AS user_id,
                   A.crm_id AS crm_id,
                   A.project_id AS project_id,
                   A.task_id AS task_id,
                   A.parent_task_id AS parent_task_id,
                   A.employee_id AS employee_id,
                   A.manager_id AS manager_id,
                   A.company_id AS company_id,
                   A.department_id AS department_id,
                   A.currency_id AS currency_id,
                   A.date AS date,
                   A.amount AS amount,
                   A.unit_amount AS unit_amount
           """

    @api.model
    def _where(self):
        return "WHERE A.project_id IS NOT NULL or A.crm_id IS NOT NULL"
