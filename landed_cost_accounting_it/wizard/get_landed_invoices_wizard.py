import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)
class GetLandedInvoices(models.TransientModel):
	_inherit = "get.landed.invoices.wizard"
	
	invoices_ids = fields.Many2many(
		string=_('Invoices'),
		comodel_name='account.move.line',
		required=True,
		domain="[('display_type','=','product'),('parent_state','=','posted'),('is_landed','=',True),('company_id','=',company_id)]"
	)