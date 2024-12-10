# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	# provision_journal_id = fields.Many2one('account.journal', string='Diario')
	# type_doc_prov = fields.Many2one('l10n_latam.document.type', string=u'Tipo de documento para asiento provisión')
	detallar_provision = fields.Boolean(string="Detallar por Trabajador", default=True)

	cts_debe = fields.Many2one('account.account',string="CTS Debe")
	cts_haber = fields.Many2one('account.account',string="CTS Haber")
	grati_debe = fields.Many2one('account.account',string="Gratificacion Debe")
	grati_haber = fields.Many2one('account.account',string="Gratificacion Haber")
	boni_debe = fields.Many2one('account.account',string="Bono Debe")
	boni_haber = fields.Many2one('account.account',string="Bono Haber")
	vaca_debe = fields.Many2one('account.account',string="Vacaciones Debe")
	vaca_haber = fields.Many2one('account.account',string="Vacaciones Haber")

