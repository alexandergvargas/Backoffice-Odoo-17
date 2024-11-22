# -*- coding: utf-8 -*-

from odoo import models, fields, api

class InvoicesWithDifferentRateView(models.Model):
	_name = 'invoices.with.different.rate.view'
	_description = 'Invoices With Different Rate View'
	_auto = False
	
	fecha = fields.Date(string='Fecha')
	libro = fields.Char(string='Libro')
	partner = fields.Char(string='Partner')
	td = fields.Char(string='TD')
	nro_comprobante = fields.Char(string=u'Nro Comp')
	amount = fields.Float(string='Monto', digits=(64,2))