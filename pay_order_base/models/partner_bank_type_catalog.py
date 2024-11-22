# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PartnerBankTypeCatalog(models.Model):
	_name = 'partner.bank.type.catalog'

	name = fields.Char(string='Descripcion',required=True)