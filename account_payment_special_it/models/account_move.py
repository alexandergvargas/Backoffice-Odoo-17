from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
import base64

class account_move(models.Model):
    _inherit = 'account.move'

    
    payment_special = fields.Boolean(
        compute='_compute_payment_special', 
        string='Pago Especial',
        store=True)
    
    @api.depends('company_id')
    def _compute_payment_special(self):
        for i in self:
            i.payment_special = self.env['account.main.parameter'].search([('company_id','=',i.company_id.id)],limit=1).payment_special

    def context_vals_multipayment_line(self):
        vals=[] 
        for i in self:
                      
            for line in i.line_ids.filtered(lambda l:   l.display_type and
                                                        l.parent_state == 'posted' and
                                                        l.partner_id and
                                                        l.type_document_id and
                                                        l.account_id.account_type in ['liability_payable','asset_receivable'] and
                                                        not l.reconciled and
                                                        l.company_id and
                                                        l.amount_residual != 0 and
                                                        l.amount_residual_currency !=0 ):
                residual_amount = 0
                if line.currency_id:
                    residual_amount = line.amount_residual_currency
                else:
                    residual_amount = line.amount_residual                                
                val = {                
                    'partner_id': line.partner_id.id,
                    'tipo_documento': line.type_document_id.id,
                    'invoice_id':line.id,
                    'saldo':residual_amount,
                    'operation_type': i.type_op_det,
                    'good_services': i.detraction_percent_id.code,
                    'cta_abono': i.acc_number_partner_id.id
                }
                vals.append(val)   			
        return vals
    
    def action_create_payment_special(self):
        for i in self:
            context ={
                'default_payment_special':i.payment_special,
                'default_glosa': "COBRANZA FACTURA %s"%(i.vou_number),
                'default_invoice_ids':i.context_vals_multipayment_line()
            }         
            return {
                    'type': 'ir.actions.act_window',
                    'name': "Generar Pago especial",
                    'view_type': 'form',
                    'view_mode': 'form',
                    'context': context,
                    'res_model': 'multipayment.advance.it',                   
            }
        
    def action_creates_payments_special(self):
        vals=[] 
        for i in self:                      
            for line in i.line_ids.filtered(lambda l:   l.display_type and
                                                        l.parent_state == 'posted' and
                                                        l.partner_id and
                                                        l.type_document_id and
                                                        l.account_id.account_type in ['liability_payable','asset_receivable'] and
                                                        not l.reconciled and
                                                        l.company_id and
                                                        l.amount_residual != 0 and
                                                        l.amount_residual_currency !=0 ):
                residual_amount = 0
                if line.currency_id:
                    residual_amount = line.amount_residual_currency
                else:
                    residual_amount = line.amount_residual                                
                val = {                
                    'partner_id': line.partner_id.id,
                    'tipo_documento': line.type_document_id.id,
                    'invoice_id':line.id,
                    'saldo':residual_amount,
                    'operation_type': i.type_op_det,
                    'good_services': i.detraction_percent_id.code,
                    'cta_abono': i.acc_number_partner_id.id
                }
                vals.append(val)   	
        context = {
                #'default_payment_special':i.payment_special,
                #'default_glosa': "COBRANZA FACTURA %s"%(i.vou_number),
                'default_invoice_ids':vals
            }        
        return {
                    'type': 'ir.actions.act_window',
                    'name': "Generar Pago especial",
                    'view_type': 'form',
                    'view_mode': 'form',
                    'context': context,
                    'res_model': 'multipayment.advance.it',                   
            }
                