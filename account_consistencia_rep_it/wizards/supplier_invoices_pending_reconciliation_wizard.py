# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class SupplierInvoicesPendingReconciliationWizard(models.TransientModel):
	_name = 'supplier.invoices.pending.reconciliation.wizard'

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period_from_id = fields.Many2one('account.period',string='Periodo Inicial')
	period_to_id = fields.Many2one('account.period',string='Periodo Final')
	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en',default='pantalla', required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def _get_sql(self):

		sql = """
		select am2.date as fecha,
		aj.code as libro,
		rp.name as partner,
		l10n.code as td,
		am2.nro_comp as nro_comprobante,
		am2.amount_total as amount
		from (
		
		select gs.move_id from get_saldos('{date_from}','{date_to}',{company_id}) gs
		left join account_move am on am.id = gs.move_id
		where (case when gs.moneda <> 'PEN' then am.amount_residual else abs(am.amount_residual_signed) end) <> (case when gs.moneda <> 'PEN' then gs.saldo_me else abs(gs.saldo_mn) end)
		and am.move_type in ('in_invoice','in_refund')
		)T
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
			DROP VIEW IF EXISTS invoices_pending_reconciliation_view;
			CREATE OR REPLACE view invoices_pending_reconciliation_view as (SELECT row_number() OVER () AS id, T2.* FROM ("""+self._get_sql()+""")T2)""")

			return {
				'name': 'Facturas de Proveedor pendientes de conciliar',
				'type': 'ir.actions.act_window',
				'res_model': 'invoices.pending.reconciliation.view',
				'view_mode': 'tree',
				'view_type': 'form',
			}

		if self.type_show == 'excel':
			return self.get_excel()


	def get_excel(self):
		ReportBase = self.env['report.base']
		workbook = ReportBase.get_excel_sql_export(self._get_sql(),self.get_header())
		return self.env['popup.it'].get_file('Facturas de Proveedor pendientes de conciliar.xlsx',workbook)

	def get_header(self):
		HEADERS = ['FECHA','LIBRO','PARTNER','TD','NRO COMP','MONTO']
		return HEADERS