# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
import time
import io
import importlib
import sys
from xlsxwriter.workbook import Workbook
import re

class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'

	def get_report_txt(self,bank_parameter):
		if bank_parameter.format_id.name == 'bbva':
			name_doc = "BBVAPROV.txt"
			amount_total = f"{sum(self.invoice_ids.mapped('importe_divisa')):016.2f}".replace('.', '')
			#cabecera
			ctxt = "750"
			if not self.journal_id.bank_account_id:
				raise UserError(u'Falta configurar la cuenta bancaria del Diario')
			ctxt += self.journal_id.bank_account_id.acc_number.replace('-','')[:20].ljust(20)
			ctxt += self.journal_id.bank_account_id.currency_id.name or 'PEN'
			ctxt += amount_total
			ctxt += "A"
			ctxt += "        "
			ctxt += " "
			ctxt += self.name.replace('-','')[:25].ljust(25)
			ctxt += '{:06}'.format(len(self.invoice_ids))
			ctxt += "S"
			ctxt += "000000000000000000                                                  "
			ctxt += """\r\n"""
			for line in self.invoice_ids:
				ctxt += "002"
				type_doc_param = self.env['type.doc.partner.bank'].search([('identification_type_id','=',line.partner_id.l10n_latam_identification_type_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				if not type_doc_param:
					raise UserError(u'Es necesario configurar el Tipo de Documento %s en los parámetros de Banco \n Ruta: "Contabilidad / Configuración / Tablas / Parametros para Bancos"'%line.partner_id.l10n_latam_identification_type_id.name)
				ctxt += type_doc_param if type_doc_param else ' '
				ctxt += line.partner_id.vat[:12].ljust(12) if line.partner_id.vat else ''.ljust(12)
				#type_payment_param = self.env['type.doc.payment.bank'].search([('payment_type_id','=',line.payment_type_catalog_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				if not line.cta_abono:
					raise UserError(u'Falta configurar la cuenta de abono en el registro %s.'%(line.invoice_id.nro_comp))
				ctxt += 'I' if line.cta_abono.bank_id != self.journal_id.bank_account_id.bank_id else 'P'
				if line.cta_abono.bank_id == self.journal_id.bank_account_id.bank_id:
					cta_abono = line.cta_abono.acc_number.replace('-','')[:20] if line.cta_abono else ' '.ljust(20)
					if len(cta_abono) == 18:
						cta_abono = cta_abono[:8] + '00' + cta_abono[8:]
				else:
					cta_abono = line.cta_abono.cci.replace('-','')[:20].ljust(20) if line.cta_abono else ' '.ljust(20)
				
				ctxt += cta_abono
				ctxt += re.sub(r'[^A-Za-z0-9 ]', '', line.partner_id.name)[:40].ljust(40) if line.partner_id else ' '.ljust(40)
				amount = f"{line.importe_divisa:016.2f}".replace('.', '')
				ctxt += amount
				type_invoice_param = self.env['type.doc.invoice.bank'].search([('type_document_id','=',line.tipo_documento.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				if not type_invoice_param:
					raise UserError(u'Es necesario configurar el Tipo de Comprobante %s en los parámetros de Banco \n Ruta: "Contabilidad / Configuración / Tablas / Parametros para Bancos"'%(line.tipo_documento.name))
				ctxt += type_invoice_param if type_invoice_param else ' '
				ctxt += line.invoice_id.nro_comp.replace('-','')[:12].ljust(12) if line.invoice_id.nro_comp else ' '.ljust(12)
				ctxt += "N"
				ctxt += "                                                                                                                         00000000000000000000000000000000                  "
				ctxt += """\r\n"""
			
			ctxt = ctxt[:-2]

			import importlib
			import sys
			importlib.reload(sys)

			return self.env['popup.it'].get_file(name_doc,base64.encodebytes(b''+ctxt.encode("utf-8")))
		else:
			return super(MultipaymentAdvanceIt,self).get_report_txt(bank_parameter)
		
	def get_report_excel(self,bank_parameter):
		if bank_parameter.format_id.name == 'bbva':
			import io
			from xlsxwriter.workbook import Workbook
			ReportBase = self.env['report.base']
			direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

			workbook = Workbook(direccion +'BBVAPROV.xlsx')
			workbook, formats = ReportBase.get_formats(workbook)

			formats['boldbord'].set_font_size(9)
			formats['especial1'].set_font_size(9)

			import importlib
			import sys
			importlib.reload(sys)

			worksheet = workbook.add_worksheet("bbva")
			worksheet.set_tab_color('blue')

			HEADERS = ["DOI Tipo","DOI Número","Tipo Abono","N° Cuentas a Abonar","Nombre de Beneficiario","Importe Abonar","Tipo Recibo","N° Documento","Abono agrupado","Referencia"]
			worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
			x=1

			for line in self.invoice_ids:
				type_doc_param = self.env['type.doc.partner.bank'].search([('identification_type_id','=',line.partner_id.l10n_latam_identification_type_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				if not type_doc_param:
					raise UserError(u'Es necesario configurar el Tipo de Documento %s en los parámetros de Banco \n Ruta: "Contabilidad / Configuración / Tablas / Parametros para Bancos"'%line.partner_id.l10n_latam_identification_type_id.name)
				worksheet.write(x,0,type_doc_param if type_doc_param else '',formats['especial1'])
				worksheet.write(x,1,line.partner_id.vat[:12].ljust(12) if line.partner_id.vat else ''.ljust(12),formats['especial1'])
				if not line.cta_abono:
					raise UserError(u'Falta configurar la cuenta de abono en el registro %s.'%(line.invoice_id.nro_comp))
				worksheet.write(x,2,'I' if line.cta_abono.bank_id != self.journal_id.bank_account_id.bank_id else 'P',formats['especial1'])
				if line.cta_abono.bank_id == self.journal_id.bank_account_id.bank_id:
					cta_abono = line.cta_abono.acc_number.replace('-','')[:20] if line.cta_abono else ' '.ljust(20)
					if len(cta_abono) == 18:
						cta_abono = cta_abono[:8] + '00' + cta_abono[8:]
				else:
					cta_abono = line.cta_abono.cci.replace('-','')[:20].ljust(20) if line.cta_abono else ' '.ljust(20)
				worksheet.write(x,3,cta_abono,formats['especial1'])
				worksheet.write(x,4,re.sub(r'[^A-Za-z0-9 ]', '', line.partner_id.name)[:40].ljust(40) if line.partner_id else ' '.ljust(40),formats['especial1'])
				amount = str(line.importe_divisa)
				worksheet.write(x,5,amount,formats['especial1'])
				type_invoice_param = self.env['type.doc.invoice.bank'].search([('type_document_id','=',line.tipo_documento.id),('parameter_id','=',bank_parameter.id)],limit=1).code
				if not type_invoice_param:
					raise UserError(u'Es necesario configurar el Tipo de Comprobante %s en los parámetros de Banco \n Ruta: "Contabilidad / Configuración / Tablas / Parametros para Bancos"'%(line.tipo_documento.name))
				worksheet.write(x,6,type_invoice_param if type_invoice_param else ' ',formats['especial1'])
				worksheet.write(x,7,line.invoice_id.nro_comp.replace('-','')[:12].ljust(12) if line.invoice_id.nro_comp else ' '.ljust(12),formats['especial1'])
				worksheet.write(x,8,"N",formats['especial1'])
				worksheet.write(x,9,self.glosa,formats['especial1'])
				x += 1

			widths = [7,10,10,10,4,11,40,4,10,10,10,10,12,12,12,12]
			worksheet = ReportBase.resize_cells(worksheet,widths)
			workbook.close()
			f = open(direccion +'BBVAPROV.xlsx', 'rb')
			return self.env['popup.it'].get_file('BBVAPROV.xlsx',base64.encodebytes(b''.join(f.readlines())))
		else:				
			return super(MultipaymentAdvanceIt,self).get_report_excel(bank_parameter)