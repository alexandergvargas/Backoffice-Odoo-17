# -*- coding: utf-8 -*-

from odoo import models, fields, api

class UnbalancedAccountingEntriesView(models.Model):
	_name = 'unbalanced.accounting.entries.view'
	_description = 'Unbalanced Accounting Entries View'
	_auto = False
	
	fecha = fields.Date(string='Fecha')
	libro = fields.Char(string='Libro')
	partner = fields.Char(string='Partner')
	td = fields.Char(string='TD')
	nro_comprobante = fields.Char(string=u'Nro Comp')
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
	diferencia = fields.Float(string='Diferencia', digits=(12,2))