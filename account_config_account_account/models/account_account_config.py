# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountAccountConfig(models.Model):
    _name = 'account.account.config'
    _description = 'Configuraciones Plan contable'

    name = fields.Char('Nombre',default="Configuración Plan contable")

    
    company_id = fields.Many2one(
        string=_('Compañia'), 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company,
        readonly=True
    )

    line_m_close_ids = fields.One2many(
        string=_('Detalle Cierre'),
        comodel_name='account.account.config.line',
        inverse_name='config_m_close_id',
    )
    
    line_sheet_ids = fields.One2many(
        string=_('Detalle Hoja T'),
        comodel_name='account.account.config.line',
        inverse_name='config_sheet_id',
    )
    
    line_type_it_ids = fields.One2many(
        string=_('Detalle EF'),
        comodel_name='account.account.config.line',
        inverse_name='config_type_it_id',
    )
    
    line_type_fe_ids = fields.One2many(
        string=_('Detalle FE'),
        comodel_name='account.account.config.line',
        inverse_name='config_type_fe_id',
    )

    line_type_ptn_ids = fields.One2many(
        string=_('Detalle PTN'),
        comodel_name='account.account.config.line',
        inverse_name='config_type_ptn_id',
    )
    
    def update_account_sheet(self):
        for record in self:
            for line in record.line_sheet_ids:
                if line.prefix and line.clasification_sheet:
                    prefixes = "', '".join(line.prefix.split(','))
                    prefixes = f"'{prefixes}'"
                    self.env.cr.execute("""UPDATE account_account SET clasification_sheet = %s 
                                            WHERE LEFT(code,2) in (%s) 
                                            AND company_id = %d
                                        """% (line.clasification_sheet,prefixes,record.company_id.id))
        return self.env['popup.it'].get_message(u'SE CONFIGURÓ CORRECTAMENTE.')
    
    def update_account_close(self):
        for record in self:
            for line in record.line_m_close_ids:
                if line.prefix and line.m_close:
                    prefixes = "', '".join(line.prefix.split(','))
                    prefixes = f"'{prefixes}'"
                    self.env.cr.execute("""UPDATE account_account SET m_close = %s 
                                            WHERE LEFT(code,2) in (%s) 
                                            AND company_id = %d
                                        """% (line.m_close,prefixes,record.company_id.id))
        return self.env['popup.it'].get_message(u'SE CONFIGURÓ CORRECTAMENTE.')
    
    def update_account_ef_type_it(self):
        for record in self:
            for line in record.line_type_it_ids:
                if line.prefix and line.account_type_it_id:
                    prefixes = "', '".join(line.prefix.split(','))
                    prefixes = f"'{prefixes}'"
                    self.env.cr.execute("""UPDATE account_account SET account_type_it_id = %d 
                                            WHERE LEFT(code,2) in (%s) 
                                            AND company_id = %d
                                        """% (line.account_type_it_id.id,prefixes,record.company_id.id))
        return self.env['popup.it'].get_message(u'SE CONFIGURÓ CORRECTAMENTE.')
    
    def update_account_type_cash_id(self):
        for record in self:
            for line in record.line_type_fe_ids:
                if line.prefix and line.account_type_cash_id:
                    prefixes = "', '".join(line.prefix.split(','))
                    prefixes = f"'{prefixes}'"
                    self.env.cr.execute("""UPDATE account_account SET account_type_cash_id = %d 
                                            WHERE LEFT(code,2) in (%s) 
                                            AND company_id = %d
                                        """% (line.account_type_cash_id.id,prefixes,record.company_id.id))
        return self.env['popup.it'].get_message(u'SE CONFIGURÓ CORRECTAMENTE.')
    
    def update_patrimony_id(self):
        for record in self:
            for line in record.line_type_ptn_ids:
                if line.prefix and line.patrimony_id:
                    prefixes = "', '".join(line.prefix.split(','))
                    prefixes = f"'{prefixes}'"
                    self.env.cr.execute("""UPDATE account_account SET patrimony_id = %d 
                                            WHERE LEFT(code,2) in (%s) 
                                            AND company_id = %d
                                        """% (line.patrimony_id.id,prefixes,record.company_id.id))
        return self.env['popup.it'].get_message(u'SE CONFIGURÓ CORRECTAMENTE.')