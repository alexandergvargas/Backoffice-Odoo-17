# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class ResPartnerBank(models.Model):
	_inherit = 'res.partner.bank'

	#type_bank = fields.Selection([('001','001 Corriente'),('002','002 Ahorros'),('007','007 CTS')],string='Tipo de Cuenta',default='001')
	partner_bank_type_catalog_id = fields.Many2one('partner.bank.type.catalog',string='Tipo de Cuenta')
	cci = fields.Char(string='CCI')