from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class multipayment_advance_it(models.Model):
    _inherit = 'multipayment.advance.it'


    def action_import_account_multipayment_advance_wizard(self):
        for i in self:
            if i.state =='draft':
                return {
                    'name': 'Importar Lineas de Caja',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'import.account.multipayment.advance.wizard',
                    'context': {'default_multipayment_advance_id': i.id},
                    'target': 'new',
                }