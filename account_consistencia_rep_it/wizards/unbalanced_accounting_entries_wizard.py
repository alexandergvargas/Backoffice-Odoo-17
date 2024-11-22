# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class UnbalancedAccountingEntriesWizard(models.TransientModel):
	_name = 'unbalanced.accounting.entries.wizard'

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_from_id = fields.Many2one('account.period',string='Periodo Inicial')
	period_to_id = fields.Many2one('account.period',string='Periodo Final')
	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en',default='pantalla', required=True)

	def _get_sql(self):

		sql = """
		select am2.date as fecha,
		aj.code as libro,
		rp.name as partner,
		l10n.code as td,
		am2.nro_comp as nro_comprobante,
		T.debe,
		T.haber,
		T.diferencia
		from (select  aml.move_id,sum(aml.debit) as debe,sum(aml.credit) as haber,sum(aml.debit-aml.credit) as diferencia from account_move_line aml
		left join account_move am on am.id=aml.move_id
		where  am.date between '{date_from}' and '{date_to}' and am.company_id = {company_id}
		group by aml.move_id
		having sum(aml.debit-aml.credit)<>0)T
		left join account_move am2 on am2.id = T.move_id
		LEFT JOIN account_journal aj ON aj.id = am2.journal_id
		LEFT JOIN res_partner rp ON rp.id = am2.partner_id
		LEFT JOIN l10n_latam_document_type l10n ON l10n.id = am2.l10n_latam_document_type_id
		""".format(
			company_id = self.company_id.id,
			date_from = self.period_from_id.date_start.strftime('%Y/%m/%d'),
			date_to = self.period_to_id.date_end.strftime('%Y/%m/%d'))
		return sql

	def get_report(self):
		
		if self.type_show == 'pantalla':
			self.env.cr.execute("""
			DROP VIEW IF EXISTS unbalanced_accounting_entries_view;
			CREATE OR REPLACE view unbalanced_accounting_entries_view as (SELECT row_number() OVER () AS id, T2.* FROM ("""+self._get_sql()+""")T2)""")

			return {
				'name': 'Asientos Descuadrados',
				'type': 'ir.actions.act_window',
				'res_model': 'unbalanced.accounting.entries.view',
				'view_mode': 'tree',
				'view_type': 'form',
			}

		if self.type_show == 'excel':
			return self.get_excel()


	def get_excel(self):
		ReportBase = self.env['report.base']
		workbook = ReportBase.get_excel_sql_export(self._get_sql(),self.get_header())
		return self.env['popup.it'].get_file('Asientos Descuadrados.xlsx',workbook)

	def get_header(self):
		HEADERS = ['FECHA','LIBRO','PARTNER','TD','NRO COMP','DEBE','HABER','DIFERENCIA']
		return HEADERS