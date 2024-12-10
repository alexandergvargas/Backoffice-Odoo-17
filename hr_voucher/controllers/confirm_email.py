# -*- encoding: utf-8 -*-
import logging

from odoo import fields, http, _
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class Employee_Verified_mail_cts_Controller(http.Controller):

	@http.route('/payslip_line/<int:payslip_line_id>', type='http',auth='public',website=True, csrf=False)
	def verified_payslip_line(self, payslip_line_id, **kw):
		payslip = request.env['hr.payslip'].sudo().search([('id','=',payslip_line_id)])
		if not payslip.is_verified:
			payslip.is_verified = True
			payslip.date_confirmation = fields.Datetime.now()
			return request.render("hr_voucher.template_confirm_email_boleta")
		else:
			return request.render("hr_voucher.template_confirm_email_boleta_bucle")
