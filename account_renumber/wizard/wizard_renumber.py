# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import *

periods = {'00':'opening',
		   '01':'january',
		   '02':'february',
		   '03':'march',
		   '04':'april',
		   '05':'may',
		   '06':'june',
		   '07':'july',
		   '08':'august',
		   '09':'september',
		   '10':'october',
		   '11':'november',
		   '12':'december',
		   '13':'closing'}

class WizardRenumber(models.TransientModel):
	_name = 'wizard.renumber'
	_description = 'Wizard Renumber'	

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_id = fields.Many2one('account.period',string='Periodo')
	first_number = fields.Integer(string=u'Primer Número',default=1)
	journal_ids = fields.Many2many('account.journal','account_renumber_journal_rel','id_wizard_renumber','id_journal_wizard',string=u'Libros', required=True)

	def renumber(self):
		if len(self.journal_ids)<1:
			raise UserError("Debe seleccionar al menos un libro")

		order_by = 'DATE,INVOICE_DATE'

		for journal in self.journal_ids:
			if journal.type == 'sale':
				order_by = 'MOVE_TYPE, REF'
			sql = """UPDATE ACCOUNT_MOVE SET VOU_NUMBER = T.RNUM FROM
				(
				SELECT JOURNAL_ID, VOU_NUMBER, ID,INVOICE_DATE,DATE,
				LPAD(((ROW_NUMBER() OVER (PARTITION BY JOURNAL_ID ORDER BY %s)::TEXT)::INTEGER+%s)::TEXT, 6, '0') AS RNUM
				FROM ACCOUNT_MOVE
				WHERE JOURNAL_ID = %d AND periodo_de_fecha(DATE,IS_OPENING_CLOSE) = %s AND STATE = 'posted' AND COMPANY_ID = %d
				ORDER BY JOURNAL_ID)T
				WHERE ACCOUNT_MOVE.ID =T.ID""" % (order_by,str(self.first_number-1),journal.id,self.period_id.code,self.company_id.id)

			self.env.cr.execute(sql)
			sql = """
				SELECT (ROW_NUMBER() OVER (PARTITION BY JOURNAL_ID ORDER BY %s)::TEXT)::INTEGER+%s AS rnum
				FROM ACCOUNT_MOVE
				WHERE JOURNAL_ID = %d AND periodo_de_fecha(DATE,IS_OPENING_CLOSE) = %s AND STATE = 'posted' AND COMPANY_ID = %d
				ORDER BY JOURNAL_ID""" % (order_by,str(self.first_number-1),journal.id,self.period_id.code,self.company_id.id)

			self.env.cr.execute(sql)
			res = self.env.cr.dictfetchall()
			if res:
				reg = self.env['account.journal.sequence'].search([('journal_id','=',journal.id),('fiscal_year_id','=',self.period_id.fiscal_year_id.id)],limit=1)
				if not reg:
					raise UserError(u'No existe una secuencia para el diario y la fecha seleccionada.')
				reg.write({periods[self.period_id.code[4:]]: int(res[len(res)-1]['rnum'])+1})


		return self.env['popup.it'].get_message('SE GENERO EXITOSAMENTE')