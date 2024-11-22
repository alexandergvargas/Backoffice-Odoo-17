# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	
	def action_import_lines(self):		
		statement_id = None
		if len(self) == 1:
			statement_id = self.id
		wizard = self.env['import.statement.line.wizard'].create({'statement_id': statement_id})
		return {
			'name': _("Importador de Lineas de Extracto"),
			'type': 'ir.actions.act_window',
			'res_model': 'import.statement.line.wizard',
			'res_id': wizard.id,
			'views': [(False, 'form')],
			'target': 'new',
		}
