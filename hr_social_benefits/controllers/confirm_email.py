# -*- encoding: utf-8 -*-
import logging

from odoo import http, _
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class Employee_Verified_mail_cts_Controller(http.Controller):

	@http.route('/cts_line/<int:cts_line_id>', type='http',auth='public',website=True, csrf=False)
	def verified_cts_line(self, cts_line_id, **kw):
		cts = request.env['hr.cts.line'].sudo().search([('id','=',cts_line_id)])
		cts.is_verified = True
		return request.render("hr_social_benefits.template_confirm_email_bbss")

class Employee_Verified_mail_grati_Controller(http.Controller):

	@http.route('/grati_line/<int:gratification_line_id>', type='http',auth='public',website=True, csrf=False)
	def verified_grat_line(self, gratification_line_id, **kw):
		grat = request.env['hr.gratification.line'].sudo().search([('id','=',gratification_line_id)])
		grat.is_verified = True
		return request.render("hr_social_benefits.template_confirm_email_bbss")
