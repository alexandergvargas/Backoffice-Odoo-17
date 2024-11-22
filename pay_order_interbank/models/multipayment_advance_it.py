# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
import re
import importlib
import sys
from xlsxwriter.workbook import Workbook
from datetime import *

class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'

	def get_report_txt(self,bank_parameter):
		if bank_parameter.format_id.name == 'interbank':
			name_doc = "INTERBANK%s.txt"%self.name
			amount_total = f"{sum(self.invoice_ids.mapped('importe_divisa')):016.2f}".replace('.', '')
			#cabecera
			ctxt = "0103      "
			if not self.journal_id.bank_account_id:
				raise UserError(u'Falta configurar la cuenta bancaria del Diario')
			ctxt += self.journal_id.bank_account_id.acc_number.replace('-','')[:13].ljust(13)

			type_doc_param = self.env['type.doc.partnerbank.bank'].search([('partnerbank_type_id','=',self.journal_id.bank_account_id.partner_bank_type_catalog_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code
			if not type_doc_param:
				raise UserError(u'Es necesario configurar el Tipo de Documento %s en los parámetros de Banco \n Ruta: "Contabilidad / Configuración / Tablas / Parametros para Bancos"'%line.partner_id.l10n_latam_identification_type_id.name)
			ctxt += type_doc_param if type_doc_param else '   '

			ctxt += '01' if (self.journal_id.bank_account_id.currency_id.name or 'PEN') == 'PEN' else '10'
			ctxt +=  self.name.replace('-','')[:12].ljust(12)
			today = fields.Datetime.context_timestamp(self, datetime.now())
			ctxt += today.strftime('%Y%m%d%H%M%S')
			ctxt += "0"
			ctxt += self.payment_date.strftime('%Y%m%d')
			ctxt += '{:06}'.format(len(self.invoice_ids))
			ctxt += amount_total
			ctxt += "000000000000000"
			ctxt += "MC001"
			ctxt += """\r\n"""
			for line in self.invoice_ids:
				ctxt += "02"
				ctxt += line.partner_id.vat[:20].ljust(20) if line.partner_id.vat else ''.ljust(20)
				type_invoice_param = self.env['type.doc.invoice.bank'].search([('type_document_id','=',line.tipo_documento.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				if not type_invoice_param:
					raise UserError(u'Es necesario configurar el Tipo de Comprobante %s en los parámetros de Banco \n Ruta: "Contabilidad / Configuración / Tablas / Parametros para Bancos"'%(line.tipo_documento.name))
				ctxt += type_invoice_param if type_invoice_param else ' '
				ctxt += line.invoice_id.nro_comp.replace('-','')[:20].ljust(20) if line.invoice_id.nro_comp else ' '.ljust(20)
				ctxt += line.invoice_id.date_maturity.strftime('%Y%m%d') if line.invoice_id.date_maturity else ' '.ljust(8)
				ctxt += '01' if (line.main_id.journal_id.currency_id.name or 'PEN') == 'PEN' else '10'
				ctxt += f"{line.importe_divisa:016.2f}".replace('.', '')
				ctxt += ' '
				type_payment_param = self.env['type.doc.payment.bank'].search([('payment_type_id','=',line.payment_type_catalog_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				if not type_payment_param:
					raise UserError(u'Debe establecer el Tipo de Abono en el Documento %s'%line.invoice_id.nro_comp)
				ctxt += type_payment_param if type_payment_param else ''
				type_partner_bank_param = self.env['type.doc.partnerbank.bank'].search([('partnerbank_type_id','=',line.cta_abono.partner_bank_type_catalog_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				ctxt += type_partner_bank_param if type_partner_bank_param and type_payment_param not in ('11','99') else '   '
				ctxt += '01' if (line.cta_abono.currency_id.name or 'PEN') == 'PEN' else '10'
				ctxt += line.cta_abono.acc_number.replace('-','')[:23] if line.cta_abono else ' '.ljust(23)
				ctxt += 'C' if line.partner_id.is_company else 'P'
				type_doc_param = self.env['type.doc.partner.bank'].search([('identification_type_id','=',line.partner_id.l10n_latam_identification_type_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				if not type_doc_param:
					raise UserError(u'Es necesario configurar el Tipo de Documento %s en los parámetros de Banco \n Ruta: "Contabilidad / Configuración / Tablas / Parametros para Bancos"'%line.partner_id.l10n_latam_identification_type_id.name)
				ctxt += type_doc_param if type_doc_param else '  '
				ctxt += line.partner_id.vat[:15].ljust(15) if line.partner_id.vat else ''.ljust(15)
				ctxt += re.sub(r'[^A-Za-z0-9 ]', '', line.partner_id.name)[:60].ljust(60) if line.partner_id else ' '.ljust(60)
				ctxt += ' '.ljust(203)
				ctxt += """\r\n"""
			
			#ctxt = ctxt[:-2]

			import importlib
			import sys
			importlib.reload(sys)

			return self.env['popup.it'].get_file(name_doc,base64.encodebytes(b''+ctxt.encode("utf-8")))
		else:				
			return super(MultipaymentAdvanceIt,self).get_report_txt(bank_parameter)

	def get_report_excel(self,bank_parameter):
		if bank_parameter.format_id.name == 'interbank':
			ReportBase = self.env['report.base']
			direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

			workbook = Workbook(direccion +'OrdenPago.xlsx')
			workbook, formats = ReportBase.get_formats(workbook)
			importlib.reload(sys)
			worksheet = workbook.add_worksheet("DETALLE")
			worksheet.set_tab_color('blue')
			
			HEADERS = ['Tipo de Documento',u'Número de Documento','Nombre del Beneficiario',u'Correo Electrónico',
			u'N° Celular','Tipo de doc. de pago',u'N° de doc. de pago','Fecha de Vencimiento del documento','Tipo de Abono',
			'Tipo de Cuenta','Moneda de Cuenta',u'N° Cuenta','Moneda de Abono','Monto de Abono']
			worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
			x=1

			for line in self.invoice_ids:
				type_doc_param = self.env['type.doc.partner.bank'].search([('identification_type_id','=',line.partner_id.l10n_latam_identification_type_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				worksheet.write(x,0,type_doc_param if type_doc_param else '',formats['especial1'])
				worksheet.write(x,1,line.partner_id.vat if line.partner_id.vat else '',formats['especial1'])
				worksheet.write(x,2,re.sub(r'[^A-Za-z0-9 ]+', '', line.partner_id.name) if line.partner_id else '',formats['especial1'])
				worksheet.write(x,3,line.partner_id.email if line.partner_id.email else '',formats['especial1'])
				worksheet.write(x,4,line.partner_id.mobile if line.partner_id.mobile else '',formats['especial1'])
				type_invoice_param = self.env['type.doc.invoice.bank'].search([('type_document_id','=',line.tipo_documento.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				worksheet.write(x,5,type_invoice_param if type_invoice_param else '',formats['especial1'])
				worksheet.write(x,6,re.sub(r'[^A-Za-z0-9]', '', line.invoice_id.nro_comp) if line.invoice_id.nro_comp else '',formats['especial1'])
				worksheet.write(x,7,line.invoice_id.date_maturity.strftime('%Y%m%d') if line.invoice_id.date_maturity else '',formats['especial1'])
				type_payment_param = self.env['type.doc.payment.bank'].search([('payment_type_id','=',line.payment_type_catalog_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				if not type_payment_param:
					raise UserError(u'Debe establecer el Tipo de Abono en el Documento %s'%line.invoice_id.nro_comp)
				worksheet.write(x,8,type_payment_param if type_payment_param else '',formats['especial1'])
				type_partner_bank_param = self.env['type.doc.partnerbank.bank'].search([('partnerbank_type_id','=',line.cta_abono.partner_bank_type_catalog_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				worksheet.write(x,9,type_partner_bank_param if type_partner_bank_param else '',formats['especial1'])
				worksheet.write(x,10,('10' if line.cta_abono.currency_id.name != 'PEN' else '01') if line.cta_abono.currency_id else '01',formats['especial1'])
				worksheet.write(x,11,line.cta_abono.acc_number if line.cta_abono else '',formats['especial1'])
				worksheet.write(x,12,'10' if line.main_id.journal_id.currency_id else '01',formats['especial1'])
				worksheet.write(x,13,line.importe_divisa ,formats['numberdos'])
				x += 1

			widths = [10,15,35,15,10,13,15,15,12,12,10,17,10,12]
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
			worksheet2.write(3,1,u'CAMPO CORREO ELECTRÓNICO DE IDENTIFICACION CONFIGURADO EN SOCIO DE CADA LINEA DE LA PESTAÑA FACTURA',formats['especial1'])
			worksheet2.write(4,1,u'CAMPO MÓVIL CONFIGURADO EN SOCIO DE CADA LINEA DE LA PESTAÑA FACTURA',formats['especial1'])
			worksheet2.write(5,1,u'SALE DEL CODIGO CONFIGURADO EN PARAMETROS DE BANCO (BANCO SELECCIONADO) PESTAÑA "Tipo de Comprobante"',formats['especial1'])
			worksheet2.write(6,1,u'CAMPO FACTURA CONFIGURADO EN LA PESTAÑA FACTURA',formats['especial1'])
			worksheet2.write(7,1,u'CAMPO FECHA VENCIMIENTO CONFIGURADO EN EL APUNTE CONTABLE',formats['especial1'])
			worksheet2.write(8,1,u'SALE DEL CODIGO CONFIGURADO EN PARAMETROS DE BANCO (BANCO SELECCIONADO) PESTAÑA "Tipo de Abono"',formats['especial1'])
			worksheet2.write(9,1,u'SE CONFIGURA ENTRANDO A CTA DE ABONO, CAMPO "TIPO CUENTA"',formats['especial1'])
			worksheet2.write(10,1,u'SE CONFIGURA ENTRANDO A CTA DE ABONO, CAMPO "MONEDA" si no esta establecido por default sera SOLES',formats['especial1'])
			worksheet2.write(11,1,u'SE CONFIGURA ENTRANDO A CTA DE ABONO, CAMPO "NÚMERO DE CUENTA" ',formats['especial1'])
			worksheet2.write(12,1,u'SE CONFIGURA ENTRANDO AL DIARIO , CAMPO "MONEDA" si no esta establecido por default sera SOLES',formats['especial1'])
			worksheet2.write(13,1,u'SALE DEL CAMPO IMPORTE DIVISA',formats['especial1'])

			widths = [30,100]
			worksheet2 = ReportBase.resize_cells(worksheet2,widths)

			

			workbook.close()

			f = open(direccion +'OrdenPago.xlsx', 'rb')
			return self.env['popup.it'].get_file('Pago - %s.xlsx'%bank_parameter.bank_id.name,base64.encodebytes(b''.join(f.readlines())))
		else:				
			return super(MultipaymentAdvanceIt,self).get_report_excel(bank_parameter)