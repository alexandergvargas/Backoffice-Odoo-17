import pytz

from odoo import fields, api, models, _
from odoo.exceptions import UserError, RedirectWarning
from datetime import datetime
from markupsafe import Markup


class MsQuery(models.Model):
	_name = "ms.query"
	_description = "Execute Query"
	_inherit = ['mail.thread']
	
	name = fields.Char('Title', required=True)
	query = fields.Text('Query', required=True)
	result = fields.Text('Result', default='[]')

	def get_datetime_tz(self):
		return pytz.UTC.localize(datetime.now()).astimezone(
			pytz.timezone(self.env.user.tz or 'UTC')).strftime('%Y-%m-%d %H:%M:%S')
	
	def get_credentials(self):
		wizard = self.env['login.sql.wizard'].create({
			'ms_query_id': self.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_login_sql_wizard_form' % module)
		return {
			'name':u'Ingresar PIN',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'login.sql.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def execute_query(self):
		if not self.query:
			return
		prefix = self.query[:6].upper()
		try:
			self._cr.execute(self.query)
		except Exception as e:
			raise UserError(e)

		if prefix == 'SELECT':
			result = self._cr.dictfetchall()
			if result:
				self.result = '\n\n'.join(str(res) for res in result)
			else:
				self.result = "Data not found"
		elif prefix == 'UPDATE':
			self.result = '%d row(s) affected' % self._cr.rowcount
		else:
			self.result = 'Successful'
		self.message_post(body=Markup(f"""{self.query}<br/><br/>Executed on {self.get_datetime_tz()}"""))
