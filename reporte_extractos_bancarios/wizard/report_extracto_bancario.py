from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from datetime import datetime, timedelta
from io import BytesIO
import re
import uuid

class report_extracto_bancario(models.TransientModel):
	_name = 'report.extracto.bancario'

	name = fields.Char()

	company_id = fields.Many2one(
		'res.company',
		string=u'Compañia',
		required=True, 
		default=lambda self: self.env.company,
		readonly=True
	)
	
	date_from = fields.Date(
		string=u'Fecha Inicial',
		
	)

	date_to = fields.Date(
		string=u'Fecha Final',
		
	)

	journal_id = fields.Many2one(
		'account.journal',
		string='Diario',
		domain="[('id','in', journal_domain_ids)]"
	)

	journal_type = fields.Selection([
		('bank', 'Banco'),
		('cash', 'Caja'),
		('surrender', 'Rendiciones')
	],string="Tipo", help="Campo utilizado para elegir tipo de diario")
	
	journal_domain_ids = fields.Many2many(
		"account.journal",
		compute="get_diarios_domains",
	)

	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF')],string=u'Mostrar en',default='excel')
	
	statement_id = fields.Many2one('account.bank.statement', string='Exracto',domain="[('journal_id','=', journal_id)]" )

	@api.onchange('journal_type')
	@api.depends('journal_type')
	def get_diarios_domains(self):
		for record in self:    
			diarios = self.env['account.journal']
			journals = []
			if record.journal_type=="bank":
						journals = self.env['account.journal'].search([('type','=',str(record.journal_type))])
			if record.journal_type=="cash":
						journals = self.env['account.journal'].search([('type','=',str(record.journal_type))]).filtered(lambda l: not l.check_surrender)    
			if record.journal_type=="surrender":
						journals = self.env['account.journal'].search([('type','=',str('cash')),('check_surrender','=',True)])			
			for journal in journals:									
				diarios |= journal
			record.journal_domain_ids = [(6, 0, diarios.ids)]

	def get_report(self):
		for i in self:
			if i.type_show == 'excel':
				return i.get_excel()
			if i.type_show == 'pantalla':
				self.env.cr.execute("""
				DROP VIEW IF EXISTS account_statement_view;
				CREATE OR REPLACE view account_statement_view as (SELECT row_number() OVER () AS id, T.* FROM ("""+self._get_sql()+""")T)""")

				return {
					'name': 'Extracto',
					'type': 'ir.actions.act_window',
					'res_model': 'account.statement.view',
					'view_mode': 'tree',
					#'view_type': 'tree',
				}
			if i.type_show == 'pdf':
				return i.get_pdf()

	def get_pdf(self):
		for i in self:
			return i.env.ref('reporte_extractos_bancarios.action_report_statement_it').report_action(i)

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Extractos_Bancarios.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("EXTRACTOS BANCARIOS")
		worksheet.set_tab_color('blue')

		formats['numberdosespecial'].set_num_format('"%s" #,##0.00' % self.statement_id.currency_id.symbol)
		formats['numberdos'].set_num_format('"%s" #,##0.00' % self.statement_id.currency_id.symbol)

		if self.statement_id.journal_id.type == 'bank':
			name_rep = 'EXTRACTO BANCARIO'
		elif self.statement_id.journal_id.type == 'cash' and self.statement_id.journal_check_surrender:
			name_rep ='RENDICIONES'
		else:
			name_rep ='CAJA CHICA'


		worksheet.merge_range(1,0,1,5, name_rep, formats['especial4'])

		worksheet.write(3,0, "Diario:", formats['especial2'])
		worksheet.write(4,0, "Fecha:", formats['especial2'])
		worksheet.write(3,2, "Saldo Inicial:", formats['especial2'])

		worksheet.write(3,1, self.statement_id.journal_id.name, formats['especial4'])
		worksheet.write(4,1, self.statement_id.date, formats['especialdate'])
		worksheet.write_number(3,3, self.statement_id.balance_start , formats['numberdosespecial'])

		HEADERS = ['FECHA','DESCRIPCION','PARTNER','TD','REFERENCIA','MEDIO DE PAGO','MONTO','CONCILIADO']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,6,0,formats['boldbord'])

		x=7
		tot = 0

		for line in self.statement_id.line_ids:
			worksheet.write(x,0,line.date if line.date else '',formats['dateformat'])
			worksheet.write(x,1,line.payment_ref if line.payment_ref else '',formats['especial1'])
			worksheet.write(x,2,line.partner_id.name if line.partner_id else '',formats['especial1'])
			worksheet.write(x,3,line.type_document_id.code if line.type_document_id else '',formats['especial1'])
			worksheet.write(x,4,line.ref if line.ref else '',formats['especial1'])
			worksheet.write(x,5,line.catalog_payment_id.code if line.catalog_payment_id else '',formats['especial1'])
			worksheet.write(x,6,line.amount if line.amount else '0.00',formats['numberdos'])
			worksheet.write(x,7,'SI' if line.is_reconciled else 'NO',formats['especial1'])
			tot += line.amount if line.amount else 0
			x += 1

		worksheet.write(x+1,1, 'SALDO', formats['especial5'])
		worksheet.write(x+1,6, tot+self.statement_id.balance_start, formats['numberdosespecialbold'])

		widths = [10,50,46,10,23,20,15,18]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Extractos_Bancarios.xlsx', 'rb')

		return self.env['popup.it'].get_file('%s.xlsx'%(name_rep),base64.encodebytes(b''.join(f.readlines())))


	

	def _get_sql(self):
		
		sql = """SELECT am.date,
						abs.balance_start,
						abs.balance_end_real,  
						absl.payment_ref as des, 
						rp.name as partner, 
						ldt.code as td,
						am.nro_comp  as ref, 
						ecp.name as catalog_payment,
						absl.amount, 
						absl.is_reconciled as reconcile
					FROM account_bank_statement_line as absl
					LEFT JOIN res_partner rp ON rp.id = absl.partner_id
					LEFT JOIN l10n_latam_document_type ldt ON ldt.id = absl.type_document_id
					LEFT JOIN einvoice_catalog_payment ecp ON ecp.id = absl.catalog_payment_id
					LEFT JOIN account_bank_statement abs ON abs.id = absl.statement_id
					LEFT JOIN account_move am ON am.id = absl.move_id
					WHERE 	abs.company_id = %d
							AND abs.journal_id = %d
							AND abs.id = %d
				""" % (							
						self.company_id.id,
						self.journal_id.id,
						self.statement_id.id)
		
		return sql
