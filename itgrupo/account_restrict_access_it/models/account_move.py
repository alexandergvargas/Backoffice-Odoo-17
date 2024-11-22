# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
from datetime import datetime
from odoo.exceptions import UserError

class AccountReport(models.AbstractModel):
	_inherit = "account.report"

	def get_html(self, options, line_id=None, additional_context=None):
		res=super(AccountReport,self).get_html(options, line_id, additional_context)
		if self.env.company.restricted_account:
			cadsql="""select res_groups_users_rel from res_groups
				inner join res_groups_users_rel on res_groups.id = res_groups_users_rel.gid
				where res_groups.name ='Restringir datos para usuarios' and res_groups_users_rel.uid="""+str(self.env.uid)
			self.env.cr.execute(cadsql)
			data = self.env.cr.dictfetchall()
			if len(data)>0:
				modelo = self.env.company.model_resticted_ids.filtered(lambda x: x.model==self._name)
				if len(modelo)>0:
					return ""
		
		return res

class BaseModelExtend2(models.AbstractModel):
	_inherit = 'base'


	def read(self, fields=None, load='_classic_read'):
		selected_companies = self.env.companies
		for l in selected_companies:
			if l.restricted_account:
				cadsql="""select res_groups_users_rel from res_groups
					inner join res_groups_users_rel on res_groups.id = res_groups_users_rel.gid
					where res_groups.name->>'en_US' ='Restringir datos para usuarios' and res_groups_users_rel.uid="""+str(self.env.uid)
				self.env.cr.execute(cadsql)
				data = self.env.cr.dictfetchall()
				if len(data)>0:
					modelo = l.sudo().model_resticted_ids.filtered(lambda x: x.model==self._name)
					if len(modelo)>0:
						return []

		return super(BaseModelExtend2,self).read(fields,load)



	@api.model
	def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):		
		selected_companies = self.env.companies
		for l in selected_companies:
			if l.restricted_account:
				cadsql="""select res_groups_users_rel from res_groups
					inner join res_groups_users_rel on res_groups.id = res_groups_users_rel.gid
					where res_groups.name->>'en_US' ='Restringir datos para usuarios' and res_groups_users_rel.uid="""+str(self.env.uid)
				self.env.cr.execute(cadsql)
				data = self.env.cr.dictfetchall()
				if len(data)>0:
					modelo = l.sudo().model_resticted_ids.filtered(lambda x: x.model==self._name)
					if len(modelo)>0:
						return []
		return super(BaseModelExtend2,self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)


class res_company(models.Model):
	_inherit = 'res.company'

	restricted_account  = fields.Boolean('Restringir modelos')
	model_resticted_ids = fields.Many2many('ir.model','rel_company_model','company_id','model_id')


