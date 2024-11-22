# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountRetentionSupplierBook(models.Model):
	_name = 'account.retention.supplier.book'
	_auto = False
	
	name = fields.Char(string=u'Retención')
	date = fields.Date(string=u'Fecha Retención')
	partner = fields.Char(string=u'Auxiliar')
	ruc = fields.Char(string=u'RUC')
	moneda = fields.Char(string=u'Moneda')
	td = fields.Char(string=u'TD')
	serie = fields.Char(string=u'Serie')
	numero = fields.Char(string=u'Número')
	invoice_date = fields.Char(string=u'Fecha Doc.')
	payment_date = fields.Char(string=u'Fecha Pago')
	tc = fields.Float(string=u'TC',digita=(12,3))
	amount_total_signed = fields.Float(string='Total', digits=(64,2))
	percentage = fields.Float(string='Porcentaje %', digits=(64,2))
	amount_retention = fields.Float(string=u'Retención S/.', digits=(64,2))
	amount_retention_me = fields.Float(string=u'Retención $', digits=(64,2))