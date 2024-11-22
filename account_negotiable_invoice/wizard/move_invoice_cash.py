# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MoveInvoiceCash(models.TransientModel):
	_name = 'move.invoice.cash'
	_description = _('MoveInvoiceCash')

	name = fields.Char(_('Factura Negociable'), default="Factura Negociable")

	multipayment_advance_id = fields.Many2one(
		comodel_name='multipayment.advance.it', 
		string='Pago Multiple',
		readonly=True)
	
	account_id = fields.Many2one(
		string=_('Cuenta Negociable'),
		comodel_name='account.account',
	)

	type_document_id = fields.Many2one(
		string=_('Tipo de Documento'),
		comodel_name='l10n_latam.document.type',
	)

	def upload_invoice_in_cash(self):
		for i in self:
			i.multipayment_advance_id.lines_ids.unlink()
			i.multipayment_advance_id.write({'lines_ids': i.vals_lines_ids()})
			for line in i.multipayment_advance_id.lines_ids:
				line._update_debit_credit()
			return self.env['popup.it'].get_message(u'Facturas Negocioables Cargadas')
	#_update_debit_credit
	def vals_lines_ids(self):
		for i in self:	
			move_lines = []	
			for line in i.multipayment_advance_id.invoice_ids:						
				line_firt = (0,0,{
								'account_id': i.account_id.id,
								'partner_id': line.partner_id.id,
								'type_document_id': i.type_document_id.id,
								'currency_id': line.currency_id.id,
								'nro_comp':line.invoice_id.nro_comp,
								'importe_divisa': line.saldo,									
								'fecha_vencimiento':line.fecha_vencimiento,													
								'cta_cte_origen':True
								})				
				move_lines.append(line_firt)
			return move_lines
	def validate_fields(self):
		for i in self:
			if not i.account_id or not i.type_document_id:
				raise UserError(u"LA CUENTA ES OBLIGATORIA COMO EL TIPO DE DOCUMENTO")