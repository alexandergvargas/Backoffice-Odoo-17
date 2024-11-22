# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class InvoicesWithDifferentRateWizard(models.TransientModel):
	_name = 'invoices.with.different.rate.wizard'

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_from_id = fields.Many2one('account.period',string='Periodo Inicial')
	period_to_id = fields.Many2one('account.period',string='Periodo Final')
	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en',default='pantalla', required=True)
	invoice_type = fields.Selection([('out','Cliente'),('in','Proveedor')],string=u'Tipo',default='out', required=True)

	def _get_sql(self):
		usd = self.env.ref('base.USD')
		sql = """
		select am2.date as fecha,
		aj.code as libro,
		rp.name as partner,
		l10n.code as td,
		am2.nro_comp as nro_comprobante,
		am2.amount_total as amount
		from (select  am.id as move_id from account_move am
		LEFT JOIN (SELECT DISTINCT ON (name) name,currency_id, rate, sale_type FROM res_currency_rate where currency_id = {usd}
		ORDER BY name) rc on rc.name = am.invoice_date
		where  am.date between '{date_from}' and '{date_to}' and am.company_id = {company_id}
		and am.move_type in ('{type}_invoice','{type}_refund'))T
		left join account_move am2 on am2.id = T.move_id
		LEFT JOIN account_journal aj ON aj.id = am2.journal_id
		LEFT JOIN res_partner rp ON rp.id = am2.partner_id
		LEFT JOIN l10n_latam_document_type l10n ON l10n.id = am2.l10n_latam_document_type_id
		LEFT JOIN res_currency rc ON rc.id = am.currency_id
		WHERE rc.name = 'USD'
		""".format(
			type = self.invoice_type,
			usd = usd.id,
			company_id = self.company_id.id,
			date_from = self.period_from_id.date_start.strftime('%Y/%m/%d'),
			date_to = self.period_to_id.date_end.strftime('%Y/%m/%d'))
		return sql

	def get_report(self):
		
		if self.type_show == 'pantalla':
			self.env.cr.execute("""
			DROP VIEW IF EXISTS invoices_with_different_rate_view;
			CREATE OR REPLACE view invoices_with_different_rate_view as (SELECT row_number() OVER () AS id, T2.* FROM ("""+self._get_sql()+""")T2)""")

			return {
				'name': 'Facturas con diferente Tipo de Cambio',
				'type': 'ir.actions.act_window',
				'res_model': 'invoices.with.different.rate.view',
				'view_mode': 'tree',
				'view_type': 'form',
			}

		if self.type_show == 'excel':
			return self.get_excel()


	def get_excel(self):
		ReportBase = self.env['report.base']
		workbook = ReportBase.get_excel_sql_export(self._get_sql(),self.get_header())
		return self.env['popup.it'].get_file('Facturas con diferente Tipo de Cambio.xlsx',workbook)

	def get_header(self):
		HEADERS = ['FECHA','LIBRO','PARTNER','TD','NRO COMP','MONTO']
		return HEADERS