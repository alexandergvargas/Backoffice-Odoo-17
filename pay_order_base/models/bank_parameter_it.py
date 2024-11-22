# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class BankParameterIt(models.Model):
	_name = 'bank.parameter.it'

	@api.depends('bank_id')
	def _get_name(self):
		for i in self:
			i.name = i.bank_id.name

	name = fields.Char(compute=_get_name,store=True)
	bank_id = fields.Many2one('res.bank',string='Banco')
	type_doc_partner_ids = fields.One2many('type.doc.partner.bank','parameter_id',string='Tipo Doc Partner')
	type_doc_invoice_ids = fields.One2many('type.doc.invoice.bank','parameter_id',string='Tipo Comprobante Pago')
	type_doc_payment_ids = fields.One2many('type.doc.payment.bank','parameter_id',string='Tipo Abono')
	type_doc_partnerbank_ids = fields.One2many('type.doc.partnerbank.bank','parameter_id',string='Tipo Cuenta')
	type_doc_bank_ids = fields.One2many('type.doc.bank','parameter_id',string='Banco')
	format_id = fields.Many2one('format.bank.it', string='Formato')


class TypeDocPartnerBank(models.Model):
	_name = 'type.doc.partner.bank'

	parameter_id = fields.Many2one('bank.parameter.it',string='Banco')
	code = fields.Char(string=u'Código')
	identification_type_id = fields.Many2one('l10n_latam.identification.type',string='Tipo de Doc')

class TypeDocInvoiceBank(models.Model):
	_name = 'type.doc.invoice.bank'

	parameter_id = fields.Many2one('bank.parameter.it',string='Banco')
	code = fields.Char(string=u'Código')
	type_document_id = fields.Many2one('l10n_latam.document.type',string='Tipo de Comprobante')

class TypeDocPaymentBank(models.Model):
	_name = 'type.doc.payment.bank'

	parameter_id = fields.Many2one('bank.parameter.it',string='Banco')
	code = fields.Char(string=u'Código')
	payment_type_id = fields.Many2one('payment.type.catalog',string='Tipo de Abono')

class TypeDocPartnerbankBank(models.Model):
	_name = 'type.doc.partnerbank.bank'

	parameter_id = fields.Many2one('bank.parameter.it',string='Banco')
	code = fields.Char(string=u'Código')
	partnerbank_type_id = fields.Many2one('partner.bank.type.catalog',string='Tipo de Cuenta')

class TypeDocPartnerbankBank(models.Model):
	_name = 'type.doc.bank'

	parameter_id = fields.Many2one('bank.parameter.it',string='Banco')
	name = fields.Char(string=u'Nombre')
	bank_id = fields.Many2one('res.bank',string='Banco')