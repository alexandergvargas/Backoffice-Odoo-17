# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	sequence_number_it = fields.Char(string='Backup Number')

	@api.onchange('serie_id')
	def onchange_serie_id(self):
		for i in self:
			if not i.vou_number or i.vou_number == '/':
				if i.serie_id:
					next_number = i.serie_id.sequence_id.number_next_actual
					if not i.serie_id.sequence_id.prefix:
						raise UserError("No existe un prefijo configurado en la secuencia de la serie.")
					prefix = i.serie_id.sequence_id.prefix
					padding = i.serie_id.sequence_id.padding
					i.nro_comp = prefix + "0"*(padding - len(str(next_number))) + str(next_number)

	def action_post(self):
		for i in self:			
			res = super(AccountMove,i).action_post()
			if i.move_type != 'entry':
				name = i.vou_number
				if (i.sequence_number_it != i.nro_comp):
					if i.serie_id.sequence_id:
						if not i.serie_id.sequence_id.prefix:
							raise UserError("No existe un prefijo configurado en la secuencia de la serie.")
						sequence = i.serie_id.sequence_id
						next_number =sequence.number_next_actual
						serie = str(next_number).rjust(sequence.padding, '0')
						serie = (sequence.prefix or '') + serie + (sequence.suffix or '')
						name = serie

						sequence.number_next_actual = next_number + i.serie_id.sequence_id.number_increment
						i.nro_comp = name
						i.sequence_number_it = name
			return res


