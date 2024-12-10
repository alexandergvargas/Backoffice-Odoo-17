# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrGratificationMoveWizard(models.TransientModel):
	_name = 'hr.gratification.move.wizard'
	_description = 'Hr Gratification Move Wizard'

	name = fields.Char()
	debit = fields.Float(string='Total Debe', readonly=False)
	credit = fields.Float(string='Total Haber', readonly=False)
	difference = fields.Float(string='Diferencia', compute='_get_difference')
	# journal_id = fields.Many2one('account.journal', string='Diario')
	account_id = fields.Many2one('account.account', string='Cuenta de Ajuste')

	@api.depends('debit', 'credit')
	def _get_difference(self):
		for record in self:
			record.difference = abs(record.debit - record.credit)

	def generate_move(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.type_doc_pla.id:
			raise UserError('No se ha configurado el tipo de comprobante para Planilla')
		if not MainParameter.partner_id.id:
			raise UserError('No se ha configurado un partner para Planilla')
		grati = self.env['hr.gratification'].browse(self._context.get('gratification_id'))
		# if grati.state=='draft':
		# 	raise UserError('Primero tiene que exportar el calculo de la gratificacion')
		PR = grati.payslip_run_id
		# print("PR",PR)
		extra_line = {}
		if self.debit > self.credit:
			extra_line = {
				'account_id': self.account_id.id,
				'debit': 0,
				'credit': self.difference,
				'type_document_id' : MainParameter.type_doc_pla.id,
				'nro_comp' : None,
				'description': 'Ajuste por Redondeo',
				'partner_id': MainParameter.partner_id.id}
		if self.credit > self.debit:
			extra_line = {
				'account_id': self.account_id.id,
				'debit': self.difference,
				'credit': 0,
				'type_document_id' : MainParameter.type_doc_pla.id,
				'nro_comp' : None,
				'description': 'Ajuste por Redondeo',
				'partner_id': MainParameter.partner_id.id}

		move_lines = self._context.get('move_lines')
		if extra_line:
			move_lines.append(extra_line)
		# print("move_lines",move_lines)
		move = self.env['account.move'].create({
			'journal_id': MainParameter.journal_id.id,
			'date': grati.deposit_date,
			'ref': 'GRA'+(PR.periodo_id.code).replace("-", ""),
			'glosa': 'GRATIFICACION %s' %(PR.name),
			'line_ids': [(0, 0, {
					'account_id': line['account_id'],
					'debit': line['debit'],
					'credit': line['credit'],
					'type_document_id' : MainParameter.type_doc_pla.id,
					'nro_comp' : 'GRA'+(PR.periodo_id.code).replace("-", ""),
					'name': line['description'] if line['description'] else None,
					'partner_id': line['partner_id'] if line['partner_id'] is not None else MainParameter.partner_id.id,
					'analytic_distribution': {line['analytic_account_id']: 100} if 'analytic_account_id' in line and line['analytic_account_id'] else None
				}) for line in move_lines
			]
		})
		move.action_post()
		grati.account_move_id = move.id
		return self.env['popup.it'].get_message('Generacion de Asiento Exitosa')