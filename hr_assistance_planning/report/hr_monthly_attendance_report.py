# -*- coding: utf-8 -*-

import calendar
from datetime import datetime
from odoo import api, models

class HrMonthlyAttendanceReport(models.AbstractModel):
    _name = "report.hr_assistance_planning.hr_monthly_attendance_report_tmpl"
    _description = "Hr Monthly Attendance Report"

    def get_dates(self, rec):
        days_of_month = rec.periodo_id.date_end.day
        return range(1, days_of_month + 1)

    def get_data(self, rec):
        # print("rec get_data",rec)
        res_data = []
        result_data = []
        att_data = {}
        data = []
        no_of_class = 1
        matched_dates = []
        days_of_month = rec.periodo_id.date_end.day
        # print("days_of_month", days_of_month)
        for student in self.env["hr.attendance.monitor"].search([('fecha', '>=', rec.periodo_id.date_start),('fecha', '<=', rec.periodo_id.date_end)],order='fecha'):
            day_date = student.fecha.day
            # print("student", student.employee_id.name)
            # print("day_date", day_date)
            for att_count in range(1, days_of_month + 1):
                if day_date == att_count:
                    # print("matched_dates", matched_dates)
                    status = "F"
                    # if student.is_present:
                    if student.state=='ok':
                        status = no_of_class
                        if (day_date in matched_dates or not matched_dates):
                            if att_data.get(student.employee_id.name) and att_data.get(student.employee_id.name).get(att_count):
                                if (att_data.get(student.employee_id.name).get(att_count) != "F"):
                                    status = (int(att_data.get(student.employee_id.name).get(att_count)) + no_of_class)
                                    # print("student if", student.employee_id.name)
                                    # print("status", status)
                    elif student.state=='descanso':
                        if att_data.get(student.employee_id.name) and att_data.get(student.employee_id.name).get(att_count):
                            if (att_data.get(student.employee_id.name).get(att_count) != "F"):
                                status = 'D'
                                # print("student DESCANSO elif", student.employee_id.name)
                                # print("status", status)
                    elif student.state=='vacaciones':
                        if att_data.get(student.employee_id.name) and att_data.get(student.employee_id.name).get(att_count):
                            if (att_data.get(student.employee_id.name).get(att_count) != "F"):
                                status = 'V'
                    elif student.state=='justificada':
                        if att_data.get(student.employee_id.name) and att_data.get(student.employee_id.name).get(att_count):
                            if (att_data.get(student.employee_id.name).get(att_count) != "F"):
                                status = 'J'
                    elif student.state == 'descansotrab':
                        if att_data.get(student.employee_id.name) and att_data.get(student.employee_id.name).get(att_count):
                            if (att_data.get(student.employee_id.name).get(att_count) != "F"):
                                status = 'DT'
                    else:
                        if day_date in matched_dates:
                            if att_data.get(student.employee_id.name) and att_data.get(student.employee_id.name).get(att_count):
                                if (att_data.get(student.employee_id.name).get(att_count) != "F"):
                                    status = int(att_data.get(student.employee_id.name).get(att_count))
                                    # print("student else", student.employee_id.name)
                                    # print("status", status)

                    # print("att_data", att_data)
                    if not att_data.get(student.employee_id.name):
                        att_data.update({student.employee_id.name: {att_count: str(status)}})
                        total_absent = 0
                        if student.state not in ('ok', 'descanso', 'vacaciones', 'justificada', 'descansotrab'):
                            total_absent = no_of_class
                        if student.state=='descanso':
                            data.append({
                                "student_code": student.employee_id.identification_id,
                                "total_absent": total_absent,
                                "name": student.employee_id.name,
                                "att": {att_count: 'D'},
                            })
                        elif student.state == 'vacaciones':
                            data.append({
                                "student_code": student.employee_id.identification_id,
                                "total_absent": total_absent,
                                "name": student.employee_id.name,
                                "att": {att_count: 'V'},
                            })
                        elif student.state == 'justificada':
                            data.append({
                                "student_code": student.employee_id.identification_id,
                                "total_absent": total_absent,
                                "name": student.employee_id.name,
                                "att": {att_count: 'J'},
                            })
                        elif student.state == 'descansotrab':
                            data.append({
                                "student_code": student.employee_id.identification_id,
                                "total_absent": total_absent,
                                "name": student.employee_id.name,
                                "att": {att_count: 'DT'},
                            })
                        else:
                            data.append({
                                "student_code": student.employee_id.identification_id,
                                "total_absent": total_absent,
                                "name": student.employee_id.name,
                                "att": {att_count: str(status)},
                            })
                        # print("student if not", student.employee_id.name)
                        # print("status", status)
                    else:
                        if student.state == 'descanso':
                            att_data.get(student.employee_id.name).update({att_count: 'D'})
                        elif student.state == 'vacaciones':
                            att_data.get(student.employee_id.name).update({att_count: 'V'})
                        elif student.state == 'justificada':
                            att_data.get(student.employee_id.name).update({att_count: 'J'})
                        elif student.state == 'descansotrab':
                            att_data.get(student.employee_id.name).update({att_count: 'DT'})
                        else:
                            att_data.get(student.employee_id.name).update({att_count: str(status)})
                        for stu in data:
                            if (stu.get("name") == student.employee_id.name):
                                # if not student.state=='ok':
                                if student.state not in ('ok', 'descanso', 'vacaciones', 'justificada', 'descansotrab'):
                                    stu.update({"total_absent": stu.get("total_absent") + no_of_class})
                                if student.state == 'descanso':
                                    stu.get("att").update({att_count: 'D'})
                                elif student.state == 'vacaciones':
                                    stu.get("att").update({att_count: 'V'})
                                elif student.state == 'justificada':
                                    stu.get("att").update({att_count: 'J'})
                                elif student.state == 'descansotrab':
                                    stu.get("att").update({att_count: 'DT'})
                                else:
                                    stu.get("att").update({att_count: str(status)})
                                # print("student not else", student.employee_id.name)
                                # print("status", status)
                else:
                    status = ""
                    if not att_data.get(student.employee_id.name):
                        att_data.update({student.employee_id.name: {att_count: status}})
                        data.append({
                            "student_code": student.employee_id.identification_id,
                            "total_absent": 0,
                            "name": student.employee_id.name,
                            "att": {att_count: status},
                        })
                    else:
                        if (att_data.get(student.employee_id.name).get("att_count") == ""):
                            att_data.get(student.employee_id.name).update({att_count: status})
                            for stu in data:
                                if (stu.get("name") == student.employee_id.name):
                                    stu.get("att").update({att_count: status})
            if day_date not in matched_dates:
                matched_dates.append(day_date)

        roll_no_list = []
        # print("data employee",data)
        for stu in data:
            roll_no_list.append(stu.get("student_code"))
        roll_no_list.sort()
        for roll_no in roll_no_list:
            for stu in data:
                if stu.get("student_code") == roll_no:
                    result_data.append(stu)
                    data.remove(stu)
        res_data.append({
                "school_name": self.env.company.name,
                "month": rec.periodo_id.name,
                "result_data": result_data,
        })
        # print("res_data",res_data)
        return res_data

    @api.model
    def _get_report_values(self, docids, data):
        report = self.env["ir.actions.report"]
        emp_report = report._get_report_from_name("hr_assistance_planning.hr_monthly_attendance_report_tmpl")
        model = self.env.context.get("active_model")
        docs = self.env[model].browse(self.env.context.get("active_id"))
        return {
            "doc_ids": docids,
            "doc_model": emp_report.model,
            "data": data,
            "docs": docs,
            "get_dates": self.get_dates,
            "get_data": self.get_data,
        }
