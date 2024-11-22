# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class FormatBankIt(models.Model):
	_name = 'format.bank.it'

	name = fields.Char(string='Banco',required=True)