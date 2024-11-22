# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountRetentionComp(models.Model):
	_name = 'account.retention.comp'
	
	partner_id = fields.Many2one('res.partner',string='Proveedor')
	date = fields.Date(string='Fecha')
	retention_document_type = fields.Many2one('l10n_latam.document.type',string=u'Tipo Documento Retenciones',compute='compute_retention_document_type')
	serie_id = fields.Many2one('it.invoice.serie',string='Serie',copy=False)
	name = fields.Char(string='Nro Comprobante',copy=False)
	sequence_number_it = fields.Char(string='Backup Number',copy=False)
	amount = fields.Float(string='Monto',copy=False,compute='compute_amount_retention',store=True)
	lines_ids = fields.One2many('account.retention.comp.line','main_id',string='Lineas')
	state = fields.Selection([('draft','Borrador'),('done','Validado'),('cancel','Cancelado')],string='Estado',default='draft',copy=False)
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)
	move_id = fields.Many2one('account.move',string='Asiento',copy=False)

	@api.depends('lines_ids','state')
	def compute_amount_retention(self):
		for i in self:
			tot = 0
			for l in i.lines_ids:
				tot += l.amount_retention
			i.amount = tot

	@api.depends('company_id')
	def compute_retention_document_type(self):
		for i in self:
			i.retention_document_type = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).retention_document_type

	def unlink(self):
		for multi in self:
			if multi.state in ('done'):
				raise UserError(u"No puede eliminar un Comprobante de Retención que esta Finalizado")
		return super(AccountRetentionComp, self).unlink()
	
	@api.onchange('serie_id')
	def onchange_serie_id(self):
		if not self.name or self.name == '/':
			if self.serie_id:
				next_number = self.serie_id.sequence_id.number_next_actual
				if not self.serie_id.sequence_id.prefix:
					raise UserError("No existe un prefijo configurado en la secuencia de la serie.")
				prefix = self.serie_id.sequence_id.prefix
				padding = self.serie_id.sequence_id.padding
				self.name = prefix + "0"*(padding - len(str(next_number))) + str(next_number)

	def action_draft(self):
		if self.move_id.id:
			if self.move_id.state =='draft':
				pass
			else:
				for mm in self.move_id.line_ids:
					mm.remove_move_reconcile()
				self.move_id.button_cancel()
			self.move_id.line_ids.unlink()
			self.move_id.vou_number = "/"
			self.move_id.unlink()
		self.state = 'draft'

	def action_done(selfs):
		self = selfs
		name = self.name
		if (self.sequence_number_it != self.name):
			if self.serie_id.sequence_id:
				if not self.serie_id.sequence_id.prefix:
					raise UserError("No existe un prefijo configurado en la secuencia de la serie.")
				sequence = self.serie_id.sequence_id
				next_number =sequence.number_next_actual
				serie = str(next_number).rjust(sequence.padding, '0')
				serie = (sequence.prefix or '') + serie + (sequence.suffix or '')
				name = serie

				sequence.number_next_actual = next_number + self.serie_id.sequence_id.number_increment
				self.name = name
				self.sequence_number_it = name
		
		self.move_id = self.create_move()
		self.move_id._post()

		self.state = 'done'
		lines = self.env['account.retention.comp.line'].search([('main_id','!=',self.id)]).multipayment_line_id.ids
		for l in self.lines_ids:
			if l.multipayment_line_id.id in lines:
				raise UserError(u'Hay un pago que se encuentra en otro comprobante de Retención')
			
		return True
	
	def create_move(self):
		lineas = []
		param = self.env['account.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1)
		if not param.retention_account_id:
			raise UserError(u'No tiene configurado la Cuenta de Retención en los Parametros Principales de Contabilidad de su Compañía')
		if not param.vario_partner_id:
			raise UserError(u'No tiene configurado el Partner VARIOS en los Parametros Principales de Contabilidad de su Compañía')
		if not param.others_document_type:
			raise UserError(u'No tiene configurado el TD Otros en los Parametros Principales de Contabilidad de su Compañía')
		if not param.retention_document_type:
			raise UserError(u'No tiene configurado el TD de Rentención en los Parametros Principales de Contabilidad de su Compañía')
		if not param.retention_bo_journal_id:
			raise UserError(u'No tiene configurado el Diario para Rentenciones en los Parametros Principales de Contabilidad de su Compañía')
		tot_ret = 0
		for elemnt in self.lines_ids:
			vals = (0,0,{
				'account_id': param.retention_account_id.id,
				'partner_id':param.vario_partner_id.id,
				'type_document_id':param.others_document_type.id,
				'nro_comp': elemnt.multipayment_line_id.main_id.name,
				'name': elemnt.multipayment_line_id.main_id.name,
				'debit': elemnt.amount_retention,
				'credit': 0,
				'company_id': self.company_id.id,
			})
			tot_ret += elemnt.amount_retention
			lineas.append(vals)

		vals = (0,0,{
			'account_id': param.retention_account_id.id,
			'partner_id':self.partner_id.id,
			'type_document_id':param.retention_document_type.id,
			'nro_comp': self.name,
			'name': self.name,
			'debit':  0,
			'credit': tot_ret,
			'company_id': self.company_id.id,
		})
		lineas.append(vals)
		

		data = {
			'company_id': self.company_id.id,
			'partner_id': self.partner_id.id if self.partner_id else None,
			'l10n_latam_document_type_id': param.retention_document_type.id,
			'journal_id': param.retention_bo_journal_id.id,
			'date': self.date,
			'invoice_date': self.date,
			'line_ids':lineas,
			'ref': self.name,
			'glosa':u'POR LA EMISIÓN DE COMPROBANTE DE RETENCION NRO: %s'%self.name,
			'move_type':'entry'
		}

		move_id = self.env['account.move'].create(data)

		return move_id
	
	def action_cancel(self):
		if self.move_id.id:
			if self.move_id.state =='draft':
				pass
			else:
				for mm in self.move_id.line_ids:
					mm.remove_move_reconcile()
				self.move_id.button_cancel()
			self.move_id.line_ids.unlink()
			self.move_id.vou_number = "/"
			self.move_id.unlink()
		self.state = 'cancel'

	#@api.model
	#def create(self, vals):
	#	id_seq = self.env['ir.sequence'].search([('name', '=', 'Retenciones PM IT'),('company_id','=',self.env.company.id)],limit=1)

	#	if not id_seq:
	#		id_seq = self.env['ir.sequence'].create({'name': 'Retenciones PM IT', 
	#										'company_id': self.env.company.id, 
	#										'implementation': 'no_gap',
	#										'active': True, 
	#										'prefix': 'RET-', 
	#										'padding': 6, 
	#										'number_increment': 1, 
	#										'number_next_actual': 1})

	#	vals['name'] = id_seq._next()
	#	t = super(AccountRetentionComp, self).create(vals)
	#	return t
	
	def get_lines(self):
		wizard = self.env['get.account.multipayment.line.wizard'].create({
			'retention_comp': self.id,
			'company_id':self.company_id.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_get_account_multipayment_line_wizard' % module)
		return {
			'name':u'Seleccionar Lines de PM',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'get.account.multipayment.line.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
	
class AccountRetentionCompLine(models.Model):
	_name = 'account.retention.comp.line'
	
	main_id = fields.Many2one('account.retention.comp',string='Main',ondelete="cascade")
	type_document_id = fields.Many2one('l10n_latam.document.type',string='Tipo de Documento')	
	invoice_id = fields.Many2one('account.move.line',string='Factura')
	invoice_date_it = fields.Date(string=u'Fecha Emisión')
	amount_total_signed = fields.Float(string='Monto',digits=(12,2))
	debit = fields.Float(string='Pago',digits=(12,2))
	amount_retention = fields.Float(string='Monto Retenido',digits=(12,2))
	multipayment_line_id = fields.Many2one('multipayment.advance.it.line',string='PM')

	def unlink(self):
		for l in self:
			l.multipayment_line_id.retention_id = None
		return super(AccountRetentionCompLine, self).unlink()