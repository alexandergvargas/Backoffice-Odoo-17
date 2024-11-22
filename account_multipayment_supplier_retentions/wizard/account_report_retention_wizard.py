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


class AccountReportRetentionWizard(models.TransientModel):
	_name = 'account.report.retention.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_from_id = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to_id = fields.Many2one('account.period',string='Periodo Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF')],default='pantalla',string=u'Mostrar en', required=True)

	def get_sql(self):
		sql = """
			SELECT 
			arp.name,
			arp.date,
			rp.name as partner,
			rp.vat as ruc,
			rc.currency_unit_label as moneda,
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
			am.invoice_date,
			mai.payment_date,
			mai.tc,
			arpl.amount_total_signed,
			amp.retention_percentage * 100 as percentage,
			arpl.amount_retention,
			arpl.amount_retention/coalesce(mai.tc,1) as amount_retention_me
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
				date_from = self.period_from_id.date_start.strftime('%Y/%m/%d'),
				date_to = self.period_to_id.date_end.strftime('%Y/%m/%d'),
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
	
	def get_excel_report(self):

		import io
		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell

		ReportBase = self.env['report.base']
		param = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		direccion = param.dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Transvial_Report_Retention.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		for y in ['especial1','numberpercent','dateformat','numberdos','numbercuatro']:
			formats[y].set_font_name('Calibri')
			formats[y].set_border(style=0)
			formats[y].set_font_size(10)

		centered = workbook.add_format({'bold': True})
		centered.set_align('center')
		centered.set_align('vcenter')
		centered.set_text_wrap()
		centered.set_font_size(10)
		centered.set_font_name('Calibri')

		subtitle_center = workbook.add_format({'bold': True})
		subtitle_center.set_align('center')
		subtitle_center.set_align('vcenter')
		subtitle_center.set_text_wrap()
		subtitle_center.set_border(style=1)
		subtitle_center.set_font_size(10)
		subtitle_center.set_bg_color('#AEAAAA')
		subtitle_center.set_font_name('Calibri')

		right_title = workbook.add_format({'bold': True})
		right_title.set_align('right')
		right_title.set_align('vcenter')
		right_title.set_text_wrap()
		right_title.set_font_size(10)
		right_title.set_font_name('Calibri')
		
		left_title = workbook.add_format({'bold': True})
		left_title.set_align('left')
		left_title.set_align('vcenter')
		left_title.set_text_wrap()
		left_title.set_font_size(10)
		left_title.set_font_name('Calibri')

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Reporte Retenciones")
		worksheet.set_tab_color('blue')

		today = fields.Datetime.context_timestamp(self, datetime.now())

		worksheet.merge_range('A1:B1', self.company_id.name, left_title)
		worksheet.merge_range('A2:B2', 'RUC: %s' % self.company_id.partner_id.vat, left_title)
		worksheet.merge_range('A3:O3', u'REGISTRO DE RETENCIONES', centered)
		worksheet.merge_range('A4:O4', u'DE %s A %s'%(self.period_from_id.name,self.period_to_id.name), centered)
		worksheet.merge_range('N1:O1', 'Pag.1 de 1', right_title)
		worksheet.merge_range('N2:O2', '%s' % today.strftime('%d/%m/%Y %H:%M:%S'), right_title)

		worksheet.merge_range('A6:B7','RETENCION',subtitle_center)
		worksheet.merge_range('C6:C7','AUXILIAR',subtitle_center)
		worksheet.merge_range('D6:D7','RUC',subtitle_center)
		worksheet.merge_range('E6:E7','MONEDA DEL DOCUMENTO',subtitle_center)
		worksheet.merge_range('F6:H7',u'N° DOCUMENTO',subtitle_center)
		worksheet.merge_range('I6:I7','FECHA',subtitle_center)
		worksheet.merge_range('J6:J7','FECHA PAGO',subtitle_center)
		worksheet.merge_range('K6:K7','TC',subtitle_center)
		worksheet.merge_range('L6:L7','TOTAL',subtitle_center)
		worksheet.merge_range('M6:M7',u'PORCENT.',subtitle_center)
		worksheet.merge_range('N6:N7',u'RETENCION S/.',subtitle_center)
		worksheet.merge_range('O6:O7',u'RETENCION $',subtitle_center)

		self._cr.execute(self.get_sql())
		data = self._cr.dictfetchall()

		x=7

		for line in data:
			worksheet.write(x,0,line['name'] if line['name'] else '',formats['especial1'])
			worksheet.write(x,1,line['date'] if line['date'] else '',formats['dateformat'])
			worksheet.write(x,2,line['partner'] if line['partner'] else '',formats['especial1'])
			worksheet.write(x,3,line['ruc'] if line['ruc'] else '',formats['especial1'])
			worksheet.write(x,4,line['moneda'] if line['moneda'] else '',formats['especial1'])
			worksheet.write(x,5,line['td'] if line['td'] else '',formats['especial1'])
			worksheet.write(x,6,line['serie'] if line['serie'] else '',formats['especial1'])
			worksheet.write(x,7,line['numero'] if line['numero'] else '',formats['especial1'])
			worksheet.write(x,8,line['invoice_date'] if line['invoice_date'] else '',formats['dateformat'])
			worksheet.write(x,9,line['payment_date'] if line['payment_date'] else '',formats['dateformat'])
			worksheet.write(x,10,line['tc'] if line['tc'] else 0,formats['numbercuatro'])
			worksheet.write(x,11,line['amount_total_signed'] if line['amount_total_signed'] else '',formats['numberdos'])
			worksheet.write(x,12,line['percentage'] if line['percentage'] else 0,formats['numberpercent'])
			worksheet.write(x,13,line['amount_retention'] if line['amount_retention'] else 0,formats['numberdos'])
			worksheet.write(x,14,line['amount_retention_me'] if line['amount_retention_me'] else 0,formats['numberdos'])
			x+=1

		widths = [14,16,40,12,11,4,7,11,11,11,11,11,11,12,11]
		worksheet = ReportBase.resize_cells(worksheet,widths)

		
		workbook.close()
		f = open(direccion +'Transvial_Report_Retention.xlsx', 'rb')
		return self.env['popup.it'].get_file('Reporte Retenciones.xlsx',base64.encodebytes(b''.join(f.readlines())))
		
	def get_pdf_report(self):
		import importlib
		import sys
		importlib.reload(sys)

		today = fields.Datetime.context_timestamp(self, datetime.now())

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths,pagina):
			c.setFont("Helvetica-Bold", 11)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "REGISTRO DE RETENCIONES")
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-12, particionar_text( self.company_id.name,90))
			c.drawString(30,hReal-32,'RUC: %s' % self.company_id.partner_id.vat)
			c.drawRightString(wReal-30,hReal-12, 'Pag. %d'%pagina)
			c.drawRightString(wReal-30,hReal-32,'%s' % today.strftime('%d/%m/%Y %H:%M:%S'))


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>RETENCION</b></font>",style), '',
				Paragraph("<font size=8><b>AUXILIAR</b></font>",style), 
				Paragraph("<font size=8><b>RUC</b></font>",style), 
				Paragraph("<font size=8><b>MONEDA</b></font>",style),
				Paragraph(u"<font size=8><b>N° DOCUMENTO</b></font>",style),'','',
				Paragraph(u"<font size=8><b>FECHA</b></font>",style),
				Paragraph(u"<font size=8><b>FECHA PAGO</b></font>",style),
				Paragraph(u"<font size=8><b>TC</b></font>",style),
				Paragraph(u"<font size=8><b>TOTAL</b></font>",style),
				Paragraph(u"<font size=8><b>PORCENT.</b></font>",style),
				Paragraph(u"<font size=8><b>RETENCION S/.</b></font>",style),
				Paragraph(u"<font size=8><b>RETENCION $</b></font>",style),
				]]
			t=Table(data,colWidths=size_widths, rowHeights=(20))
			color_cab = colors.Color(red=(174/255),green=(170/255),blue=(170/255))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,0)),
				('SPAN',(5,0),(7,0)),
				('BACKGROUND', (0, 0), (14, 0),color_cab),
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-60)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths,pagina)
				return pagina+1,hReal-117
			else:
				return pagina,posactual-valor

		width ,height  = 842, 595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "reporte_retencion.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (width ,height) )
		pos_inicial = hReal-60
		pagina = 1

		size_widths = [55,45,155,50,55,10,20,45,45,45,25,50,55,65,65]

		pdf_header(self,c,wReal,hReal,size_widths,pagina)

		c.setFont("Helvetica", 8)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(self.get_sql())
		res = self.env.cr.dictfetchall()


		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['name'] if i['name'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,str(i['date'] if i['date'] else '') )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',150) )
			first_pos += size_widths[2]
			
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['ruc'] if i['ruc'] else '',200) )
			first_pos += size_widths[3]
			
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['moneda'] if i['moneda'] else '',200) )
			first_pos += size_widths[4]
			
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td'] if i['td'] else '',200) )
			first_pos += size_widths[5]
			
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['serie'] if i['serie'] else '',200) )
			first_pos += size_widths[6]
			
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['numero'] if i['numero'] else '',200) )
			first_pos += size_widths[7]
			
			c.drawString( first_pos+2 ,pos_inicial,str(i['invoice_date'] if i['invoice_date'] else '') )
			first_pos += size_widths[8]
			
			c.drawString( first_pos+2 ,pos_inicial, str(i['payment_date'] if i['payment_date'] else ''))
			first_pos += size_widths[9]

			c.drawRightString( first_pos+size_widths[10] ,pos_inicial,'{:,.4f}'.format(decimal.Decimal ("%0.4f" % i['tc'])) )
			first_pos += size_widths[10]

			c.drawRightString( first_pos+size_widths[11] ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['amount_total_signed'])) )
			first_pos += size_widths[11]

			c.drawRightString( first_pos+size_widths[12] ,pos_inicial,'{:,.2f}%'.format(decimal.Decimal ("%0.2f" % i['percentage'])) )
			first_pos += size_widths[12]

			c.drawRightString( first_pos+size_widths[13] ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['amount_retention'])))
			first_pos += size_widths[13]

			c.drawRightString( first_pos+size_widths[14] ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['amount_retention_me'])))

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('INFORME DE RETENCIONES.pdf',base64.encodebytes(b''.join(f.readlines())))