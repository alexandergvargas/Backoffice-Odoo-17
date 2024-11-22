from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'
	

	def _post(self, soft=True):
		for elem in self:
			if elem.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
				if elem.currency_rate == 1 and elem.currency_id.id != elem.company_id.currency_id.id:
					raise UserError (u"EL TIPO DE CAMBIO NO DEBE SER 1 EN MONEDAS EXTRANJERA")
		return super(AccountMove,self)._post(soft=soft)