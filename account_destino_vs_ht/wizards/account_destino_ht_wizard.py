# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
from io import BytesIO

import base64
import subprocess
import sys

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	import openpyxl
except:
	install('openpyxl==3.0.5')

class AccountDestinoHTWizard(models.TransientModel):
	_name = 'account.destino.ht.wizard'

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_id = fields.Many2one('account.period',string=u'Periodo',required=True)

	def get_report(self):
		ReportBase = self.env['report.base']
		workbook = ReportBase.get_excel_sql_export(self._get_sql())
		return self.env['popup.it'].get_file('Diferencia Destinos VS Hoja de Trabajo.xlsx',workbook)

	def _get_sql(self):
		sql = """SELECT T.cuenta, T2.saldo, T.saldo as destino, T2.saldo - T.saldo as diferencia FROM (SELECT a1.cuenta, sum(a1.debe-a1.haber) as saldo FROM get_destinos({period_code},{period_code},{company_id}) a1 group by a1.cuenta)T
		LEFT JOIN (select 
			a2.code as cuenta,
			a1.debe,
			a1.haber,
			a1.debe-a1.haber as saldo
			from get_sumas_mayor_f1('{date_from}','{date_to}',{company_id},{show_closed}) a1
			left join account_account a2 on a2.id=a1.account_id) T2 ON T.cuenta = T2.cuenta
			where T2.saldo - T.saldo <> 0
				""".format(
					period_code = self.period_id.code,
					date_from = self.period_id.date_start.strftime('%Y/%m/%d'),
					date_to = self.period_id.date_end.strftime('%Y/%m/%d'),
					company_id = self.company_id.id,
					show_closed = "FALSE"
				)
		return sql