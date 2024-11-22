# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class BankRecWidgetLine(models.Model):
    _inherit = 'bank.rec.widget.line'

    nro_comp = fields.Char(
        compute='_compute_nro_comp',
        store=True,
        readonly=False
    )

    type_document_id = fields.Many2one(
        comodel_name='l10n_latam.document.type',
        compute='_compute_type_document_id',
        store=True,
        readonly=False
    )

    cash_flow_id = fields.Many2one(
        comodel_name='account.cash.flow',
        compute='_compute_cash_flow_id',
        store=True,
        readonly=False
    )

    @api.depends('source_aml_id')
    def _compute_nro_comp(self):
        for line in self:
            if line.flag in ('new_aml','liquidity'):
                line.nro_comp = line.source_aml_id.nro_comp
            else:
                line.nro_comp = line.nro_comp
    

    @api.depends('source_aml_id')
    def _compute_type_document_id(self):
        for line in self:
            if line.flag in ('new_aml','liquidity'):
                line.type_document_id = line.source_aml_id.type_document_id
            else:
                line.type_document_id = line.type_document_id
    
    @api.depends('source_aml_id')
    def _compute_cash_flow_id(self):
        for line in self:
            if line.flag in ('liquidity'):
                line.cash_flow_id = line.source_aml_id.cash_flow_id
            else:
                line.cash_flow_id = line.cash_flow_id

    def _get_aml_values(self, **kwargs):
        # EXTENDS account_accountant
        return super()._get_aml_values(
            **kwargs,
            nro_comp=self.nro_comp,
            type_document_id=self.type_document_id.id,
            cash_flow_id=self.cash_flow_id.id,
        )
