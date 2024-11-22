# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'
	
	type_operation_outproduction = fields.Many2one('type.operation.kardex', string=u'Consumo de Producción')
	type_operation_inproduction = fields.Many2one('type.operation.kardex', string=u'Ingreso de Producción')
	type_operation_gv = fields.Many2one('type.operation.kardex', string=u'Gasto Vinculado')

	in_operation_type_ids = fields.Many2many('type.operation.kardex', 'in_type_operation_kardex_warehouse_parameter_rel', string=u'Tipo de Operación Ingresos')
	out_operation_type_ids = fields.Many2many('type.operation.kardex', 'out_type_operation_kardex_warehouse_parameter_rel', string=u'Tipo de Operación Salidas')