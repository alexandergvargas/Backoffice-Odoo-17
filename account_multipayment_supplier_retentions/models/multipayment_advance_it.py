# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'
	
	def calculate_line(self):
		param = self.env['account.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1)
		if param.without_retention_document_type_ids:
			self.env.cr.execute("""SELECT mul.partner_id, sum(mul.debe) as sum_debe, array_agg(mul.id) as mul_ids FROM multipayment_advance_it_line mul
									LEFT JOIN multipayment_advance_it mu ON mu.id = mul.main_id
									LEFT JOIN account_move_line aml on aml.id = mul.invoice_id
									LEFT JOIN account_move am on am.id =  aml.move_id
					   				LEFT JOIN res_partner rp on rp.id = mul.partner_id
									WHERE mu.id = %d AND mul.tipo_documento in (%s) and am.linked_to_detractions <> TRUE
					   				and coalesce(rp.is_partner_retencion,FALSE) <> TRUE and coalesce(rp.is_partner_perception,FALSE) <> TRUE
					   				and coalesce(rp.good_taxpayer,FALSE) <> TRUE and coalesce(rp.executing_unit,FALSE) <> TRUE
									GROUP BY mul.partner_id
					   				HAVING sum(mul.debe) > 700"""%(self.id,",".join(str(i) for i in param.without_retention_document_type_ids.ids)))
			res = self.env.cr.dictfetchall()
			for i in res:
				for line_i in self.invoice_ids.filtered(lambda l: l.id in i['mul_ids']):
					if not param.retention_percentage:
						raise UserError(u'No tiene configurado el Porcentaje de Retención en los Parametros Principales de Contabilidad de su Compañía')
					line_i.amount_retention = line_i.debe*param.retention_percentage

		total_retention = 0
		for line_i in self.invoice_ids.filtered(lambda l: l.amount_retention != 0):
			total_retention += line_i.amount_retention
		if total_retention > 0:
			doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)
			if not param.retention_account_id:
				raise UserError(u'No tiene configurado la Cuenta de Retención en los Parametros Principales de Contabilidad de su Compañía')
			lines = self.lines_ids.filtered(lambda l: l.account_id.id == param.retention_account_id.id)
			lines.unlink()
			for line_inv in self.invoice_ids.filtered(lambda l: l.amount_retention != 0):
				val = {
					'main_id': self.id,
					'account_id': param.retention_account_id.id,
					'importe_divisa': line_inv.amount_retention*-1,
					'partner_id': line_inv.partner_id.id,
					'type_document_id': doc.id,
					'nro_comp': self.name,
					'debe': 0,
					'haber': line_inv.amount_retention,
					'fecha_vencimiento': self.payment_date,
					'name': self.glosa
				}
				self.env['multipayment.advance.it.line2'].create(val)
		mult = super(MultipaymentAdvanceIt,self).calculate_line()
		return mult

class MultipaymentAdvanceItLine(models.Model):
	_inherit = 'multipayment.advance.it.line'

	amount_retention = fields.Float(string='Retención',digits=(12,2),default=0)
	retention_id = fields.Many2one('account.retention.comp',string=u'Retención')