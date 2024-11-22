# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
	_inherit = 'account.move'

	def _reverse_moves(self, default_values_list=None, cancel=False):
		reverse_moves = super(AccountMove, self)._reverse_moves(default_values_list, cancel)
		for c,move in enumerate(reverse_moves):
			move_origin = self[c]
			for l, line in enumerate(move.line_ids):
				line.type_document_id = move_origin.line_ids[l].type_document_id.id
				line.nro_comp = move_origin.line_ids[l].nro_comp				
		return reverse_moves


class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'
	
	def _create_exchange_difference_moves(self,exchange_diff_values_list):
		exchange_move = super(AccountMoveLine,self)._create_exchange_difference_moves(exchange_diff_values_list)
		if exchange_move:
			if exchange_move.line_ids:
				for c,line in enumerate(exchange_move.line_ids):
					if not line.type_document_id:
						line.type_document_id = self[c-1].type_document_id.id if c-1 < len(self) and self else None
					if not line.nro_comp:
						line.nro_comp = self[c-1].nro_comp if c-1 < len(self) and self else None
					exchange_move.glosa = 'ASIENTO POR DIFERENCIA DE CAMBIO %s'%(self[c-1].nro_comp if c-1 < len(self) and c-1 >= 0 else '')
					exchange_move.ref = self[c-1].nro_comp if c-1 < len(self) and c-1 >= 0 else None

		return exchange_move
	
	def copy_data(self, default=None):
		res = super(AccountMoveLine, self).copy_data(default=default)
		for line, values in zip(self, res):
			if not line.move_id.is_invoice():
				values['type_document_id'] = line.type_document_id.id
				values['nro_comp'] = line.nro_comp
			if self._context.get('include_business_fields'):
				line._copy_data_extend_business_fields(values)
		return res
	
	def _prepare_exchange_difference_move_vals(self, amounts_list, company=None, exchange_date=None, **kwargs):
		res = super(AccountMoveLine, self)._prepare_exchange_difference_move_vals(amounts_list, company=company, exchange_date=exchange_date, **kwargs)
		to_reconcile = res.get('to_reconcile', [])		
		if to_reconcile:
			aml_id = to_reconcile[0][0].id 
			aml_record = self.env['account.move.line'].browse(aml_id)  			
			nro_comp = aml_record.nro_comp
			type_document_id = aml_record.type_document_id.id
			
			for line in res['move_values']['line_ids']:
				if isinstance(line, tuple) and len(line) == 3:
					line_data = line[2]
					if not line_data.get('nro_comp') and nro_comp:
						line_data['nro_comp'] = nro_comp					
					if not line_data.get('type_document_id') and type_document_id:
						line_data['type_document_id'] = type_document_id
		return res