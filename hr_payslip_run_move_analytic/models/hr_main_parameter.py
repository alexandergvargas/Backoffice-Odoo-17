# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	# provision_journal_id = fields.Many2one('account.journal', string='Diario')
	# type_doc_prov = fields.Many2one('einvoice.catalog.01', string=u'Tipo de documento para asiento provisión')
	# detallar_provision = fields.Boolean(string="Detallar por Trabajador", default=True)

	# gratification_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Gratificaciones')
	bonification_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Bono Extraordinario')
	cts_sr_id = fields.Many2one('hr.salary.rule', string='R. S. CTS')
	vacation_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Vacaciones')