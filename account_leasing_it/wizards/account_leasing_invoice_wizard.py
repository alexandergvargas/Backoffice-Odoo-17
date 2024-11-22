# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountLeasingInvoiceWizard(models.TransientModel):
	_name = 'account.leasing.invoice.wizard'
	_description = 'Account Leasing Invoice Wizard'

	line_id = fields.Many2one('account.leasing.it.line',string='Linea')
	type_document_id = fields.Many2one('l10n_latam.document.type',string='T.D.')
	nro_comp = fields.Char(string='Nro Comprobante',size=40)
	date = fields.Date(string='Fecha')

	@api.onchange('nro_comp','type_document_id')
	def _get_ref(self):
		for i in self:
			digits_serie = ('').join(i.type_document_id.digits_serie*['0'])
			digits_number = ('').join(i.type_document_id.digits_number*['0'])
			if i.nro_comp:
				if '-' in i.nro_comp:
					partition = i.nro_comp.split('-')
					if len(partition) == 2:
						serie = digits_serie[:-len(partition[0])] + partition[0]
						number = digits_number[:-len(partition[1])] + partition[1]
						i.nro_comp = serie + '-' + number

	def create_invoice(self):
		self.line_id.create_invoice(self.type_document_id,self.nro_comp,self.date)