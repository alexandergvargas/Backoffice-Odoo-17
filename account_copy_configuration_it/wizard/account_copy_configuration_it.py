# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class AccountCopyConfigurationIt(models.TransientModel):
	_name = "account.copy.configuration.it"

	model_company_id = fields.Many2one('res.company',string=u'Compañía Modelo')
	copy_account = fields.Boolean(string='Plan Contable',default=False)
	copy_journal = fields.Boolean(string='Diarios',default=False)
	copy_tax = fields.Boolean(string='Impuestos',default=False)
	copy_analytic = fields.Boolean(string='Cuentas Analíticas',default=False)

	def copy_account_data(self):

		if self.model_company_id.chart_template != self.env.company.chart_template:
			raise UserError(u'Las compañía "%s" no tiene el mismo Paquete Contable que la compañía "%s", revise su Configuración.'%(self.env.company.name,self.model_company_id.name))
		self.env.cr.execute("""SELECT COUNT(id) as data FROM account_move_line where company_id = %s""" % (str(self.env.company.id)))
		data = self.env.cr.fetchall()
		if data[0][0] > 0:
			raise UserError(u'Si ya existe data en esta Compañía no puede usar este utilitario!')
		if self.copy_account:
			self.copy_account_def()

		if self.copy_journal:
			self.copy_journal_def()

		if self.copy_tax:
			self.copy_tax_def()

		if self.copy_analytic:
			self.copy_analytic_def()
		
		return self.env['popup.it'].get_message('SE COPIARON LAS CONFIGURACIONES CONTABLES DE MANERA CORRECTA.')

	def copy_account_def(self):
		account_obj = self.env['account.account']
		group_obj = self.env['account.group']

		#SE ELIMINAN LOS ANTIGUOS GRUPOS
		last_groups = group_obj.search([('company_id','=',self.env.company.id)])
		last_groups.unlink()

		#SE CREAN LOS GRUPOS PARA LAS NUEVAS CUENTAS
		groups = group_obj.sudo().search([('company_id','=',self.model_company_id.id)])
		for group in groups:
			data = {
				'parent_id': group_obj.search([('code_prefix_start','=',group.parent_id.code_prefix_start),('code_prefix_end','=',group.parent_id.code_prefix_end),('company_id','=',self.env.company.id)],limit=1).id if group.parent_id else None,
				'parent_path': group.parent_path,
				'name': group.name,
				'code_prefix_start': group.code_prefix_start,
				'code_prefix_end': group.code_prefix_end,
			}
			group_obj.create(data)
		
		#SE ARCHIVAN LAS CUENTAS
		last_accounts = account_obj.search([('company_id','=',self.env.company.id),('deprecated','=',False)])
		last_accounts.write({'deprecated':True})

		#SE CONFIGURAN NUEVAS CUENTAS EN BASE AL OTRO PC
		accounts = account_obj.sudo().search([('company_id','=',self.model_company_id.id),('deprecated','=',False)],order='account_close_id')
		for account in accounts:
			search_account = account_obj.search([('code','=',account.code),('company_id','=',self.env.company.id)],limit=1)
			data = {
				'code' : account.code,
				'name' : account.name,
				'account_type':account.account_type,
				#'tax_ids':[(6,0,[y.id for y in account.tax_ids])]if account.tax_ids else False,	
				'tag_ids':[(6,0,[x.id for x in account.tag_ids])]if account.tag_ids else False,
				'currency_id':account.currency_id.id,
				'reconcile':account.reconcile,
				'deprecated':account.deprecated,
				'account_type_it_id':account.account_type_it_id.id,
				'm_close':account.m_close,
				'account_close_id':account_obj.search([('code','=',account.account_close_id.code),('company_id','=',self.env.company.id)],limit=1).id if account.account_close_id else None,
				'account_type_cash_id':account.account_type_cash_id.id,
				'check_moorage':account.check_moorage,
				'a_debit':account_obj.search([('code','=',account.a_debit.code),('company_id','=',self.env.company.id)],limit=1).id if account.a_debit else None,
				'a_credit':account_obj.search([('code','=',account.a_credit.code),('company_id','=',self.env.company.id)],limit=1).id if account.a_credit else None,
				'is_document_an':account.is_document_an,
				'clasification_sheet':account.clasification_sheet,
				'code_sunat':account.code_sunat,
				}
			if not search_account:
				account_obj.create(data)
			else:
				search_account.write(data)
	
	def copy_journal_def(self):
		journal_obj = self.env['account.journal']
		journals = journal_obj.sudo().search([('company_id','=',self.model_company_id.id)])
		for journal in journals:
			search_journal = journal_obj.search([('code','=',journal.code),('company_id','=',self.env.company.id)],limit=1)
			data = {
				'code' : journal.code,
				'name' : journal.name,
				'type':journal.type,
				'default_account_id':self.env['account.account'].search([('code','=',journal.default_account_id.code),('company_id','=',self.env.company.id)],limit=1).id,
				'refund_sequence': journal.refund_sequence,
				'currency_id':journal.currency_id.id,
				'restrict_mode_hash_table': journal.restrict_mode_hash_table,
				'register_sunat': journal.register_sunat,
				'voucher_edit': journal.voucher_edit,
				'check_surrender': journal.check_surrender,
				'check_retention': journal.check_retention,
				'account_multipayment_id':self.env['account.account'].search([('code','=',journal.account_multipayment_id.code),('company_id','=',self.env.company.id)],limit=1).id if journal.account_multipayment_id else None,
				'multipayment_precentage': journal.multipayment_precentage
				}
			if not search_journal:
				journal_obj.create(data)
			else:
				search_journal.write(data)
	
	def copy_tax_def(self):
		if not self.env.company.country_id:
			raise UserError(u'Falta configurar País en su Compañía para crear sus impuestos.')
		tax_obj = self.env['account.tax']
		tax_group_obj = self.env['account.tax.group']
		account_obj = self.env['account.account']

		pf = self.env['account.fiscal.position'].search([('company_id','=',self.env.company.id)])
		pf.unlink()

		last_taxes = tax_obj.search([('company_id','=',self.env.company.id)])
		last_taxes.unlink()

		last_groups = tax_group_obj.search([('company_id','=',self.env.company.id)])
		last_groups.unlink()

		groups = tax_group_obj.sudo().search([('company_id','=',self.model_company_id.id)])

		for group in groups:
			data = {
				'name': group.name,
				'country_id': self.env.company.country_id.id,
				'company_id': self.env.company.id,
			}
			tax_group_obj.create(data)

		taxes = tax_obj.sudo().search([('company_id','=',self.model_company_id.id)])

		for tax in taxes:
			data = {
				'name': tax.name,
				'type_tax_use': tax.type_tax_use,
				'amount_type': tax.amount_type,
				'active': tax.active,
				'company_id': self.env.company.id,
				'country_id': self.env.company.country_id.id,
				'sequence': tax.sequence,
				'amount': tax.amount,
				'description': tax.description,
				'price_include':tax.price_include,
				'include_base_amount':tax.include_base_amount,
				'tax_group_id': tax_group_obj.search([('name','=',tax.tax_group_id.name),('company_id','=',self.env.company.id)], limit=1).id,
				'tax_exigibility':tax.tax_exigibility,
				'invoice_repartition_line_ids': [
					(0, 0, { 'repartition_type': tax.invoice_repartition_line_ids[0].repartition_type, 
							'factor_percent': tax.invoice_repartition_line_ids[0].factor_percent,
							'company_id': self.env.company.id, 
							'tag_ids': [(6,0,[y.id for y in tax.invoice_repartition_line_ids[0].tag_ids])]if tax.invoice_repartition_line_ids[0].tag_ids else False}), 
					(0, 0, { 'repartition_type': tax.invoice_repartition_line_ids[1].repartition_type, 
							'factor_percent': tax.invoice_repartition_line_ids[1].factor_percent,
							'company_id': self.env.company.id, 
							'account_id': account_obj.search([('code','=',tax.invoice_repartition_line_ids[1].account_id.code),('company_id','=',self.env.company.id)], limit=1).id,
							'tag_ids':  [(6,0,[y.id for y in tax.invoice_repartition_line_ids[1].tag_ids])]if tax.invoice_repartition_line_ids[1].tag_ids else False}),
				],
				'refund_repartition_line_ids': [
					(0, 0, { 'repartition_type': tax.refund_repartition_line_ids[0].repartition_type, 
							'factor_percent': tax.refund_repartition_line_ids[0].factor_percent,
							'company_id': self.env.company.id, 
							'tag_ids': [(6,0,[y.id for y in tax.refund_repartition_line_ids[0].tag_ids])]if tax.refund_repartition_line_ids[0].tag_ids else False}), 
					(0, 0, { 'repartition_type': tax.refund_repartition_line_ids[1].repartition_type, 
							'factor_percent': tax.refund_repartition_line_ids[1].factor_percent,
							'company_id': self.env.company.id, 
							'account_id': account_obj.search([('code','=',tax.refund_repartition_line_ids[1].account_id.code),('company_id','=',self.env.company.id)], limit=1).id,
							'tag_ids':  [(6,0,[y.id for y in tax.refund_repartition_line_ids[1].tag_ids])]if tax.refund_repartition_line_ids[1].tag_ids else False}),
				]
			}

			tax_obj.create(data)

	def copy_analytic_def(self):
		analytic_obj = self.env['account.analytic.account']
		plan_obj = self.env['account.analytic.plan']
		account_obj = self.env['account.account']

		analytics = analytic_obj.sudo().search([('company_id','=',self.model_company_id.id)])
		for analytic in analytics:
			data = {
				'name': analytic.name,
				'partner_id': analytic.partner_id.id,
				'plan_id': plan_obj.search([('name','=',analytic.plan_id.name)],limit=1).id,
				'code': analytic.code,
				'currency_id': analytic.currency_id.id,
				'a_debit':account_obj.search([('code','=',analytic.a_debit.code),('company_id','=',self.env.company.id)],limit=1).id if analytic.a_debit else None,
				'a_credit':account_obj.search([('code','=',analytic.a_credit.code),('company_id','=',self.env.company.id)],limit=1).id if analytic.a_credit else None,
			}
			analytic_obj.create(data)