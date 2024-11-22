# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
import time
import io
import importlib
import sys
from xlsxwriter.workbook import Workbook

class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'

	def get_report_txt(self,bank_parameter):
		if bank_parameter.format_id.name == 'banbif':
			return self.env['popup.it'].get_message('Aún no se encuentra disponible.')
		else:				
			return super(MultipaymentAdvanceIt,self).get_report_txt(bank_parameter)

	def get_report_excel(self,bank_parameter):
		if bank_parameter.format_id.name == 'banbif':
			ReportBase = self.env['report.base']
			direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

			workbook = Workbook(direccion +'OrdenPago.xlsx')
			workbook, formats = ReportBase.get_formats(workbook)
			
			importlib.reload(sys)

			worksheet = workbook.add_worksheet("DETALLE")
			worksheet.set_tab_color('blue')
			HEADERS = ['Tipo Documento','Nro Documento Proveedor','Nombre del Proveedor','Tipo de Documento de Pago','Numero de Documento de Pago',
			'Moneda de Pago','Importe','Fecha de Pago','Forma de Pago','Codigo del Banco','Moneda de Cuenta','Numero de Cuenta']

			worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
			x=1

			for line in self.invoice_ids:
				type_doc_param = self.env['type.doc.partner.bank'].search([('identification_type_id','=',line.partner_id.l10n_latam_identification_type_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				worksheet.write(x,0,type_doc_param if type_doc_param else '',formats['especial1'])
				worksheet.write(x,1,line.partner_id.vat if line.partner_id.vat else '',formats['especial1'])
				worksheet.write(x,2,line.partner_id.name if line.partner_id else '',formats['especial1'])
				type_invoice_param = self.env['type.doc.invoice.bank'].search([('type_document_id','=',line.tipo_documento.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				worksheet.write(x,3,type_invoice_param if type_invoice_param else '',formats['especial1'])
				worksheet.write(x,4,line.invoice_id.nro_comp if line.invoice_id.nro_comp else '',formats['especial1'])
				worksheet.write(x,5,'USD' if line.main_id.journal_id.currency_id else 'SOL',formats['especial1'])
				worksheet.write(x,6,line.importe_divisa ,formats['numberdos'])
				worksheet.write(x,7,line.main_id.payment_date.strftime('%Y-%m-%d') if line.main_id.payment_date else '',formats['especial1'])
				type_payment_param = self.env['type.doc.payment.bank'].search([('payment_type_id','=',line.payment_type_catalog_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				worksheet.write(x,8,type_payment_param if type_payment_param else '',formats['especial1'])
				worksheet.write(x,9,line.cta_abono.bank_id.code_bank if line.cta_abono.bank_id.code_bank else '',formats['especial1'])
				worksheet.write(x,10,('USD' if line.cta_abono.currency_id.name != 'PEN' else 'SOL') if line.cta_abono.currency_id else 'SOL',formats['especial1'])
				worksheet.write(x,11,line.cta_abono.acc_number if line.cta_abono else '',formats['especial1'])
				x += 1

			widths = [15,24,47,26,30,16,16,15,23,16,18,18]
			worksheet = ReportBase.resize_cells(worksheet,widths)

			worksheet2 = workbook.add_worksheet("FORMATO")
			worksheet2.set_tab_color('green')
			c=0
			for i in HEADERS:
				worksheet2.write(c,0,i,formats['boldbord'])
				c+=1

			worksheet2.write(0,1,u'SALE DEL CODIGO CONFIGURADO EN PARAMETROS DE BANCO (BANCO SELECCIONADO) PESTAÑA "Tipo de Documento"',formats['especial1'])
			worksheet2.write(1,1,u'CAMPO NUMERO DE IDENTIFICACION CONFIGURADO EN SOCIO DE CADA LINEA DE LA PESTAÑA FACTURA',formats['especial1'])
			worksheet2.write(2,1,u'CAMPO NOMBRE CONFIGURADO EN SOCIO DE CADA LINEA DE LA PESTAÑA FACTURA',formats['especial1'])
			worksheet2.write(3,1,u'SALE DEL CODIGO CONFIGURADO EN PARAMETROS DE BANCO (BANCO SELECCIONADO) PESTAÑA "Tipo de Comprobante"',formats['especial1'])
			worksheet2.write(4,1,u'CAMPO FACTURA CONFIGURADO EN LA PESTAÑA FACTURA',formats['especial1'])
			worksheet2.write(5,1,u'SE CONFIGURA ENTRANDO AL DIARIO , CAMPO "MONEDA" si no esta establecido por default sera SOLES',formats['especial1'])
			worksheet2.write(6,1,u'SALE DEL CAMPO IMPORTE DIVISA',formats['especial1'])
			worksheet2.write(7,1,u'SALE DEL CAMPO FECHA PAGO',formats['especial1'])
			worksheet2.write(8,1,u'SALE DEL CODIGO CONFIGURADO EN PARAMETROS DE BANCO (BANCO SELECCIONADO) PESTAÑA "Tipo de Abono"',formats['especial1'])
			worksheet2.write(9,1,u'SE CONFIGURA ENTRANDO A CTA DE ABONO, CAMPO "BANCO->CODIGO" ',formats['especial1'])
			worksheet2.write(10,1,u'SE CONFIGURA ENTRANDO A CTA DE ABONO, CAMPO "MONEDA" si no esta establecido por default sera SOLES',formats['especial1'])
			worksheet2.write(11,1,u'SE CONFIGURA ENTRANDO A CTA DE ABONO, CAMPO "NÚMERO DE CUENTA" ',formats['especial1'])

			widths = [30,100]
			worksheet2 = ReportBase.resize_cells(worksheet2,widths)

			workbook.close()

			f = open(direccion +'OrdenPago.xlsx', 'rb')
			return self.env['popup.it'].get_file('Pago - %s.xlsx'%bank_parameter.bank_id.name,base64.encodebytes(b''.join(f.readlines())))
		else:				
			return super(MultipaymentAdvanceIt,self).get_report_excel(bank_parameter)
