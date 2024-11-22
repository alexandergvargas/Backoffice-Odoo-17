# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
import base64
from io import BytesIO
import re
import uuid


class AccountBookDiaryWizard(models.TransientModel):
	_inherit = 'account.book.diary.wizard'

	currency = fields.Selection([('pen','PEN'),('usd','USD')],string='Mostrar en base a',default='pen')

	def _get_sql(self):
		sql =  super(AccountBookDiaryWizard,self)._get_sql()
		if self.currency == 'usd':
			sql_journals = ""
			if self.content == 'pick':
				if not self.journal_ids:
					raise UserError(u'Debe escoger por lo menos un Diario.')
				sql_journals = "WHERE am.journal_id in (%s) " % (','.join(str(i) for i in self.journal_ids.ids))

			sql = """SELECT
				vst1.periodo::character varying,vst1.fecha,vst1.libro,vst1.voucher,
				vst1.cuenta,vst1.debe,vst1.haber,vst1.balance,
				vst1.moneda,vst1.tc,0::numeric as importe_me,
				regexp_replace(vst1.glosa, '[^a-zA-Z0-9-]', '', 'g') as glosa,
				vst1.td_partner,vst1.doc_partner,vst1.partner,
				vst1.td_sunat,vst1.nro_comprobante,vst1.fecha_doc,vst1.fecha_ven,
				vst1.col_reg,vst1.monto_reg,vst1.medio_pago,vst1.ple_diario,
				vst1.ple_compras,vst1.ple_ventas
				FROM get_diariog_usd('%s','%s',%d) vst1
				LEFT JOIN account_move am on am.id =  vst1.move_id %s
			""" % (self.date_from.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_from_id.date_start.strftime('%Y/%m/%d'),
				self.date_to.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_to_id.date_end.strftime('%Y/%m/%d'),
				self.company_id.id,
				sql_journals)
		return sql

	def get_report(self):
		
		if self.type_show == 'pantalla':
			self.env.cr.execute("""
			DROP VIEW IF EXISTS account_book_diary_view;
			CREATE OR REPLACE view account_book_diary_view as (SELECT row_number() OVER () AS id, T.* FROM ("""+self._get_sql()+""")T)""")
			if self.currency == 'pen':
				view_tree_id = self.env.ref('account_book_diary_it.view_account_book_diary_view_tree')
			else:
				view_tree_id = self.env.ref('account_book_diary_usd_it.view_account_book_diary_view_usd_tree')
			return {
				'name': 'Libro Diario',
				'type': 'ir.actions.act_window',
				'res_model': 'account.book.diary.view',
				'view_mode': 'tree,pivot,graph',
				'view_type': 'form',
				'views': [(view_tree_id.id, 'tree'), (False, 'pivot'), (False, 'graph')]
			}

		if self.type_show == 'excel':
			return self.get_excel()
		
		if self.type_show == 'csv':
			return self.getCsv()

	def get_excel(self):
		if not self.show_header:
			ReportBase = self.env['report.base']
			workbook = ReportBase.get_excel_sql_export(self._get_sql(),self.get_header())
			return self.env['popup.it'].get_file('Libro Diario.xlsx',workbook)
		else:
			import io
			from xlsxwriter.workbook import Workbook
			ReportBase = self.env['report.base']

			direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

			workbook = Workbook(direccion +'Libro_diario.xlsx')
			workbook, formats = ReportBase.get_formats(workbook)

			import importlib
			import sys
			importlib.reload(sys)

			worksheet = workbook.add_worksheet("LIBRO DIARIO")
			worksheet.set_tab_color('blue')

			x=0
			worksheet.merge_range(x,0,x,14, "LIBRO DIARIO", formats['especial5'] )
			x+=2
			worksheet.write(x,0,u"Compañía:",formats['especial2'])
			worksheet.merge_range(x,1,x,12,self.company_id.name,formats['especial2'])
			x+=1
			worksheet.write(x,0,"Fecha Inicial:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.date_from.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_from_id.date_start.strftime('%Y/%m/%d')),formats['especial2'])
			x+=1
			worksheet.write(x,0,"Fecha Final:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.date_to.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_to_id.date_end.strftime('%Y/%m/%d')),formats['especial2'])
			x+=2

			worksheet = ReportBase.get_headers(worksheet,self.get_header(),x,0,formats['boldbord'])
			#DECLARANDO TOTALES
			debe, haber = 0, 0

			self.env.cr.execute(self._get_sql())
			res = self.env.cr.dictfetchall()
			x+=1
			for line in res:
				c=0
				worksheet.write(x,c,line['periodo'] if line['periodo'] else '',formats['especial1'])
				worksheet.write(x,c+1,line['fecha'] if line['fecha'] else '',formats['reverse_dateformat'])
				worksheet.write(x,c+2,line['libro'] if line['libro'] else '',formats['especial1'])
				worksheet.write(x,c+3,line['voucher'] if line['voucher'] else '',formats['especial1'])
				worksheet.write(x,c+4,line['cuenta'] if line['cuenta'] else '',formats['especial1'])
				worksheet.write(x,c+5,line['debe'] if line['debe'] else 0,formats['numberdos'])
				worksheet.write(x,c+6,line['haber'] if line['haber'] else 0,formats['numberdos'])
				worksheet.write(x,c+7,line['balance'] if line['balance'] else 0,formats['numberdos'])
				worksheet.write(x,c+8,line['moneda'] if line['moneda'] else '',formats['especial1'])
				worksheet.write(x,c+9,line['tc'] if line['tc'] else '',formats['numbercuatro'])
				if self.currency == 'pen':
					worksheet.write(x,c+10,line['importe_me'] if line['importe_me'] else 0,formats['numberdos'])
					c+=1
				worksheet.write(x,c+10,line['glosa'] if line['glosa'] else '',formats['especial1'])
				worksheet.write(x,c+11,line['td_partner'] if line['td_partner'] else '',formats['especial1'])
				worksheet.write(x,c+12,line['doc_partner'] if line['doc_partner'] else '',formats['especial1'])
				worksheet.write(x,c+13,line['partner'] if line['partner'] else '',formats['especial1'])
				worksheet.write(x,c+14,line['td_sunat'] if line['td_sunat'] else '',formats['especial1'])
				worksheet.write(x,c+15,line['nro_comprobante'] if line['nro_comprobante'] else '',formats['especial1'])
				worksheet.write(x,c+16,line['fecha_doc'] if line['fecha_doc'] else '',formats['reverse_dateformat'])
				worksheet.write(x,c+17,line['fecha_ven'] if line['fecha_ven'] else '',formats['reverse_dateformat'])
				worksheet.write(x,c+18,line['col_reg'] if line['col_reg'] else '',formats['especial1'])
				worksheet.write(x,c+19,line['monto_reg'] if line['monto_reg'] else '0.00',formats['numberdos'])
				worksheet.write(x,c+20,line['medio_pago'] if line['medio_pago'] else '',formats['especial1'])
				worksheet.write(x,c+21,line['ple_diario'] if line['ple_diario'] else '',formats['especial1'])
				worksheet.write(x,c+23,line['ple_compras'] if line['ple_compras'] else '',formats['especial1'])
				worksheet.write(x,c+24,line['ple_ventas'] if line['ple_ventas'] else '',formats['especial1'])

				debe += line['debe'] if line['debe'] else 0
				haber += line['haber'] if line['haber'] else 0

				x += 1

			#TOTALES

			worksheet.write(x,5,debe,formats['numbertotal'])
			worksheet.write(x,6,haber,formats['numbertotal'])

			if self.currency == 'pen':
				widths = [10,9,7,11,9,10,10,10,5,7,13,47,4,11,40,3,16,12,12,12,12,12,12,12,12]
			else:
				widths = [10,9,7,11,9,10,10,10,5,7,47,4,11,40,3,16,12,12,12,12,12,12,12,12]
			
			worksheet = ReportBase.resize_cells(worksheet,widths)
			workbook.close()

			f = open(direccion +'Libro_diario.xlsx', 'rb')
			return self.env['popup.it'].get_file('Libro Diario.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def getCsv(self):
		ReportBase = self.env['report.base']
		workbook = ReportBase.get_file_sql_export(self._get_sql(),',',True)
		return self.env['popup.it'].get_file('Libro Diario.csv',workbook)
	
	def get_header(self):
		if self.currency == 'pen':
			HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE','MON','TC','IMP ME',
			'GLOSA','TDP','RUC','PARTNER','TD','NRO COMP','FECHA DOC','FECHA VEN','COL REG','MONTO REG','MED PAGO',
			'PLE DIARIO','PLE COMPRAS','PLE VENTAS']
		else:
			HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE','MON','TC',
			'GLOSA','TDP','RUC','PARTNER','TD','NRO COMP','FECHA DOC','FECHA VEN','COL REG','MONTO REG','MED PAGO',
			'PLE DIARIO','PLE COMPRAS','PLE VENTAS']
		return HEADERS