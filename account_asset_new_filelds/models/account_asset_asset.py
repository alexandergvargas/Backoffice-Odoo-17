from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

class account_asset_asset(models.Model):
	_inherit = 'account.asset.asset'

	date_at = fields.Date( 
		string = "Fecha de adquisición tributaria",
		copy=False)
	valor_at = fields.Float(
		string = "Valor de adquisición tributaria",
		copy=False)
	depreciacion_at  = fields.Float(
		string = "Depreciación acumulada tributaria",
		copy=False)
	valor_at_me = fields.Float(
		string = "Valor de Adquisición tributaria ME",
		compute = "_compute_valor_at_me",
		store=True)
	depreciacion_at_me  = fields.Float(
		string = "Depreciación acumulada tributaria ME",
		compute = "_compute_depreciacion_at",
		store=True)
	
	@api.depends('tipo_cambio_d','valor_at')
	def _compute_valor_at_me(self):
		for record in self:
			if record.tipo_cambio_d!=0:
				record.valor_at_me = record.valor_at/record.tipo_cambio_d
	
	@api.depends('tipo_cambio_d','depreciacion_at')
	def _compute_depreciacion_at(self):
		for record in self:
			if record.tipo_cambio_d!=0:
				record.depreciacion_at_me = record.depreciacion_at/record.tipo_cambio_d

	@api.onchange('date_at')
	def _get_currency_rate(self):		
			cu_rate = self.env['res.currency.rate'].search([('name','=',self.date_at),('company_id','=',self.company_id.id)],limit=1)
			if cu_rate:
				self.tipo_cambio_d = cu_rate.sale_type
				
	def asset_action_change_state(self):
		for i in self:
			if i.state == 'draft':
				i.compute_depreciation_board()
				i.validate()

	def get_amls_unsubscribe(self, line_baja):
		if not self.valor_at:
			self.valor_at = self.value
		if not self.category_id.account_retire_id:
			raise UserError(u'No esta establecida la Cuenta de Retiro en la Categoría del Activo.')
		deprec_acum = line_baja.depreciated_value+(self.depreciacion_at or 0)
		lineas = []
		vals = (0,0,{
				'account_id': self.category_id.account_asset_id.id,
				'name': 'BAJA DE ACTIVO '+self.name,
				'debit': 0,
				'credit': self.valor_at,
				'company_id': self.company_id.id,
			})
		lineas.append(vals)

		vals = (0,0,{
				'account_id': self.category_id.account_depreciation_id.id,
				'name': 'BAJA DE ACTIVO '+self.name,
				'debit': deprec_acum,
				'credit': 0,
				'company_id': self.company_id.id,
			})
		lineas.append(vals)

		vals = (0,0,{
				'account_id': self.category_id.account_retire_id.id,
				'name': 'BAJA DE ACTIVO '+self.name,
				'debit': self.valor_at - deprec_acum,
				'credit': 0,
				'company_id': self.company_id.id,
			})
		lineas.append(vals)
		return lineas
	
	def get_values_am(self, lineas, journal_id):
		return {
			'company_id': self.company_id.id,
			'journal_id': journal_id.id,
			'date': self.f_baja,
			'line_ids':lineas,
			'ref': 'BAJA-'+ (self.code or ''),
			'glosa':'BAJA DE ACTIVO '+self.name,
			'move_type':'entry'}