# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError

class AccountSequenceJournalWizard(models.TransientModel):
	_name='account.sequence.journal.wizard'
	
	name = fields.Char()
	journal_ids =fields.Many2many('account.journal','account_journal_sequence_wizard_rel','sequence_wizard_id','journal_id',string='Diarios',required=True)	

	def get_fiscal_year(self):
		today = fields.Date.context_today(self)
		fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
		if not fiscal_year:
			raise UserError(u'No existe un año fiscal con el año actual.')
		else:
			return fiscal_year.id

	fiscal_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',default=lambda self:self.get_fiscal_year())

	def do_rebuild(self):
		diarios= ""
		obj_seq = self.env['account.journal.sequence']
		flag = False
		for i in self.journal_ids:
			seq = obj_seq.search([('fiscal_year_id','=',self.fiscal_id.id),('journal_id','=',i.id)],limit=1)
			if not seq:
				flag = True
				obj_seq.create({'fiscal_year_id':self.fiscal_id.id, 'journal_id':i.id})
				if diarios == "":
					diarios+= i.name
				else:
					diarios+= ', '+i.name
		if flag:
			return self.env['popup.it'].get_message("Se ha generado las secuencias para el ejercicio fiscal '"+self.fiscal_id.name+"'" + ", y los diarios '"+diarios+"'")
		else:
			return self.env['popup.it'].get_message("Ya existen las secuencias para los diarios seleccionados.")