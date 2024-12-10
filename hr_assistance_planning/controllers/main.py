# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.tools import float_round
import datetime
from odoo.addons.hr_attendance.controllers.main import HrAttendance

class HrAttendanceInherit(HrAttendance):

	@staticmethod
	def _get_geoip_response(mode, assistance_planning_id=False, latitude=False, longitude=False):
		return {
			'city': request.geoip.city.name or _('Unknown'),
			'country_name': request.geoip.country.name or request.geoip.continent.name or _('Unknown'),
			'latitude': latitude or request.geoip.location.latitude or False,
			'longitude': longitude or request.geoip.location.longitude or False,
			'ip_address': request.geoip.ip,
			'browser': request.httprequest.user_agent.browser,
			'mode': mode,
			'activity_id':assistance_planning_id #AGREGA EL TURNO
		}


	@http.route(["/hr_attendance/<token>"], type='http', auth='public', website=True, sitemap=True)
	def open_kiosk_mode(self, token):
		company = self._get_company(token)
		if not company:
			return request.not_found()
		else:
			employee_list = [{"id": e["id"],
							  "name": e["name"],
							  "avatar": e["avatar_1024"].decode(),
							  "job": e["job_id"][1] if e["job_id"] else False,
							  "department": {"id": e["department_id"][0] if e["department_id"] else False,
											 "name": e["department_id"][1] if e["department_id"] else False
											 }
							  } for e in request.env['hr.employee'].sudo().search_read(domain=[('company_id', '=', company.id)],
																					   fields=["id",
																							   "name",
																							   "avatar_1024",
																							   "job_id",
																							   "department_id"])]
			departement_list = [{'id': dep["id"],
								 'name': dep["name"],
								 'count': dep["total_employee"]
								 } for dep in request.env['hr.department'].sudo().search_read(domain=[('company_id', '=', company.id)],
																							  fields=["id",
																									  "name",
																									  "total_employee"])]

			activities = [{'id': ac["id"],
								 'name': ac["name"]
								 } for ac in request.env['attendance.activity'].sudo().search_read(
																							  fields=["id",
																									  "name"])]
			# print("activities de controller",activities)
			request.session.logout(keep_db=True)
			return request.render(
				'hr_attendance.public_kiosk_mode',
				{
					'kiosk_backend_info': {
						'token': token,
						'company_id': company.id,
						'company_name': company.name,
						'employees': employee_list,
						'departments': departement_list,
						'kiosk_mode': company.attendance_kiosk_mode,
						'barcode_source': company.attendance_barcode_source,
						'lang': company.partner_id.lang,
						'activities': activities
					}
				}
			)


	@http.route('/hr_attendance/manual_selection', type="json", auth="public")
	def manual_selection(self, token, employee_id, pin_code, assistance_planning_id=None):
		company = self._get_company(token)
		if company:
			employee = request.env['hr.employee'].sudo().browse(employee_id)
			if employee.company_id == company and ((not company.attendance_kiosk_use_pin) or (employee.pin == pin_code)):
				employee.sudo()._attendance_action_change(self._get_geoip_response('kiosk',assistance_planning_id)) #AGREGA EL TURNO
				# print("_get_geoip_response()",self._get_geoip_response('kiosk',assistance_planning_id))
				# print("_attendance_action_change",employee.sudo()._attendance_action_change(self._get_geoip_response('kiosk',assistance_planning_id)))
				return self._get_employee_info_response(employee)
		return {}
