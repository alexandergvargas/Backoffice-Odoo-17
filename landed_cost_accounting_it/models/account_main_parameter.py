# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMainParameter(models.Model):
    _inherit = 'account.main.parameter'

    lc_account_id = fields.Many2one(
        string=_('Cuenta de Ingreso de Existencias por recibir'),
        comodel_name='account.account',
    )

    lc_journal_id = fields.Many2one(
        string=_('Diario de Ingreso de Existencias por recibir'),
        comodel_name='account.journal',
    )