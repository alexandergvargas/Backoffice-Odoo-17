# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4,letter
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import simpleSplit
import decimal


class AccountReportRetentionTxtWizard(models.TransientModel):
	_name = 'account.report.retention.txt.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_id = fields.Many2one('account.period',string='Periodo',required=True)

	def get_sql(self):
		sql = """
			SELECT 
			rp.vat as ruc,
			rp.name as partner,
			rp.last_name as apellidop,
			rp.m_last_name as apellidom,
			rp.name_p as nombre,

			CASE
				WHEN split_part(arp.name, '-', 2) <> '' THEN split_part(arp.name, '-', 1)::character varying
				ELSE ''
			END
			AS serie_comp,
			CASE
				WHEN split_part(arp.name, '-', 2) <> '' THEN split_part(arp.name, '-', 2)::character varying
				ELSE split_part(arp.name, '-', 1)::character varying
			END
			AS numero_comp,
			CASE WHEN arp.date is not null THEN TO_CHAR(arp.date::DATE, 'dd/mm/yyyy') END as date,
			arp.amount as monto,
			lldt.code as td,
			CASE
				WHEN split_part(am.ref, '-', 2) <> '' THEN split_part(am.ref, '-', 1)::character varying
				ELSE ''
			END
			AS serie,
			CASE
				WHEN split_part(am.ref, '-', 2) <> '' THEN split_part(am.ref, '-', 2)::character varying
				ELSE split_part(am.ref, '-', 1)::character varying
			END
			AS numero,
			CASE WHEN am.invoice_date is not null THEN TO_CHAR(am.invoice_date::DATE, 'dd/mm/yyyy') END as invoice_date,
			arpl.debit
			FROM account_retention_comp_line arpl
			LEFT JOIN account_retention_comp arp on arp.id = arpl.main_id
			LEFT JOIN res_partner rp on rp.id = arp.partner_id
			LEFT JOIN account_move_line aml on aml.id = arpl.invoice_id
			LEFT JOIN account_move am on am.id = aml.move_id
			LEFT JOIN res_currency rc on rc.id = am.currency_id
			LEFT JOIN l10n_latam_document_type lldt ON lldt.id = am.l10n_latam_document_type_id
			LEFT JOIN multipayment_advance_it_line mail on mail.id = arpl.multipayment_line_id
			LEFT JOIN multipayment_advance_it mai on mai.id = mail.main_id
			LEFT JOIN account_main_parameter amp on amp.company_id = arp.company_id
			WHERE (arp.date between '{date_from}' and '{date_to}') and arp.company_id = {company_id}
			""".format(
				date_from = self.period_id.date_start.strftime('%Y/%m/%d'),
				date_to = self.period_id.date_end.strftime('%Y/%m/%d'),
				company_id = self.company_id.id
			)
		return sql
	
	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
	
	def get_report(self):
		if self.type_show == 'excel':
			return self.get_excel_report()
		elif self.type_show == 'pdf':
			return self.get_pdf_report()
		else:
			self.env.cr.execute("""
			CREATE OR REPLACE view account_retention_supplier_book as (SELECT row_number() OVER () AS id, T.* FROM ("""+self.get_sql()+""")T)""")
			if self.type_show == 'pantalla':
				return {
					'name': 'Retenciones',
					'type': 'ir.actions.act_window',
					'res_model': 'account.retention.supplier.book',
					'view_mode': 'tree',
					'view_type': 'form',
					'views': [(False, 'tree')],
				}

	def get_txt(self):
		ruc = self.company_id.partner_id.vat
		mond = self.company_id.currency_id.name

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		if not mond:
			raise UserError('No configuro la moneda de su Compañia.')

		name_doc = "0626"+ruc+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month)) + ".txt"
		sql_ple = self.get_sql()
		ReportBase = self.env['report.base']
		res = ReportBase.get_file_sql_export(sql_ple,'|')
	
		return self.env['popup.it'].get_file(name_doc,res if res else base64.encodebytes(b"== Sin Registros =="))