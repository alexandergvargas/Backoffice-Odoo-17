from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
import base64

class account_main_parameter(models.Model):
    _inherit = 'account.main.parameter'



    payment_special = fields.Boolean(
            string=u'Aplica Pago Especial', 
            default=False)
    
    def write(self, vals):
        for i in self:
            res = super(account_main_parameter,i).write(vals)
            if 'payment_special' in vals:
                i.value_payment_special()
            return res

    def value_payment_special(self):
        for i in self:
            self.env.cr.execute("""UPDATE account_move SET payment_special = %s WHERE company_id = %d""" % (i.payment_special ,i.company_id.id))
        
