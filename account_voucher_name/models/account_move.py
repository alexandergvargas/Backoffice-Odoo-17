# -*- coding: utf-8 -*-
from odoo import models, fields, api, _ 
from odoo.exceptions import UserError, ValidationError
from odoo.tools import (format_date)
from textwrap import shorten

periods = {'00':'opening',
		   '01':'january',
		   '02':'february',
		   '03':'march',
		   '04':'april',
		   '05':'may',
		   '06':'june',
		   '07':'july',
		   '08':'august',
		   '09':'september',
		   '10':'october',
		   '11':'november',
		   '12':'december',
		   '13':'closing'}

def get_period(account_date,is_opening_close):
		if is_opening_close and account_date.strftime('%m%d') == '0101':
			return '00'
		elif is_opening_close and account_date.strftime('%m%d') == '1231':
			return '13'
		else:
			return account_date.strftime('%m')
		
def lpad(s, length, char=' '):
		padding = char * (length - len(s))
		return padding + s
class AccountMove(models.Model):
	_inherit = 'account.move'

	vou_number = fields.Char(string='Voucher',default='/',copy=False)
	name = fields.Char(compute="_compute_name",inverse='_set_name_it')
	
	def action_change_name_it(self):
		for move in self:
			if move.state == 'draft':
				move.vou_number = '/'
				move.posted_before = False
				move.name = '/'
			else:
				raise UserError("No puede alterar el voucher si no se encuentra en estado Borrador")

		return self.env['popup.it'].get_message('Se borro correctamente la secuencia.')
		
	def _post(self, soft=True):
		for move in self:
			if move.vou_number == '/':
				reg = self.env['account.journal.sequence'].search([('journal_id','=',move.journal_id.id),('fiscal_year_id','=',self.env['account.fiscal.year'].search([('name','=',str(move.date.year))],limit=1).id)],limit=1)
				if not reg:
					raise UserError(u'No existe una secuencia para el diario y la fecha seleccionada.')
				seq = reg[periods[get_period(move.date,move.is_opening_close)]]
				move.vou_number = lpad(str(seq), 6, '0')
				reg.write({periods[get_period(move.date,move.is_opening_close)]: seq + 1})
			move.name = move.nro_comp if move.move_type != 'entry' else (move.date.strftime('%Y-%m-') or '') + move.vou_number
		res = super(AccountMove,self)._post(soft=soft)
		return res
	

	def check_move_sequence_chain(self):
		return self.filtered(lambda move: move.vou_number != '/')._is_end_of_seq_chain()

	@api.ondelete(at_uninstall=False)
	def _unlink_forbid_parts_of_chain(self):
		""" For a user with Billing/Bookkeeper rights, when the fidu mode is deactivated,
		moves with a sequence number can only be deleted if they are the last element of a chain of sequence.
		If they are not, deleting them would create a gap. If the user really wants to do this, he still can
		explicitly empty the 'name' field of the move; but we discourage that practice.
		If a user is a Billing Administrator/Accountant or if fidu mode is activated, we show a warning,
		but they can delete the moves even if it creates a sequence gap.
		"""
		if not self._context.get('force_delete') and self.filtered(lambda move: move.vou_number != '/'):
			raise UserError(u'No puede eliminar este asiento ya que ya consumió un número de secuencia y no es el último de la cadena. Puede optar por la acción "Borrar Secuencia"')

	@api.depends('nro_comp','vou_number','state','date')
	def _compute_name(self):
		for move in self:
			move_name = '/'
			if move.state == 'posted':
				if move.move_type == 'entry':
					move_name = (move.date.strftime('%Y-%m-') or '') + move.vou_number
				else:
					move_name = move.nro_comp
			move.name = move_name
	
	def _set_name_it(self):
		pass

	def _get_move_display_name(self, show_ref=False):
		''' Helper to get the display name of an invoice depending of its type.
		:param show_ref:    A flag indicating of the display name must include or not the journal entry reference.
		:return:            A string representing the invoice.
		'''
		self.ensure_one()
		name = ''
		if self.state == 'draft':
			name += {
				'out_invoice': _('Draft Invoice'),
				'out_refund': _('Draft Credit Note'),
				'in_invoice': _('Draft Bill'),
				'in_refund': _('Draft Vendor Credit Note'),
				'out_receipt': _('Draft Sales Receipt'),
				'in_receipt': _('Draft Purchase Receipt'),
				'entry': _('Draft Entry'),
			}[self.move_type]
			name += ' '
		if self.move_type == 'entry':
			move_name = self.vou_number
		else:
			move_name = self.name
		if not move_name or move_name == '/':
			name += '(* %s)' % str(self.id)
		else:
			name += move_name
			if self.env.context.get('input_full_display_name'):
				if self.partner_id:
					name += f', {self.partner_id.name}'
				if self.date:
					name += f', {format_date(self.env, self.date)}'
		return name + (f" ({shorten(self.ref, width=50)})" if show_ref and self.ref else '')
		
	@api.constrains('vou_number', 'journal_id', 'state','date')
	def _check_unique_sequence_vou_number(self):
		moves = self.filtered(lambda move: move.state == 'posted')
		if not moves:
			return

		self.flush_model(['vou_number', 'journal_id', 'move_type', 'state'])

		# /!\ Computed stored fields are not yet inside the database.
		self._cr.execute('''
			SELECT move2.id
			FROM account_move move
			INNER JOIN account_move move2 ON
				move2.vou_number = move.vou_number
				AND move2.journal_id = move.journal_id
				AND move2.move_type = move.move_type
				AND EXTRACT (YEAR FROM move2.date) = EXTRACT (YEAR FROM move.date) 
				AND EXTRACT (MONTH FROM move2.date) = EXTRACT (MONTH FROM move.date) 
				AND move2.id != move.id
			WHERE move.id IN %s AND move2.state = 'posted'
		''', [tuple(moves.ids)])
		res = self._cr.fetchone()
		if res:
			raise ValidationError(u"El número de Asiento ya existe en el mes seleccionado para la compañía : %s"%(str(res)))