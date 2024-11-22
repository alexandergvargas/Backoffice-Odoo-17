# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
import time

class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'
	
	def get_report_txt(self,bank_parameter):
		if bank_parameter.format_id.name == 'bcp':
			if self.is_detraction_payment!=False:
				return self.env['popup.it'].get_message(u'Se ha marcado como PAGO DE DETRACCIONES')
			
			n_operations=0
			total = 0
			lst_all=[]
			
			strall=''
			checksum=0
			elementos = self.env['multipayment.advance.it.line'].search([('main_id','=',self.id)],order='partner_id')
			partners = []
			for deta in elementos:
				partners.append(deta.partner_id.id)
			partners=set(partners)
			for partner in partners:
				n_operations=n_operations+1
				amount_doc =0
				nmovs=0
				elementos = self.env['multipayment.advance.it.line'].search([('main_id','=',self.id),('partner_id','=',partner)],order='partner_id')
				yahead=[]
				for deta in elementos:
					# solo voy a tomar facturas
					if deta.tipo_documento.code in ['01','03','02','00','10','14']:
						yahead.append(deta.invoice_id)
				yahead = set(yahead)
				ids=[]
				for invoice in yahead:
					ids.append(invoice.id)
				aa=self.env['multipayment.advance.it.line'].search([('main_id','=',self.id),('invoice_id','in',ids)],order='partner_id')

				nmovs=len(aa)
				for invoice in yahead:
					lst_deta=[]
					elementos = self.env['multipayment.advance.it.line'].search([('main_id','=',self.id),('invoice_id','=',invoice.id)],order='partner_id')
					for deta in elementos:
						if deta.importe_divisa!=0:
							total=total+abs(deta.importe_divisa)
							amount_doc=amount_doc+abs(deta.importe_divisa)
						else:
							total=total+abs(deta.debe)-abs(deta.haber)
							amount_doc=amount_doc+abs(deta.debe)-abs(deta.haber)
						
						tdocpay = None
						type_invoice_param = self.env['type.doc.invoice.bank'].search([('type_document_id','=',deta.tipo_documento.id),('parameter_id','=',bank_parameter.id)],limit=1).code
						tdocpay = type_invoice_param
						dict_deta = {
							'treg':'D',
							'tcta':'',
							'nun_cta':'',
							'tdoc_partner':'',
							'ndoc_partner':'',
							'partner_name':'',
							'currency': '',
							'amount_doc':'',
							'val_doc':'',
							'num_opes': '',
							'tdocpay':tdocpay,
							'numdocpay':deta.invoice_id.ref,
							'currencydocpay':'D' if deta.currency_id else 'S',
							'amountdocpay':abs(abs(deta.debe)-abs(deta.haber)) if deta.importe_divisa==0 else abs(deta.importe_divisa),
						}
						
						lst_deta.append(dict_deta)
						#añadimos los documentos que dependen de la factura
						l=self.env['doc.invoice.relac'].search([('nro_comprobante','=',deta.invoice_id.move_id.ref)])
						for deta2 in l:
							if deta2.move_id.partner_id.id == deta.partner_id.id:
								deta1=deta2.move_id
								nmovs=nmovs+1
								for a in self.invoice_ids:
									if a.invoice_id.move_id.id == deta1.id:
										tdocpay = None
										type_invoice_param = self.env['type.doc.invoice.bank'].search([('type_document_id','=',a.tipo_documento.id),('parameter_id','=',bank_parameter.id)],limit=1).code
										tdocpay = type_invoice_param
										if a.importe_divisa!=0:
											total=total+abs(a.importe_divisa)
											amount_doc=amount_doc+abs(a.importe_divisa)
										else:
											total=total+abs(a.debe)-abs(a.haber)
											amount_doc=amount_doc+abs(a.debe)-abs(a.haber)
										dict_deta = {
											'treg':'D',
											'tcta':'',
											'nun_cta':'',
											'tdoc_partner':'',
											'ndoc_partner':'',
											'partner_name':'',
											'currency': '',
											'amount_doc':'',
											'val_doc':'',
											'num_opes': '',
											'tdocpay':tdocpay,
											'numdocpay':a.invoice_id.ref,
											'currencydocpay':'D' if a.currency_id else 'S',
											'amountdocpay':abs(abs(a.debe)-abs(a.haber)) if a.importe_divisa!=0 else abs(a.importe_divisa),
										}

										lst_deta.append(dict_deta)
					cmovs=str(nmovs)
					# cabecera

					# aqui debo de impedir que se agrege una linea repetida del partner
					falta=True
					for o in lst_all:
						if deta.partner_id.vat == o['ndoc_partner']:
							falta=False
					nmonto = 0
					
					for l in lst_deta:
						if l['tdocpay']=='N':
							nmonto = nmonto-l['amountdocpay']
						else:
							nmonto = nmonto+l['amountdocpay']

					if falta:
						if not deta.cta_abono:
							raise UserError(u'Falta configurar la cuenta de abono en el registro %s.'%(deta.invoice_id.nro_comp))	
						checksum=checksum+int(deta.cta_abono.acc_number.replace('-','')[3:])	
						type_partnerbank_param = self.env['type.doc.partnerbank.bank'].search([('partnerbank_type_id','=',deta.cta_abono.partner_bank_type_catalog_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code	
						if not deta.cta_abono.partner_bank_type_catalog_id:
							raise UserError(u'Es necesario establecer el Tipo de Cuenta para la Cuenta Bancaria %s del Socio %s'%(deta.cta_abono.acc_number, deta.partner_id.name))
						dict_head = {
							'treg':'A',
							'tcta':type_partnerbank_param,
							'nun_cta':deta.cta_abono.acc_number,
							'tdoc_partner':deta.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
							'ndoc_partner':deta.partner_id.vat,
							'partner_name':(deta.partner_id.name[:75]) if len(deta.partner_id.name) > 75 else deta.partner_id.name.ljust(75,' '),
							'currency': 'D' if deta.currency_id else 'S',
							'amount_doc':nmonto,
							'val_doc':'S',
							'num_opes': cmovs.rjust(4,'0'),
							'tdocpay':'',
							'numdocpay':'',
							'currencydocpay':'',
							'amountdocpay':0,
						}
						lst_all.append(dict_head)

					for l in lst_deta:
						lst_all.append(l)
				p = self.env['res.partner'].search([('id','=',partner)])
				for l in lst_all:
					if l['ndoc_partner']==p.vat:
						l['amount_doc']=amount_doc


			# cuenta de la empresa (cargo)
			if not self.journal_id.bank_account_id.acc_number:
				return self.env['popup.it'].get_message(u'Falta configurar el Numero de Cuenta para el Diario: '+self.journal_id.name)	
			checksum=checksum+int(self.journal_id.bank_account_id.acc_number.replace('-','')[3:])
			print(1,self.journal_id.bank_account_id.acc_number.replace('-',''))
			strall = '1'+str(n_operations).rjust(6,'0')
			strall =strall+str(self.payment_date.year)+str(self.payment_date.month).rjust(2,'0')+str(self.payment_date.day).rjust(2,'0')
			strall =strall+'C'
			currencyc = '0001'
			if self.journal_id.currency_id.id != False:
				currencyc = '1001'
			strall =strall+currencyc
			strall =strall+self.journal_id.bank_account_id.acc_number.replace('-','').ljust(20,' ')
			strall =strall+("{:.2f}".format(total)).rjust(17,'0')

			strall =strall+self.glosa.ljust(40,' ')
			strall =strall+'N'+str(checksum).rjust(15,'0')
			strall =strall+'\r\n'
			for l in lst_all:
				if l['tcta']:
					strall =strall+'2'
					# strall =strall+l['treg']
					strall =strall+l['tcta']
					strall =strall+l['nun_cta'].replace('-','').ljust(20,' ')+'1'
					strall =strall+l['tdoc_partner']
					strall =strall+l['ndoc_partner'].ljust(12,' ')
					strall =strall+'   '
					strall =strall+l['partner_name']
					strall =strall+('Referencia Beneficiario '+l['ndoc_partner']).ljust(40,' ')
					strall =strall+('Ref Emp '+ l['ndoc_partner']).ljust(20,' ')
					strall =strall+currencyc
					strall =strall+("{:.2f}".format(l['amount_doc'])).rjust(17,'0')+'S'			
					strall =strall+'\r\n'
				else:
					strall =strall+'3'
					strall =strall+l['tdocpay']
					strall =strall+l['numdocpay'].replace('-','').replace(' ','').rjust(15,'0')
					strall =strall+("{:.2f}".format(l['amountdocpay'])).rjust(17,'0')
					strall =strall+'\r\n'
			cada = time.strftime('%Y%m%d')
			name_doc = 'PROVEEDORES'+cada+'.txt'
			

			import importlib
			import sys
			importlib.reload(sys)

			return self.env['popup.it'].get_file(name_doc,base64.encodebytes(b''+strall.encode("utf-8")))	

		else:
			return super(MultipaymentAdvanceIt,self).get_report_txt(bank_parameter)
		
	def get_report_excel(self,bank_parameter):
		if bank_parameter.format_id.name == 'bcp':
			if self.is_detraction_payment:
				return self.env['popup.it'].get_message(u'Se ha marcado como PAGO DE DETRACCIONES')
			
			n_operations=0
			date_proc = self.payment_date
			reg_type = 'C'
			charge_account_type = 'C'
			total = 0
			ref=self.glosa
			lst_all=[]
			
			strall=''
			#checksum=0
			elementos = self.env['multipayment.advance.it.line'].search([('main_id','=',self.id)],order='partner_id')
			partners = []
			for deta in elementos:
				partners.append(deta.partner_id.id)
			partners=set(partners)
			for partner in partners:
				n_operations=n_operations+1
				amount_doc =0
				nmovs=0
				elementos = self.env['multipayment.advance.it.line'].search([('main_id','=',self.id),('partner_id','=',partner)],order='partner_id')
				yahead=[]
				for deta in elementos:
					# solo voy a tomar facturas
					if deta.tipo_documento.code in ['01','03','02','00','10','14']:
						yahead.append(deta.invoice_id)
				yahead = set(yahead)
				#yahead=[]
				ids=[]
				for invoice in yahead:
					ids.append(invoice.id)
				aa=self.env['multipayment.advance.it.line'].search([('main_id','=',self.id),('invoice_id','in',ids)],order='partner_id')
				#print(1234,aa,ids)
				#for l in aa:
				#	print(123,l.invoice_id.ref,l.partner_id.name)

				nmovs=len(aa)
				for invoice in yahead:
					lst_deta=[]
					elementos = self.env['multipayment.advance.it.line'].search([('main_id','=',self.id),('invoice_id','=',invoice.id)],order='partner_id')
					for deta in elementos:
					# self.invoice_ids.search([('invoice_id','=',invoice.id)],order='partner_id'):				
						
						
						#print(111,deta.partner_id.name,nmovs)
						if deta.importe_divisa!=0:
							total=total+abs(deta.importe_divisa)
							amount_doc=amount_doc+abs(deta.importe_divisa)
						else:
							total=total+abs(deta.debe)-abs(deta.haber)
							amount_doc=amount_doc+abs(deta.debe)-abs(deta.haber)
						
						tdocpay = None
						type_invoice_param = self.env['type.doc.invoice.bank'].search([('type_document_id','=',deta.tipo_documento.id),('parameter_id','=',bank_parameter.id)],limit=1).code
						tdocpay = type_invoice_param
						dict_deta = {
							'treg':'D',
							'tcta':'',
							'nun_cta':'',
							'tdoc_partner':'',
							'ndoc_partner':'',
							'partner_name':'',
							'currency': '',
							'amount_doc':'',
							'val_doc':'',
							'num_opes': '',
							'tdocpay':tdocpay,
							'numdocpay':deta.invoice_id.ref,
							'currencydocpay':'D' if deta.currency_id else 'S',
							'amountdocpay':abs(abs(deta.debe)-abs(deta.haber)) if deta.importe_divisa==0 else abs(deta.importe_divisa),
						}
						
						lst_deta.append(dict_deta)
						#añadimos los documentos que dependen de la factura
						l=self.env['doc.invoice.relac'].search([('nro_comprobante','=',deta.invoice_id.move_id.ref)])
						for deta2 in l:
							if deta2.move_id.partner_id.id == deta.partner_id.id:
								deta1=deta2.move_id
								nmovs=nmovs+1
								for a in self.invoice_ids:
									if a.invoice_id.move_id.id == deta1.id:
										tdocpay = None
										type_invoice_param = self.env['type.doc.invoice.bank'].search([('type_document_id','=',a.tipo_documento.id),('parameter_id','=',bank_parameter.id)],limit=1).code
										tdocpay = type_invoice_param
										if a.importe_divisa!=0:
											total=total+abs(a.importe_divisa)
											amount_doc=amount_doc+abs(a.importe_divisa)
										else:
											total=total+abs(a.debe)-abs(a.haber)
											amount_doc=amount_doc+abs(a.debe)-abs(a.haber)
										dict_deta = {
											'treg':'D',
											'tcta':'',
											'nun_cta':'',
											'tdoc_partner':'',
											'ndoc_partner':'',
											'partner_name':'',
											'currency': '',
											'amount_doc':'',
											'val_doc':'',
											'num_opes': '',
											'tdocpay':tdocpay,
											'numdocpay':a.invoice_id.ref,
											'currencydocpay':'D' if a.currency_id else 'S',
											'amountdocpay':abs(abs(a.debe)-abs(a.haber)) if a.importe_divisa!=0 else abs(a.importe_divisa),
										}

									lst_deta.append(dict_deta)
					cmovs=str(nmovs)
					falta=True
					for o in lst_all:
						if deta.partner_id.vat == o['ndoc_partner']:
							falta=False
					nmonto = 0
					
					for l in lst_deta:
						if l['tdocpay']=='N':
							nmonto = nmonto-l['amountdocpay']
						else:
							nmonto = nmonto+l['amountdocpay']

					if falta:
						if not deta.cta_abono:
							raise UserError(u'Falta configurar la cuenta de abono en el registro %s.'%(deta.invoice_id.nro_comp))	
						#checksum=checksum+int(deta.cta_abono.acc_number.replace('-','')[3:])	
						type_partnerbank_param = self.env['type.doc.partnerbank.bank'].search([('partnerbank_type_id','=',deta.cta_abono.partner_bank_type_catalog_id.id),('parameter_id','=',bank_parameter.id)],limit=1).code	
						if not deta.cta_abono.partner_bank_type_catalog_id:
							raise UserError(u'Es necesario establecer el Tipo de Cuenta para la Cuenta Bancaria %s del Socio %s'%(deta.cta_abono.acc_number, deta.partner_id.name))			
						dict_head = {
							'treg':'A',
							'tcta':type_partnerbank_param,
							'nun_cta':deta.cta_abono.acc_number,
							'tdoc_partner':deta.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
							'ndoc_partner':deta.partner_id.vat,
							'partner_name':(deta.partner_id.name[:75]) if len(deta.partner_id.name) > 75 else deta.partner_id.name.ljust(75,' '),
							'currency': 'D' if deta.currency_id else 'S',
							'amount_doc':nmonto,
							'val_doc':'S',
							'num_opes': cmovs.rjust(4,'0'),
							'tdocpay':'',
							'numdocpay':'',
							'currencydocpay':'',
							'amountdocpay':'',
						}
						lst_all.append(dict_head)

					for l in lst_deta:
						lst_all.append(l)
				
				p = self.env['res.partner'].search([('id','=',partner)])
				for l in lst_all:
					if l['ndoc_partner']==p.vat:
						l['amount_doc']=amount_doc

			fproceso=str(self.payment_date.year)+str(self.payment_date.month).rjust(2,'0')+str(self.payment_date.day).rjust(2,'0')
			currencyc = 'S'
			if self.journal_id.currency_id.id != False:
				currencyc = 'D'
			
			import io
			from xlsxwriter.workbook import Workbook
			from xlsxwriter.utility import xl_rowcol_to_cell

			direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')
			
			file_name_rute=direccion+'pagosmultiples.xlsx'
			ReportBase = self.env['report.base']
			workbook = Workbook(file_name_rute)
			workbook, formats = ReportBase.get_formats(workbook)
			formats['boldbord'].set_font_size(10)
			
			worksheet = workbook.add_worksheet('Pagos')

			worksheet.write(5, 0, u"DATOS DEL CARGO", formats['boldbord'])

			HEADERS = ['Tipo de Registro','Cantidad de abonos en la planilla','Fecha de proceso','Tipo de Cuenta de cargo','Cuenta de cargo','Monto total de la planilla','Referencia de la planilla']
			worksheet = ReportBase.get_headers(worksheet,HEADERS,6,0,formats['boldbord'])

			worksheet.write(7, 0, reg_type, formats['especial1'])
			worksheet.write(7, 1, str(n_operations).rjust(4,'0'), formats['especial1'])
			worksheet.write(7, 2, fproceso, formats['especial1'])
			worksheet.write(7, 3, charge_account_type, formats['especial1'])
			worksheet.write(7, 4, self.journal_id.bank_account_id.acc_number.replace('-',''), formats['especial1'])
			worksheet.write(7, 5, total, formats['especial1'])
			worksheet.write(7, 6, ref, formats['especial1'])		



			worksheet.write(8, 0, u"DATOS DEL ABONO A CUENTA", formats['boldbord'])

			HEADERS2 = ["Tipo de Registro","Tipo de Cuenta de Abono","Cuenta de Abono","Tipo de Documento de Identidad","Número de Documento de Identidad","Correlativo de Documento de Identidad",
			   			"Nombre del proveedor","Tipo de Moneda de Abono","Monto del Abono","Validación IDC del proveedor vs Cuenta","Cantidad Documentos relacionados al Abono",
						"Tipo de Documento a pagar","Nro. del Documento","Moneda Documento","Monto del Documento"]
			worksheet = ReportBase.get_headers(worksheet,HEADERS2,9,0,formats['boldbord'])

			x=10

			for l in lst_all:
				strall=''
				if len(l['tcta'])>0:
					worksheet.write(x, 0,'A'  )
					worksheet.write(x, 1,l['tcta'])
					worksheet.write(x, 2,l['nun_cta'])
					worksheet.write(x, 3,l['tdoc_partner'])
					worksheet.write(x, 4,l['ndoc_partner'])
					worksheet.write(x, 5,'' , )
					worksheet.write(x, 6,l['partner_name'])
					worksheet.write(x, 7,currencyc)
					worksheet.write(x, 8, ("{:.2f}".format(l['amount_doc'])))
					worksheet.write(x, 9, 'S')
					worksheet.write(x, 10,l['num_opes'])
					worksheet.write(x, 11,'' )
					worksheet.write(x, 12,'' )
					worksheet.write(x, 13,'' )
					worksheet.write(x, 14,'' )
				else:
					worksheet.write(x, 0,'D' )
					worksheet.write(x, 1, '')
					worksheet.write(x, 2,'' )
					worksheet.write(x, 3,'' )
					worksheet.write(x, 4,'' )
					worksheet.write(x, 5,'' )
					worksheet.write(x, 6,'' )
					worksheet.write(x, 7,'' )
					worksheet.write(x, 8,'')
					worksheet.write(x, 9, '')
					worksheet.write(x, 10,'')
					worksheet.write(x, 11, l['tdocpay'])
					worksheet.write(x, 12, l['numdocpay'].replace('-','').replace(' ',''))
					worksheet.write(x, 13, currencyc)
					worksheet.write(x, 14, ("{:.2f}".format(l['amountdocpay'])))


				x=x+1
			widths = [20,16,29,14,17,16,51,19,17,16,23,12,14,11,16]
			worksheet = ReportBase.resize_cells(worksheet,widths)
			workbook.close()
			f = open(file_name_rute, 'rb')
			return self.env['popup.it'].get_file('Pagos para el BCP.xlsx', base64.encodebytes(b''.join(f.readlines())))
		else:				
			return super(MultipaymentAdvanceIt,self).get_report_excel(bank_parameter)