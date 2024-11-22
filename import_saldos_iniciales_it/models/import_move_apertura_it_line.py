from odoo import models, fields, _

class ImportMoveAperturaItLine(models.Model):
	_name = 'import.move.apertura.it.line'

	wizard_id = fields.Many2one('import.move.apertura.it','Importacion')
	ruc = fields.Char(string='RUC')
	razon_social = fields.Many2one('res.partner',string='Razon Social')
	fecha_emision = fields.Date(string='Fecha Emision')
	fecha_vencimiento = fields.Date(string='Fecha Vencimiento')
	vendedor = fields.Many2one('res.users',string='Vendedor')
	tipo_doc = fields.Many2one('l10n_latam.document.type',string='Tipo Doc.')
	numero = fields.Char(string='Numero')
	moneda = fields.Many2one('res.currency',string='Moneda')
	saldo_mn = fields.Float(string='Saldo MN')
	saldo_me = fields.Float(string='Saldo ME')
	cuenta = fields.Many2one('account.account',string='Cuenta')
	tipo_cambio = fields.Float(string='Tipo Cambio',digits=(12,4))
	doc_origin = fields.Char(string='Doc Origen')

	n_ruc = fields.Char('Campo')
	n_razonsoc = fields.Char('Campo')
	n_fecha_emision = fields.Char('Campo')
	n_fecha_vencimiento = fields.Char('Campo')
	n_vendedor = fields.Char('Campo')
	n_tipo_doc = fields.Char('Campo')
	n_numero = fields.Char('Campo')
	n_moneda = fields.Char('Campo')
	n_saldo_mn = fields.Char('Campo')
	n_saldo_me = fields.Char('Campo')
	n_cuenta = fields.Char('Campo')
	n_tipo_cambio = fields.Char('Campo',digits=(12,4))
	n_doc_origin = fields.Char('Campo')