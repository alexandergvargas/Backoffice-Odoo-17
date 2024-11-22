# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
import time

class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'

	def action_make_wizard_order_pay_action(self):
		if not self.journal_id.bank_parameter_id:
			raise UserError(u'El Diario no tiene establecido el Formato de Banco.')
		
		wizard = self.env['make.wizard.order.pay'].create({
			'multipayment_id':self.id
		})
		return {
			'name':u'Generar',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'make.wizard.order.pay',
			'view_id': self.env.ref('pay_order_base.view_make_wizard_order_pay_form').id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def get_report_txt(self,bank_parameter):
		if not bank_parameter.format_id:
			return self.env['popup.it'].get_message('Comuniquese con su Administrador para Habilitar el Banco Requerido')
		else:
			return False
		
	def get_report_excel(self,bank_parameter):
		if not bank_parameter.format_id:
			return self.env['popup.it'].get_message('Comuniquese con su Administrador para Habilitar el Banco Requerido')
		else:
			return False

class MultipaymentAdvanceItLine(models.Model):
	_inherit = 'multipayment.advance.it.line'

	payment_type_catalog_id = fields.Many2one('payment.type.catalog',string='Tipo abono')