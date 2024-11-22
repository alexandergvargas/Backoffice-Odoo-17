# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountJournal(models.Model):
	_inherit = 'account.journal'

	check_surrender_advance = fields.Boolean(string=u'Se usa para Rendiciones Avanzadas',default=False)
	check_petty_cash_advance = fields.Boolean(string=u'Se usa para Cajas Chicas Avanzadas',default=False)