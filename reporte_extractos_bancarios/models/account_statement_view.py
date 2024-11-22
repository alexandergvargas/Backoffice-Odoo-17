from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError

class account_statement_view(models.Model):
    _name = 'account.statement.view'
    _description = 'Reporte de Extractos'
    _auto = False

    date = fields.Date(u'FECHA')
    des = fields.Char(u'DESCRIPCIÓN')
    partner = fields.Char(u'PARTNER')
    td = fields.Char(u'TD')
    ref = fields.Char(u'REFERENCIA')
    catalog_payment = fields.Char(u'MEDIO DE PAGO')
    amount = fields.Float('MONTO')
    reconcile  = fields.Boolean('CONCILIADO')