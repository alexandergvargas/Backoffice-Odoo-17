# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class AccountCtaCteReportWizard(models.TransientModel):
	_name = 'account.cta.cte.report.wizard'

	name = fields.Char()
	cta_cte_id = fields.Many2one('account.cta.cte',string='Cta Cte',required=True)
	type =  fields.Selection([('detail','Detallado'),('summary','Resumen')],string=u'Tipo',default='detail')

	def get_report(self):
		if self.type == 'detail':
			import io
			from xlsxwriter.workbook import Workbook
			ReportBase = self.env['report.base']
			direccion = self.env['account.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).dir_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

			workbook = Workbook(direccion + 'cta_cte_detail.xlsx')
			workbook, formats = ReportBase.get_formats(workbook)

			import importlib
			import sys
			importlib.reload(sys)

			worksheet = workbook.add_worksheet("Detalles")
			worksheet.set_tab_color('blue')
			
			self._cr.execute(self.get_sql_detail())
			data = self._cr.dictfetchall()
			HEADERS = ['PERIODO','FECHA','LIBRO','TDP','DOCUMENTO PARTNER','RAZON SOCIAL','TD','NRO COMP','FEC DOC','FEC VEN','CUENTA','MONEDA','DEBE','HABER','MONTO MONEDA','GLOSA','VENDEDOR','TIPO']
			worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
			debe, haber = 0, 0
			x = 1

			for line in data:
				worksheet.write(x,0,line['periodo'] if line['periodo'] else '',formats['especial1'])
				worksheet.write(x,1,line['fecha'] if line['fecha']  else '',formats['dateformat'])
				worksheet.write(x,2,line['libro'] if line['libro']  else '',formats['especial1'])
				worksheet.write(x,3,line['tdp'] if line['tdp'] else '',formats['especial1'])
				worksheet.write(x,4,line['docp'] if line['docp'] else '',formats['especial1'])
				worksheet.write(x,5,line['partner'] if line['partner'] else '',formats['especial1'])
				worksheet.write(x,6,line['td'] if line['td'] else '',formats['especial1'])
				worksheet.write(x,7,line['nro_comprobante'] if line['nro_comprobante'] else '',formats['especial1'])
				worksheet.write(x,8,line['fecha_doc'] if line['fecha_doc'] else '',formats['dateformat'])
				worksheet.write(x,9,line['fecha_ven'] if line['fecha_ven'] else '',formats['dateformat'])
				worksheet.write(x,10,line['cuenta'] if line['cuenta'] else '',formats['especial1'])
				worksheet.write(x,11,line['moneda'] if line['moneda'] else '',formats['especial1'])
				worksheet.write(x,12,line['debe'] if line['debe'] else 0,formats['numberdos'])
				worksheet.write(x,13,line['haber'] if line['haber'] else 0,formats['numberdos'])
				worksheet.write(x,14,line['monto_me'] if line['monto_me'] else 0,formats['numberdos'])
				worksheet.write(x,15,line['glosa'] if line['glosa'] else '',formats['especial1'])
				worksheet.write(x,16,line['vendedor'] if line['vendedor'] else '',formats['especial1'])
				worksheet.write(x,17,line['tipo'] if line['tipo'] else '',formats['especial1'])

				debe +=line['debe'] if line['debe'] else 0
				haber +=line['haber'] if line['haber'] else 0

				x += 1

			worksheet.write(x,12,debe,formats['numbertotal'])
			worksheet.write(x,13,haber,formats['numbertotal'])

			widths = [10,10,7,5,24,55,3,13,10,10,11,10,13,13,18,40,25,6]
			worksheet = ReportBase.resize_cells(worksheet,widths)
			workbook.close()
			f = open(direccion +'cta_cte_detail.xlsx', 'rb')
			return self.env['popup.it'].get_file('Cuentas Corrientes %s Detallado.xlsx'%(self.cta_cte_id.name),base64.encodebytes(b''.join(f.readlines())))

		else:
			import io
			from xlsxwriter.workbook import Workbook
			ReportBase = self.env['report.base']
			direccion = self.env['account.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).dir_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

			workbook = Workbook(direccion + 'cta_cte_summary.xlsx')
			workbook, formats = ReportBase.get_formats(workbook)

			import importlib
			import sys
			importlib.reload(sys)

			worksheet = workbook.add_worksheet("Resumen")
			worksheet.set_tab_color('blue')
			
			self._cr.execute(self.get_sql_summary())
			data = self._cr.dictfetchall()
			HEADERS = ['CUENTA',u'DESCRIPCIÓN','MONEDA','SALDO MN','SALDO ME']
			worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
			saldo_mn, saldo_me = 0, 0
			x = 1

			for line in data:
				worksheet.write(x,0,line['cuenta'] if line['cuenta'] else '',formats['especial1'])
				worksheet.write(x,1,line['nomen'] if line['nomen'] else '',formats['especial1'])
				worksheet.write(x,2,line['moneda'] if line['moneda'] else '',formats['especial1'])
				worksheet.write(x,3,line['saldo_mn'] if line['saldo_mn'] else 0,formats['numberdos'])
				worksheet.write(x,4,line['saldo_me'] if line['saldo_me'] else 0,formats['numberdos'])

				saldo_mn +=line['saldo_mn'] if line['saldo_mn'] else 0
				saldo_me +=line['saldo_me'] if line['saldo_me'] else 0

				x += 1

			worksheet.write(x,3,saldo_mn,formats['numbertotal'])
			worksheet.write(x,4,saldo_me,formats['numbertotal'])

			widths = [13,80,10,15,15]
			worksheet = ReportBase.resize_cells(worksheet,widths)
			workbook.close()
			f = open(direccion +'cta_cte_summary.xlsx', 'rb')
			return self.env['popup.it'].get_file('Cuentas Corrientes %s Resumen.xlsx'%(self.cta_cte_id.name),base64.encodebytes(b''.join(f.readlines())))
		
	def get_sql_detail(self):
		sql = """
			SELECT 
			periodo_de_fecha(m.date,(m.type_register = 'origin')::boolean)::character varying as periodo,
			m.date as fecha,
			aj.code as libro,
			lit.l10n_pe_vat_code AS tdp,
			rp.vat AS docp,
			rp.name as partner,
			ec1.code AS td,
			l.nro_comp as nro_comprobante,
			l.invoice_date as fecha_doc,
			l.date_maturity as fecha_ven,
			aa.code as cuenta,
			rc.name as moneda,
			l.debit as debe,
			l.credit as haber,
			l.amount_currency as monto_me,
			l.glosa,
			rpu.name as vendedor,
			case when m.type_register = 'origin' then 'Origen' else 'Ajuste' end as tipo
			from account_cta_cte_si l
			LEFT JOIN account_cta_cte m on m.id = l.main_id
			LEFT JOIN account_journal aj on aj.id = l.journal_id
			LEFT JOIN res_partner rp ON rp.id = l.partner_id
			LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
			LEFT JOIN l10n_latam_document_type ec1 ON ec1.id = l.type_document_id
			LEFT JOIN account_account aa ON aa.id = l.account_id
			LEFT JOIN res_currency rc ON rc.id = l.currency_id
			LEFT JOIN res_users ru on ru.id = l.invoice_user_id
			LEFT JOIN res_partner rpu on rpu.id = ru.partner_id
			where l.main_id = %d
			"""%(self.cta_cte_id.id)
		return sql
	
	def get_sql_summary(self):
		sql = """
			SELECT 
			aa.code as cuenta,
			(aa.name->>'es_PE'::character varying)::character varying  as nomen,
			coalesce(rc.name,'PEN') as moneda,
			sum(coalesce(l.debit,0)-coalesce(l.credit,0)) as saldo_mn,
			sum(coalesce(l.amount_currency)) as saldo_me
			from account_cta_cte_si l
			LEFT JOIN account_account aa ON aa.id = l.account_id
			LEFT JOIN res_currency rc ON rc.id = aa.currency_id
			where l.main_id = %d
			group by aa.code, (aa.name->>'es_PE'::character varying), coalesce(rc.name,'PEN')
			"""%(self.cta_cte_id.id)
		return sql