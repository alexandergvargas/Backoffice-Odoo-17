# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountJournalSequence(models.Model):
	_name = 'account.journal.sequence'
	_description = 'Account Journal Sequence'

	@api.depends('fiscal_year_id','journal_id')
	def _get_name(self):
		for i in self:
			i.name = (i.journal_id.name or '') + ' - ' + (i.fiscal_year_id.name or '')

	name = fields.Char(compute=_get_name,store=True)
	
	journal_id = fields.Many2one('account.journal',string=u'Diario',required=True,ondelete="cascade")
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',required=True)
	opening = fields.Integer(string='APE',default=1)
	january = fields.Integer(string='ENE',default=1)
	february = fields.Integer(string='FEB',default=1)
	march = fields.Integer(string='MAR',default=1)
	april = fields.Integer(string='ABR',default=1)
	may = fields.Integer(string='MAY',default=1)
	june = fields.Integer(string='JUN',default=1)
	july = fields.Integer(string='JUL',default=1)
	august = fields.Integer(string='AGO',default=1)
	september = fields.Integer(string='SEP',default=1)
	october = fields.Integer(string='OCT',default=1)
	november = fields.Integer(string='NOV',default=1)
	december = fields.Integer(string='DOC',default=1)
	closing = fields.Integer(string='CIE',default=1)
	company_id = fields.Many2one('res.company',string=u'Compañía',related='journal_id.company_id',store=True)

	@api.constrains('journal_id','fiscal_year_id')
	def _check_unique_parameter(self):
		self.env.cr.execute("""select id from account_journal_sequence where journal_id = %d and fiscal_year_id = %d""" % (self.journal_id.id,self.fiscal_year_id.id))
		res = self.env.cr.dictfetchall()
		if len(res) > 1:
			raise UserError(u"Ya existen la secuencia para el diario y el año escogido.")