# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountAccountConfig(models.Model):
    _name = 'group.account.account.config'
    _description = 'Clasificación grupos de cuentas'

    name = fields.Char('Nombre',default="Clasificación grupos de cuentas")

    
    company_id = fields.Many2one(
        string=_('Compañia'), 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company,
        readonly=True
    )

    line_sheet_ids = fields.One2many(
        string=_('Detalle Hoja T'),
        comodel_name='group.account.account.config.line',
        inverse_name='main_id',
    )
    
    
    def update_account_sheet(self):
        for record in self:
            for line in record.line_sheet_ids:
                if line.prefix and line.clasification_sheet:
                    prefixes = "', '".join(line.prefix.split(','))
                    prefixes = f"'{prefixes}'"
                    self.env.cr.execute("""UPDATE account_group SET clasification_sheet = %s 
                                            WHERE LEFT(code_prefix_start,2) in (%s) 
                                            AND company_id = %d
                                        """% (line.clasification_sheet,prefixes,record.company_id.id))
        return self.env['popup.it'].get_message(u'SE CONFIGURÓ CORRECTAMENTE.')
    
    