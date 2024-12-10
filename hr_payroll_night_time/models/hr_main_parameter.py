# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	# wd_atypical = fields.Many2many('hr.payslip.worked_days.type', 'wd_atypical_main_parameter_rel', 'main_parameter_id', 'wd_id', string=u'Worked Days Jornada Atípica')
	wd_atypical_hd = fields.Many2many('hr.payslip.worked_days.type', 'wd_atypical_hd_main_parameter_rel', 'main_parameter_id', 'wd_id', string=u'Worked Days Jornada Atípica Diurna')
	wd_atypical_hn = fields.Many2many('hr.payslip.worked_days.type', 'wd_atypical_hn_main_parameter_rel', 'main_parameter_id', 'wd_id', string=u'Worked Days Jornada Atípica Nocturna')