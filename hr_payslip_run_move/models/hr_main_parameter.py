# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	type_doc_pla = fields.Many2one('l10n_latam.document.type', string='T.D. para Asiento Planilla')
	partner_id = fields.Many2one('res.partner', string='Partner para Planillas')
	journal_id = fields.Many2one('account.journal', string='Diario Contable')
