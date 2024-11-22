# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountJournal(models.Model):
	_inherit = 'account.journal'

	bank_parameter_id = fields.Many2one('bank.parameter.it',string=u'Formato Banco')