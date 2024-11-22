# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import string

class L10nLatamDocumentType(models.Model):
	_inherit = 'l10n_latam.document.type'
	_order = 'code asc'

	digits_serie = fields.Integer(string='Digitos Serie')
	digits_number = fields.Integer(string='Digitos Numero')
	pse_code = fields.Char(string='Codigo de Facturador')

	internal_code_compute = fields.Char(
		string='internal_code_compute',
		compute='_compute_internal_code_compute',
		store=True
	)
	
	
	@api.depends('name','internal_code')
	def _compute_internal_code_compute(self):
		def generate_code(existing_codes, first_letter):
			for letter in string.ascii_uppercase:
				code = f"{first_letter}{letter}"
				if code not in existing_codes:
					return code
		for record in self:
			if record.name:
				first_letter = record.name[:1]
				existing_records = self.env['l10n_latam.document.type'].sudo().search([])
				existing_codes = {rec.internal_code for rec in existing_records if rec.internal_code}				
				record.internal_code_compute = generate_code(existing_codes, first_letter)
				if not record.internal_code:
					record._onchange_field()
			else:
				record.internal_code_compute = ""

	internal_code = fields.Char(string=u'Código interno',size=2,required=True)
	
	@api.onchange('internal_code_compute')
	def _onchange_field(self):
		if not self.internal_code:
			self.internal_code = self.internal_code_compute

	
	@api.depends('internal_code')
	def _compute_display_name(self):
		for rec in self:
			name = rec.name
			if rec.internal_code:
				name = f'({rec.internal_code}) {name}'
			rec.display_name = name

	@api.constrains('internal_code')
	def _check_unique_internal_code(self):
		self.env.cr.execute("""select id from l10n_latam_document_type where internal_code = '%s' and id <> %d""" % (self.internal_code,self.id))
		res = self.env.cr.dictfetchall()
		if len(res) > 0:
			raise UserError(u"Ya existen el codigo interno para '%s' en el listado de Tipos de Documento."%(self.internal_code))