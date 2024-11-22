# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO
import uuid
class AccountCtaCte(models.Model):
	_name = 'account.cta.cte'
	_description = 'Principal Cuenta Corriente'

	name = fields.Char(string=u'Descripción')
	date = fields.Date(string='Fecha')
	type_register = fields.Selection([('origin', 'Origen'), ('adjustment', 'Ajuste')], string='Tipo Registro',default='origin')
	line_ids = fields.One2many('account.cta.cte.si','main_id',string='Detalles')
	state = fields.Selection([('draft','Borrador'),
							('posted','Publicado'),
							('cancel','Cancelado')],string='Estado',default='draft')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	def import_lines(self):
		wizard = self.env['import.cta.cte.line.wizard'].create({
			'cta_cte_id':self.id
			})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_import_cta_cte_line_wizard_form' % module)
		return {
			'name':u'Importar Lineas Cuentas Corrientes',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'import.cta.cte.line.wizard',
			'view_id': view.id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	
	def action_post(self):
		for i in self:
			i.state = 'posted'
	
	def action_draft(self):
		for i in self:
			i.state = 'draft'

	def action_cancel(self):
		for i in self:
			i.state = 'cancel'
	
	def action_get_report(self):
		wizard = self.env['account.cta.cte.report.wizard'].create({
			'cta_cte_id': self.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_account_cta_cte_report_wizard_form' % module)
		return {
			'name':u'Generar reporte',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'account.cta.cte.report.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	
	def _check_journal_period_close(self,vals=None):
		for main in self:
			period = self.env['account.journal.period'].search([('company_id','=',main.company_id.id),('date_start','<=',main.date),('date_end','>=',main.date)],limit=1)
			if period:
				if period.state == 'done':
					raise UserError('No puede agregar/modificar entradas anteriores e inclusive a la fecha de bloqueo %s - %s. \n %s'%(period.date_start.strftime('%Y/%m/%d'),period.date_end.strftime('%Y/%m/%d'),str(vals if vals else '')))
		return True

	def write(self, vals):
		res = True
		for main in self:
			if vals:
				main._check_journal_period_close(vals)
			res |= super(AccountCtaCte, main).write(vals)
		return res
			
	@api.model_create_multi
	def create(self, vals_list):
		rslt = super(AccountCtaCte, self).create(vals_list)
		rslt._check_journal_period_close()
		return rslt

	def unlink(self):
		self._check_journal_period_close()
		res = super(AccountCtaCte, self).unlink()
		return res

class AccountCtaCteSi(models.Model):
	_name = 'account.cta.cte.si'
	_description = 'Detalle Cuenta Corriente'

	main_id = fields.Many2one('account.cta.cte', string=u'Main',required=True,ondelete="cascade")
	date = fields.Date(string='Fecha',related='main_id.date')
	journal_id = fields.Many2one('account.journal', string='Diario')
	partner_id = fields.Many2one('res.partner', string='Socio')
	type_document_id = fields.Many2one('l10n_latam.document.type', string='Tipo de Documento')
	nro_comp = fields.Char(string=u'Número Comprobante')
	invoice_date = fields.Date(string='Fecha Factura')
	date_maturity = fields.Date(string='Fecha Vencimiento')
	glosa = fields.Text(string='Glosa')
	account_id = fields.Many2one('account.account', string='Cuenta')
	currency_id = fields.Many2one('res.currency', string='Moneda')
	debit = fields.Float(string='Debe')
	credit = fields.Float(string='Haber')
	amount_currency = fields.Float(string='Importe moneda')
	type_register = fields.Selection(string='Tipo Registro',related='main_id.type_register')
	invoice_user_id = fields.Many2one('res.users', string='Vendedor')
	company_id = fields.Many2one('res.company',string=u'Compañía',related='main_id.company_id')

	@api.onchange('nro_comp','type_document_id')
	def onchange_comp(self):
		for i in self:
			i.nro_comp = i.type_document_id._get_ref(i.nro_comp)

	@api.constrains('account_id')
	def constrains_is_document_an(self):
		for i in self:
			if i.account_id:
				if not i.account_id.is_document_an:
					raise UserError(u'No puede usar una cuenta que no tenga Análisis por Documento. (%s)'%(i.account_id.code))
	
	@api.constrains('partner_id','account_id','nro_comp','invoice_date','date_maturity','type_document_id')
	def constrains_cta_cte(self):
		for i in self:
			if not i.account_id or not i.partner_id or not i.nro_comp or not i.invoice_date or not i.date_maturity or not i.type_document_id:
				raise UserError(u"Esta creando un registro y no esta estableciendo un campo obligatorio. \
					\n - Cuenta\
					\n - Socio\
					\n - Número de Comprobante\
					\n - Fecha Emisión\
					\n - Fecha Vencimiento\
					\n - Tipo de Documento")
			if i.type_register == 'origin':
				dup = self.search([('partner_id','=',i.partner_id.id),('account_id','=',i.account_id.id),('type_document_id','=',i.type_document_id.id),('nro_comp','=',i.nro_comp),('type_register','=','origin'),('id','!=',i.id)])
				if dup:
					raise UserError(u'No puede existir más de un registro Origen que obtenga estos mismo datos: \
					 \n Cuenta: %s \
					 \n Socio: %s \
					 \n Tipo de Documento: %s \
					 \n Número de Comprobante: %s'%(i.account_id.code,i.partner_id.name,i.type_document_id.code,i.nro_comp))

	@api.model_create_multi
	def create(self, vals_list):
		res = super(AccountCtaCteSi, self).create(vals_list)
		main = res.mapped('main_id')
		main._check_journal_period_close()
		return res

	def write(self, vals):
		result = True
		for line in self:
			if vals:
				line.main_id._check_journal_period_close(vals)
			result |= super(AccountCtaCteSi, line).write(vals)

		return result

	def unlink(self):
		main = self.mapped('main_id')
		main._check_journal_period_close()
		res = super(AccountCtaCteSi, self).unlink()
		return res