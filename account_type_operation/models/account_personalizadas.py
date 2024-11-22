# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class account_personalizadas(models.Model): 
	_name = 'account.personalizadas'

	name = fields.Char(
		string="Concepto"
	)
	
	cuenta_mn_id = fields.Many2one(
		'account.account',
		string='Cuenta MN',
		domain=[('deprecated', '=', False)]
		)
	cuenta_me_id = fields.Many2one(
		'account.account',
		string='Cuenta ME',
		domain=[('deprecated', '=', False)]
		)
		 
	p_type = fields.Selection([('asset_receivable','Por Cobrar'),('liability_payable','Por Pagar')],string='Tipo')

	use_default = fields.Boolean(string='Usar como predeterminado',default=False)

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company)

	type_document_id = fields.Many2one(
        comodel_name='l10n_latam.document.type',
		string=_('Tipo documento'),
	)

	@api.constrains('use_default')
	def _check_unique_default(self):
		if self.use_default:
			self.env.cr.execute("""select id from account_personalizadas where company_id = %d and use_default = true and p_type='%s' """ % (self.company_id.id,self.p_type))
			res = self.env.cr.dictfetchall()
			if len(res) > 1:
				raise UserError(u"Ya existe una cuenta predeterminada %s en esta compañía configurada como predeterminada."%(dict(self._fields['p_type'].selection).get(self.p_type)))


	
