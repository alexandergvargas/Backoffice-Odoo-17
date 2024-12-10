# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrMembership(models.Model):
	_name = 'hr.membership'
	_description = 'Afiliacion'
	_inherit = ['mail.thread']

	name = fields.Char(string='Entidad', tracking=True)
	company_id = fields.Many2one('res.company', string=u'Compañía', default=lambda self: self.env.company.id)
	fixed_commision = fields.Float(string='Comision Sobre Flujo %', tracking=True)
	mixed_commision = fields.Float(string='Comision Mixta %', tracking=True)
	prima_insurance = fields.Float(string='Prima de Seguros %', tracking=True)
	retirement_fund = fields.Float(string='Aporte Fondo de Pensiones %', tracking=True)
	insurable_remuneration = fields.Float(string='Remuneracion Asegurable', tracking=True)
	account_id = fields.Many2one('account.account', string='Cuenta Contable', tracking=True)
	is_afp = fields.Boolean(string='Es AFP', default=False, tracking=True)

	def get_membership_wizard(self):
		wizard = self.env['hr.membership.wizard'].create({'name':'Generacion de Afiliaciones'})
		return {
			'type':'ir.actions.act_window',
			'res_id':wizard.id,
			'view_mode':'form',
			'res_model':'hr.membership.wizard',
			'views':[[self.env.ref('hr_base.hr_membership_wizard_form').id,'form']],
			'context': self._context,
			'target':'new'
		}

	def get_membership_wizard_edit(self):
		wizard = self.env['hr.membership.wizard'].create({'name':'Generacion de Afiliaciones'})
		return {
			'type':'ir.actions.act_window',
			'res_id':wizard.id,
			'view_mode':'form',
			'res_model':'hr.membership.wizard',
			'views':[[self.env.ref('hr_base.hr_membership_wizard_form_edit').id,'form']],
			'context': self._context,
			'target':'new'
		}