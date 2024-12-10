# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

class HrReportAsientoPlanilla(models.Model):
	_name = 'hr.report.asiento.planilla'
	_description = 'Hr Report Asiento Planilla'
	_auto = False
	_order = 'partner_name,credit,glosa'

	# account_move_id = fields.Many2one('account.move', string='Asiento Contable')
	cta_code = fields.Char(string='Cuenta')
	cta_description = fields.Char(string='Descripcion Cuenta')
	debit = fields.Float(string='Debe')
	credit = fields.Float(string='Haber')
	cc_code = fields.Char(string='C. Costo')
	cc_description = fields.Char(string='Descripcion C. Costo')
	partner_vat = fields.Char(string='DNI Trabajador')
	partner_name = fields.Char(string='Nombre Trabajador')
	glosa = fields.Char(string='Glosa')