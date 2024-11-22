# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import re

class AccountMove(models.Model):
	_inherit = 'account.move'
	
	