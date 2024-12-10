# -*- coding:utf-8 -*-
from datetime import date, datetime, time
from odoo import api, fields, models

class HrContract(models.Model):
	_inherit = 'hr.contract'

	is_overtime = fields.Boolean(string='Calcular Horas Extras', default=False)

	work_entry_source = fields.Selection(
        selection_add=[('attendance', 'Asistencias')],
        ondelete={'attendance': 'set default'},
    )