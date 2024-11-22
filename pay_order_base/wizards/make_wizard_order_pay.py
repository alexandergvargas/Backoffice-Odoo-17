# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class MakeWizardOrderPay(models.TransientModel):
	_name = 'make.wizard.order.pay'

	multipayment_id = fields.Many2one('multipayment.advance.it',string=u'Pago Múltiple')
	format_type = fields.Selection([('txt','TXT'),('excel','Excel')],string='Formato',default='txt')

	def send_to_order(self):
		if self.format_type == 'txt':
			return self.multipayment_id.get_report_txt(self.multipayment_id.journal_id.bank_parameter_id)
		else:
			return self.multipayment_id.get_report_excel(self.multipayment_id.journal_id.bank_parameter_id)