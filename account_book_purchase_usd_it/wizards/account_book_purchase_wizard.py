# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class AccountBookPurchaseWizard(models.TransientModel):
	_inherit = 'account.book.purchase.wizard'

	currency = fields.Selection([('pen','PEN'),('usd','USD')],string=u'Moneda',default='pen', required=True)

	def get_report(self):
		
		if self.type_show == 'pantalla':
			self.env.cr.execute("""
			DROP VIEW IF EXISTS account_book_purchase_view CASCADE;
			CREATE OR REPLACE view account_book_purchase_view as (SELECT row_number() OVER () AS id, T.* FROM ("""+self._get_sql()+""")T)""")
			if self.currency == 'pen':
				view_id = self.env.ref('account_book_purchase_it.view_account_book_purchase_view_tree')
			else:
				view_id = self.env.ref('account_book_purchase_usd_it.view_account_book_purchase_usd_view_tree')
			return {
				'name': 'Registro de Compras',
				'type': 'ir.actions.act_window',
				'res_model': 'account.book.purchase.view',
				'view_mode': 'tree',
				'view_type': 'form',
				'view_id': view_id.id,
			}

		if self.type_show == 'excel':
			return self.get_excel()
		
		if self.type_show == 'csv':
			return self.getCsv()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Registro_Compras.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########REGISTRO COMPRAS############
		worksheet = workbook.add_worksheet("REGISTRO COMPRAS")
		worksheet.set_tab_color('blue')

		x=0
		if self.show_header:
			worksheet.merge_range(x,0,x,12, "REGISTRO DE COMPRAS", formats['especial5'] )
			x+=2
			worksheet.write(x,0,u"Compañía:",formats['especial2'])
			worksheet.merge_range(x,1,x,12,self.company_id.name,formats['especial4'])
			x+=1
			worksheet.write(x,0,"Fecha Inicial:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.date_from.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_from_id.date_start.strftime('%Y/%m/%d')),formats['especialdate'])
			x+=1
			worksheet.write(x,0,"Fecha Final:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.date_to.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_to_id.date_end.strftime('%Y/%m/%d')),formats['especialdate'])
			x+=2

		worksheet = ReportBase.get_headers(worksheet,self.get_header(),x,0,formats['boldbord'])
		#DECLARANDO TOTALES
		base1, base2, base3, cng, isc, otros, icbper, igv1, igv2, igv3, total = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

		self.env.cr.execute(self._get_sql())
		res = self.env.cr.dictfetchall()
		c = 1 if self.currency=='pen' else 0
		x+=1

		for line in res:
			worksheet.write(x,0,line['periodo'] if line['periodo'] else '',formats['especial1'])
			worksheet.write(x,1,line['fecha_cont'] if line['fecha_cont'] else '',formats['reverse_dateformat'])
			worksheet.write(x,2,line['libro'] if line['libro'] else '',formats['especial1'])
			worksheet.write(x,3,line['voucher'] if line['voucher'] else '',formats['especial1'])
			worksheet.write(x,4,line['fecha_e'] if line['fecha_e'] else '',formats['reverse_dateformat'])
			worksheet.write(x,5,line['fecha_v'] if line['fecha_v'] else '',formats['reverse_dateformat'])
			worksheet.write(x,6,line['td'] if line['td'] else '',formats['especial1'])
			worksheet.write(x,7,line['serie'] if line['serie'] else '',formats['especial1'])
			worksheet.write(x,8,line['anio'] if line['anio'] else '',formats['especial1'])
			worksheet.write(x,9,line['numero'] if line['numero'] else '',formats['especial1'])
			worksheet.write(x,10,line['tdp'] if line['tdp'] else '',formats['especial1'])
			worksheet.write(x,11,line['docp'] if line['docp'] else '',formats['especial1'])
			worksheet.write(x,12,line['namep'] if line['namep'] else '',formats['especial1'])
			worksheet.write(x,13,line['base1'] if line['base1'] else '0.00',formats['numberdos'])
			worksheet.write(x,14,line['base2'] if line['base2'] else '0.00',formats['numberdos'])
			worksheet.write(x,15,line['base3'] if line['base3'] else '0.00',formats['numberdos'])
			worksheet.write(x,16,line['cng'] if line['cng'] else '0.00',formats['numberdos'])
			worksheet.write(x,17,line['isc'] if line['isc'] else '0.00',formats['numberdos'])
			worksheet.write(x,18,line['icbper'] if line['icbper'] else '0.00',formats['numberdos'])
			worksheet.write(x,19,line['otros'] if line['otros'] else '0.00',formats['numberdos'])
			worksheet.write(x,20,line['igv1'] if line['igv1'] else '0.00',formats['numberdos'])
			worksheet.write(x,21,line['igv2'] if line['igv2'] else '0.00',formats['numberdos'])
			worksheet.write(x,22,line['igv3'] if line['igv3'] else '0.00',formats['numberdos'])
			worksheet.write(x,23,line['total'] if line['total'] else '0.00',formats['numberdos'])
			worksheet.write(x,24,line['name'] if line['name'] else '',formats['especial1'])
			if self.currency=='pen':
				worksheet.write(x,25,line['monto_me'] if line['monto_me'] else '0.00',formats['numberdos'])
			worksheet.write(x,c+25,line['currency_rate'] if line['currency_rate'] else '0.0000',formats['numbercuatro'])
			worksheet.write(x,c+26,line['fecha_det'] if line['fecha_det'] else '',formats['reverse_dateformat'])
			worksheet.write(x,c+27,line['comp_det'] if line['comp_det'] else '',formats['especial1'])
			worksheet.write(x,c+28,line['f_doc_m'] if line['f_doc_m'] else '',formats['reverse_dateformat'])
			worksheet.write(x,c+29,line['td_doc_m'] if line['td_doc_m'] else '',formats['especial1'])
			worksheet.write(x,c+30,line['serie_m'] if line['serie_m'] else '',formats['especial1'])
			worksheet.write(x,c+31,line['numero_m'] if line['numero_m'] else '',formats['especial1'])
			worksheet.write(x,c+32,line['glosa'] if line['glosa'] else '',formats['especial1'])

			base1 += line['base1'] if line['base1'] else 0
			base2 += line['base2'] if line['base2'] else 0
			base3 += line['base3'] if line['base3'] else 0
			cng += line['cng'] if line['cng'] else 0
			isc += line['isc'] if line['isc'] else 0
			icbper += line['icbper'] if line['icbper'] else 0
			otros += line['otros'] if line['otros'] else 0
			igv1 += line['igv1'] if line['igv1'] else 0
			igv2 += line['igv2'] if line['igv2'] else 0
			igv3 += line['igv3'] if line['igv3'] else 0
			total += line['total'] if line['total'] else 0

			x += 1

		#TOTALES

		worksheet.write(x,13,base1,formats['numbertotal'])
		worksheet.write(x,14,base2,formats['numbertotal'])
		worksheet.write(x,15,base3,formats['numbertotal'])
		worksheet.write(x,16,cng,formats['numbertotal'])
		worksheet.write(x,17,isc,formats['numbertotal'])
		worksheet.write(x,18,icbper,formats['numbertotal'])
		worksheet.write(x,19,otros,formats['numbertotal'])
		worksheet.write(x,20,igv1,formats['numbertotal'])
		worksheet.write(x,21,igv2,formats['numbertotal'])
		worksheet.write(x,22,igv3,formats['numbertotal'])
		worksheet.write(x,23,total,formats['numbertotal'])

		if self.currency=='pen':
			widths = [12,14,7,11,11,12,3,6,5,10,5,12,40,11,11,11,11,11,11,11,11,11,11,11,6,12,6,12,11,15,11,9,12,72]
		else:
			widths = [12,14,7,11,11,12,3,6,5,10,5,12,40,11,11,11,11,11,11,11,11,11,11,11,6,6,12,11,15,11,9,12,72]
		
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Registro_Compras.xlsx', 'rb')
		return self.env['popup.it'].get_file('RC%s.xlsx'%(self.company_id.partner_id.vat),base64.encodebytes(b''.join(f.readlines())))
	
	def get_header(self):
		HEADERS =  super(AccountBookPurchaseWizard,self).get_header()
		if self.currency=='usd':
			HEADERS = ['PERIODO','FECHA CONT','LIBRO','VOUCHER','FECHA EM','FECHA VEN','TD','SERIE',u'AÑO',u'NÚMERO','TDP','RUC','PARTNER',
			'BIOGYE','BIOGEYNG','BIONG','CNG','ISC','ICBPER','OTROS','IGV 1','IGV 2','IGV 3','TOTAL','MON','TC','FECHA DET','COMP DET',
			'FECHA DOC M','TD DOC M','SERIE M','NUMERO M','GLOSA']
		return HEADERS

	def _get_sql(self):
		sql =  super(AccountBookPurchaseWizard,self)._get_sql()
		if self.currency=='usd':
			sql = """SELECT periodo::character varying, fecha_cont, libro, voucher, fecha_e, fecha_v, td, 
			serie, anio, numero, tdp, docp, namep, base1, base2, base3, cng, isc, icbper, otros, igv1, igv2, igv3, total,
			name, currency_rate, fecha_det, 
			comp_det, f_doc_m, td_doc_m, serie_m, numero_m, glosa
			from get_compras_1_1_usd('%s','%s',%d)
			""" % (self.date_from.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_from_id.date_start.strftime('%Y/%m/%d'),
				self.date_to.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_to_id.date_end.strftime('%Y/%m/%d'),
				self.company_id.id)
		return sql