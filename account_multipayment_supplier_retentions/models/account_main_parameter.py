# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'
	
	retention_account_id = fields.Many2one('account.account',string='Cuenta de Retenciones')
	retention_percentage = fields.Float(string=u'Porcentaje de Retención')
	amount_retention = fields.Float(string=u'Monto para Retención')
	without_retention_document_type_ids = fields.Many2many('l10n_latam.document.type','account_main_parameter_without_retention_document_type_rel',string=u'Tienen Retención')