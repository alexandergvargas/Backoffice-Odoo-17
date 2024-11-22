# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, AccessError
import csv
import base64
import io as StringIO
import xlrd
from odoo.tools import ustr
import logging
_logger = logging.getLogger(__name__)
import json


class import_account_multipayment_advance_wizard(models.Model):
	_name = 'import.account.multipayment.advance.wizard'
	_description = 'Importador de Lineas de Caja'
	
	name = fields.Char('name')

	multipayment_advance_id = fields.Many2one(
		comodel_name='multipayment.advance.it', 
		string='Pago Multiple',
		readonly=True)
	
	document_file = fields.Binary(
		string='Excel')
	
	name_file = fields.Char(
		string='Nombre de Archivo')
	

	def show_success_msg(self, counter, skipped_line_no):							  
		context = dict(self._context or {})
		dic_msg = str(counter) + " Registros importados con éxito"
		if skipped_line_no:
			dic_msg = dic_msg + "\nNota:"
		for k, v in skipped_line_no.items():
			dic_msg = dic_msg + "\nFila No Importada " + k + " " + v + " "
		context['message'] = dic_msg 		
		return self.env['popup.it'].get_message(dic_msg)
	
	def search_account(self,val):
		for i in self:
			account = i.env['account.account'].search([('code', '=', val),('company_id','=',i.env.company.id)], limit=1)
			return account
	
	def search_partner(self,val):
		for i in self:
			partner = i.env['res.partner'].search([('vat', '=', val)], limit=1)
			return partner
	
	def search_td(self,val):
		for i in self:
			td = i.env['l10n_latam.document.type'].search([('code', '=', val)], limit=1)
			return td
	
	def search_currency(self,val):
		for i in self:
			currency = i.env['res.currency'].search([('name', '=', val)], limit=1)
			return currency	
		
	def find_analytic_account(self, code):
		analytic_obj = self.env['account.analytic.account']
		json='{'
		a = str(code).replace('(', ',').replace(')','').replace('%','')
		aux = 0
		for i in a.split(","):
			val = self.vale_numer(i)
			aux+=1
			if val is None:
				analytic_search = analytic_obj.search([('code', '=', str(i)),('company_id','=',self.env.company.id)],limit=1)
				if analytic_search:
					json+='"'+str(analytic_search.id)+'":'
				else:					
					raise UserError(u'No existe una la Distribución Analitica con el Codigo "%s" en esta Compañia'% i)
			else:
				if (len(a.split(","))) == aux:
					json+=' '+str(val)
				else:
					json+=' '+str(val) +', '
		json+='}'
		return json
	
	def vale_numer(self,valor):
		try:
			return float(valor)
		except:
			return None
		
	def convert_date(self, date):
		try:
			numeric_date = float(str(date))
			seconds = (numeric_date - 25569) * 86400.0
			d = datetime.utcfromtimestamp(seconds)
			return d.strftime('%Y-%m-%d')  
		except ValueError:
			for fmt in ("%d-%m-%Y", "%Y/%m/%d", "%b %d, %Y", "%d %B %Y","%d/%m/%Y"):
				try:
					return datetime.strptime(str(date), fmt).strftime("%Y-%m-%d")
				except ValueError:
					continue
			raise UserError(f"Formato no reconocido para la fecha: {str(date)}")
		
	def import_line_cash(self):
		for i in self:
			line_ids_obj = self.env['multipayment.advance.it.line2']		
			if self and self.document_file:			
					counter = 1
					skipped_line_no = {}
					some_lot_not_found = False                      
					try:
						wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.document_file))
						sheet = wb.sheet_by_index(0)     
						skip_header = True    
						for row in range(sheet.nrows):
							try:
								if skip_header:
									skip_header = False								
									counter = counter + 1
									continue
								
								if sheet.cell(row, 0).value != '': 
									vals = {}									
									account = i.search_account(sheet.cell(row, 0).value)
									if account:												
										vals.update({'account_id' : account.id})									
									else:
										skipped_line_no[str(counter)] = " - Cuenta no encontrada [%s]"%(str(sheet.cell(row, 0).value)) 
										counter = counter + 1 
										continue

									if  sheet.cell(row, 1).value != '':
										partner = i.search_partner(sheet.cell(row, 1).value)
										if partner:
											vals.update({'partner_id' : partner.id})										
										else:
											skipped_line_no[str(counter)] = " - Partner [%s] no encontrado "%(str(sheet.cell(row, 1).value)) 
											counter = counter + 1 
											continue
									if sheet.cell(row, 2).value != '':
										td = i.search_td(sheet.cell(row, 2).value)
										if td:
											vals.update({'type_document_id' : td.id})
										else:
											skipped_line_no[str(counter)] = " - No se encontro el Tipo Documento [%s] "%(str(sheet.cell(row, 2).value)) 
											counter = counter + 1 
											continue
									if sheet.cell(row, 3).value != '':
										vals.update({'nro_comp' : str(sheet.cell(row, 3).value)})
									if sheet.cell(row, 4).value != '':
										vals.update({'name' : str(sheet.cell(row, 4).value)})
									if sheet.cell(row, 5).value != '':
										currency = i.search_currency(sheet.cell(row, 5).value)
										if currency:
											vals.update({'currency_id' : currency.id})
										else:
											skipped_line_no[str(counter)] = " - No se encontro la Moneda [%s] "%(str(sheet.cell(row, 5).value)) 
											counter = counter + 1 
											continue
									if sheet.cell(row, 6).value != '':
										vals.update({'importe_divisa' : sheet.cell(row, 6).value})
									if sheet.cell(row, 7).value != '':										
										analytic_distribution = json.loads(self.find_analytic_account(sheet.cell(row, 7).value))
										if analytic_distribution:											
											vals.update({'analytic_distribution' : analytic_distribution})
									if sheet.cell(row, 8).value != '':
										date = i.convert_date(sheet.cell(row, 8).value)
										if date:
											vals.update({'fecha_vencimiento' : date})				
									if sheet.cell(row, 9).value == 'TRUE':
										vals.update({'cta_cte_origen' : True})										
									vals.update({'main_id' : i.multipayment_advance_id.id})					
									line_ids_obj.create(vals)																		
									counter = counter + 1
								else:
									skipped_line_no[str(counter)] = " - La Columna Cuenta está vacía."  
									counter = counter + 1						
							except Exception as e:
								skipped_line_no[str(counter)] = " - El valor no es válido " + ustr(e)   
								counter = counter + 1 
								continue          								
					except Exception:
						raise UserError(_("Lo sentimos, su archivo de Excel no coincide con nuestro formato"))					
					if counter > 1:
						completed_records = (counter - len(skipped_line_no)) - 2
						res = self.show_success_msg(completed_records, skipped_line_no)
						return res
					

	def download_template(self):
		return {
			'type' : 'ir.actions.act_url',
			'url': '/web/binary/download_template_lines_cash_import',
			'target': 'new',
			}
		