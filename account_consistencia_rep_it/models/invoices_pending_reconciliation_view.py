# -*- coding: utf-8 -*-

from odoo import models, fields, api

class InvoicesPendingReconciliationView(models.Model):
	_name = 'invoices.pending.reconciliation.view'
	_description = 'Invoices Pending Reconciliation View'
	_auto = False
	
	fecha = fields.Date(string='Fecha')
	libro = fields.Char(string='Libro')
	partner = fields.Char(string='Partner')
	td = fields.Char(string='TD')
	nro_comprobante = fields.Char(string=u'Nro Comp')
	amount = fields.Float(string='Monto', digits=(64,2))