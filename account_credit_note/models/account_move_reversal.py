# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError

class AccountMoveReversal(models.TransientModel):
	_inherit = 'account.move.reversal'

	l10n_latam_document_type_id = fields.Many2one(change_default=True)
	type_document_id = fields.Many2one('l10n_latam.document.type',string='T.D.',store=True)
	serie_id = fields.Many2one('it.invoice.serie',string='Serie',copy=False)
	nro_comp = fields.Char(string=u'Número Comprobante',size=20,copy=False)

	@api.onchange('move_ids')
	def get_td_nc(self):
		credit_note = self.env['account.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1).dt_national_credit_note
		for rev in self:
			rev.type_document_id = credit_note.id or None
	
	@api.onchange('nro_comp')
	def onchange_comp(self):
		for i in self:
			i.nro_comp = i.type_document_id._get_ref(i.nro_comp)

	@api.onchange('serie_id')
	def onchange_serie_id(self):
		for i in self:
			if i.serie_id:
				next_number = i.serie_id.sequence_id.number_next_actual
				if not i.serie_id.sequence_id.prefix:
					raise UserError("No existe un prefijo configurado en la secuencia de la serie.")
				prefix = i.serie_id.sequence_id.prefix
				padding = i.serie_id.sequence_id.padding
				i.nro_comp = prefix + "0"*(padding - len(str(next_number))) + str(next_number)

	def _prepare_default_reversal(self, move):
		res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
		credit_note = self.env['account.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1).dt_national_credit_note
		
		res.update({
                'l10n_latam_document_number': '',
                'serie_id': self.serie_id.id,
                'nro_comp': self.nro_comp,
				'currency_rate':  move.currency_rate,
				'glosa': self.reason or ('Anulacion de '+(move.glosa or '')),
				'l10n_latam_document_type_id': (credit_note.id or None),
				'tc_per':True
            })
		res['doc_invoice_relac'] = [(0, 0, {'type_document_id': move.l10n_latam_document_type_id.id,
											  'date': move.invoice_date,
											  'nro_comprobante': move.nro_comp,
											  'amount_currency': move.amount_total if move.currency_id.name != 'PEN' else 0,
											  'amount': abs(move.amount_total_signed)}
											)]
		return res
	
	
	def reverse_moves(self, is_modify=False):
		res= super(AccountMoveReversal,self).reverse_moves(is_modify)
		credit_note = self.env['account.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1).dt_national_credit_note
		
		move = self.env['account.move'].search([('id', '=',str(res['res_id']) )], limit=1)
		move.serie_id = self.serie_id.id
		move.nro_comp = self.nro_comp
		move.tc_per = True
		move.l10n_latam_document_type_id = (credit_note.id or None),
		move.glosa = (self.reason or '')
		move.line_ids.type_document_id = None
		move.line_ids.nro_comp = None
		#move._get_currency_rate()
		move._onchange_currency_rate()
		
		return res