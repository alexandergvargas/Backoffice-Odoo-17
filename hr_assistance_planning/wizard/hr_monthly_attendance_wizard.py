# -*- coding: utf-8 -*-

import base64
import calendar
import io
from datetime import date, datetime, timedelta

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

try:
    import xlsxwriter
except BaseException:
    pass

class HrMonthlyAttendanceWizard(models.TransientModel):
    _name = "hr.monthly.attendance.wizard"
    _description = "Hr Monthly Attendance Sheet"

    periodo_id = fields.Many2one('hr.period', string='Periodo')
    company_id = fields.Many2one('res.company',u'Compañía', default=lambda self: self.env.company,readonly=True)

    def generate_attendance(self):
        data = self.read()[0]
        # print("data",data)
        report_id = self.env.ref("hr_assistance_planning.hr_monthly_attendance_report")
        return report_id.report_action(self, data=data, config=False)

    def print_report(self):
        attch_obj = self.env["ir.attachment"]
        # fp = StringIO()
        fp = io.BytesIO()
        for rec in self:
            res_data = []
            result_data = []
            att_data = {}
            data = []
            no_of_class = 1
            matched_dates = []
            days_of_month = rec.periodo_id.date_end.day
            month_days = range(1, days_of_month + 1)
            # print("days_of_month", days_of_month)
            for student in self.env["hr.attendance.monitor"].search([('fecha', '>=', rec.periodo_id.date_start),('fecha', '<=', rec.periodo_id.date_end)], order='fecha'):
                day_date = student.fecha.day
                # print("student", student.employee_id.name)
                # print("day_date", day_date)
                for att_count in range(1, days_of_month + 1):
                    if day_date == att_count:
                        # print("matched_dates", matched_dates)
                        status = "F"
                        # if student.is_present:
                        if student.state == 'ok':
                            status = no_of_class
                            if (day_date in matched_dates or not matched_dates):
                                if att_data.get(student.employee_id.name) and att_data.get(student.employee_id.name).get(att_count):
                                    if (att_data.get(student.employee_id.name).get(att_count) != "F"):
                                        status = (int(att_data.get(student.employee_id.name).get(att_count)) + no_of_class)
                                        # print("student if", student.employee_id.name)
                                        # print("status", status)
                        elif student.state == 'descanso':
                            if att_data.get(student.employee_id.name) and att_data.get(student.employee_id.name).get(att_count):
                                if (att_data.get(student.employee_id.name).get(att_count) != "F"):
                                    status = 'D'
                                    # print("student DESCANSO elif", student.employee_id.name)
                                    # print("status", status)
                        elif student.state == 'vacaciones':
                            if att_data.get(student.employee_id.name) and att_data.get(student.employee_id.name).get(att_count):
                                if (att_data.get(student.employee_id.name).get(att_count) != "F"):
                                    status = 'V'
                        elif student.state == 'justificada':
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
                            if student.state not in ('ok', 'descanso', 'vacaciones','justificada','descansotrab'):
                                total_absent = no_of_class
                            if student.state == 'descanso':
                                data.append({
                                    "student_code": student.employee_id.identification_id,
                                    "total_absent": total_absent,
                                    "name": student.employee_id.name,
                                    "establecimiento": student.employee_id.work_location_id.name,
                                    "att": {att_count: 'D'},
                                })
                            elif student.state == 'vacaciones':
                                data.append({
                                    "student_code": student.employee_id.identification_id,
                                    "total_absent": total_absent,
                                    "name": student.employee_id.name,
                                    "establecimiento": student.employee_id.work_location_id.name,
                                    "att": {att_count: 'V'},
                                })
                            elif student.state == 'justificada':
                                data.append({
                                    "student_code": student.employee_id.identification_id,
                                    "total_absent": total_absent,
                                    "name": student.employee_id.name,
                                    "establecimiento": student.employee_id.work_location_id.name,
                                    "att": {att_count: 'J'},
                                })
                            elif student.state == 'descansotrab':
                                data.append({
                                    "student_code": student.employee_id.identification_id,
                                    "total_absent": total_absent,
                                    "name": student.employee_id.name,
                                    "establecimiento": student.employee_id.work_location_id.name,
                                    "att": {att_count: 'DT'},
                                })
                            else:
                                data.append({
                                    # "roll_no": student.employee_id.identification_id,
                                    "student_code": student.employee_id.identification_id,
                                    "total_absent": total_absent,
                                    "name": student.employee_id.name,
                                    "establecimiento": student.employee_id.work_location_id.name,
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
                                    if student.state not in ('ok', 'descanso', 'vacaciones','justificada','descansotrab'):
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
                                "establecimiento": student.employee_id.work_location_id.name,
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

            # Create Work Book
            workbook = xlsxwriter.Workbook(fp)
            # Set Table Header format
            tbl_data_fmt = workbook.add_format({
                    "border": 1,
                    "font_name": "Calibri",
                    "align": "center",
                    "font_size": 10,
                })
            tbl_data_fmt.set_bg_color("#D3D3D3")
            tbl_data_fmt_left = workbook.add_format({
                    "border": 1,
                    "font_name": "Calibri",
                    "font_size": 10
                })
            tbl_data_fmt_p = workbook.add_format({
                    "border": 1,
                    "font_name": "Calibri",
                    "align": "center",
                    "font_size": 10,
                })
            # sub header format
            head_fmt = workbook.add_format({
                    "border": 1,
                    "font_name": "Calibri",
                    "font_size": 10,
                    "align": "center",
                    "bold": True,
                })
            head_fmt_left = workbook.add_format({
                    "border": 1,
                    "font_name": "Calibri",
                    "font_size": 10,
                    "bold": True,
                })
            # Main head format
            main_head_fmt = workbook.add_format({
                    "border": 1,
                    "font_name": "Calibri",
                    "align": "center",
                    "font_size": 14,
                    "bold": True,
                })
            main_head_fmt.set_bg_color("#DCDCDC")
            # print the data of students
            for data in res_data:
                count = 1
                row = 5
                # Add Sheet
                sheet = workbook.add_worksheet("Asistencia Empleados")
                sheet.freeze_panes(5, 0)
                # Main Header
                # print("company",data.get("school_name"))
                sheet.merge_range(0, 0, 0, len(month_days) + 4, data.get("school_name"),main_head_fmt)
                sheet.set_column(0, 0, 3)
                sheet.set_column(3, len(month_days) + 4, 3)
                sheet.set_column(1, 1, 25)
                # Sub Headers
                sheet.merge_range(1, 0, 1, 8, "Mes: " + rec.periodo_id.name, head_fmt_left)
                # sheet.merge_range(1, 9, 1, 19, "Name of the Teacher:" + str(data.get("user")), head_fmt_left)
                # sheet.merge_range(1, 29, 1, 34, "Batch:" + str(rec.course_id.name), head_fmt)
                sheet.merge_range(1, 9, 1, 35, "Estados: A=Asistio, F=Falta, D=Descanso, V=Vacaciones, J=Justificada, DT=Descanso Trabajado", head_fmt)
                sheet.write(4, 0, "N Ide", head_fmt)
                sheet.write(4, 1, "Empleados", head_fmt)
                sheet.write(4, 2, "Establecimiento", head_fmt)
                col = 3
                for mday in month_days:
                    sheet.write(4, col, mday, head_fmt)
                    col += 1
                sheet.write(4, col, "A", head_fmt)
                sheet.write(4, col + 1, "F", head_fmt)

                for line in data.get("result_data"):
                    present_no = 0
                    present = 0
                    absent = 0
                    col = 0
                    # if line.get("divisions") or data.get("elective"):
                    #     sheet.write(row, col, count, tbl_data_fmt)
                    # else:
                    sheet.write(row, col, line.get("student_code"), tbl_data_fmt_left)
                    sheet.write(row, col + 1, line.get("name"), tbl_data_fmt_left)
                    sheet.write(row, col + 2, line.get("establecimiento"), tbl_data_fmt_left,)

                    col = col + 3
                    for date in month_days:
                        if line.get("att").get(date):
                            if line.get("att").get(date) not in ['F','D','V','J','DT', False]:
                                present_no = present + int(line.get("att").get(date))
                                present = present + int(line.get("att").get(date))
                            if line.get("att").get(date) == "D":
                                # absent += 1
                                sheet.write(row, col, line.get("att").get(date), tbl_data_fmt)
                            if line.get("att").get(date) == "V":
                                sheet.write(row, col, line.get("att").get(date), tbl_data_fmt)
                            if line.get("att").get(date) == "J":
                                sheet.write(row, col, line.get("att").get(date), tbl_data_fmt)
                            if line.get("att").get(date) == "DT":
                                sheet.write(row, col, line.get("att").get(date), tbl_data_fmt)
                            if line.get("att").get(date) == "F":
                                absent += 1
                                sheet.write(row, col, line.get("att").get(date), tbl_data_fmt)
                            elif line.get("att").get(date) not in ['F','D','V','J','DT']:
                                sheet.write(row, col, present_no, tbl_data_fmt_p)
                        col += 1

                    sheet.write(row, col, present, tbl_data_fmt_p)
                    sheet.write(row, col + 1, line.get("total_absent"), tbl_data_fmt)
                    row += 1
                    count += 1
            # Workbook save and end
            workbook.close()
            data = base64.b64encode(fp.getvalue())
            fp.close()
            # Deleting existing attachment files
            attach_ids = attch_obj.search([("res_model", "=", "hr.monthly.attendance.wizard")])
            if attach_ids:
                try:
                    attach_ids.unlink()
                except BaseException:
                    pass
            # Creating Attachment
            doc_id = attch_obj.create({
                    "name": rec.periodo_id.name
                    + " "
                    + "Asistencia Mensual.xlsx",
                    "datas": data,
                    "res_model": "hr.monthly.attendance.wizard",
                })
            # Downloading the file
            return {
                "type": "ir.actions.act_url",
                "url": "web/content/%s?download=true" % (doc_id.id),
                "target": "current",
            }
