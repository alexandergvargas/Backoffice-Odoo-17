# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class ResBank(models.Model):
	_inherit = 'res.bank'

	code_bank = fields.Char(string=u'Código Banco',size=3)