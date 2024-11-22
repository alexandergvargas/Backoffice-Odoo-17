# -*- coding: utf-8 -*-
import datetime
from random import choice
import openpyxl
import io
from string import digits
import base64
import datetime as datetime
import logging
from odoo import http
from odoo.http import request
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from odoo import models, fields, api
from odoo.exceptions import UserError
import locale
import re
from dateutil.relativedelta import relativedelta

nombres_meses_espanol = [
    'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO',
    'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'
]

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cuota_count = fields.Integer(string="Invoice Count", default=15)

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final, date=date)
        for move in moves:
            # RUC - BAYLY LETTS ANDRES
            if move.partner_id.id == 4516:
                _logger.warning('Entro Bayli')
                move.invoice_date = datetime.datetime.now() - datetime.timedelta(hours=5)
                # move.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search(
                #     [('code', '=', '03')])[0].id
                _logger.warning(move.l10n_latam_document_type_id)
                move.l10n_pe_edi_operation_type = '0101'
                descriptions = [line.name for line in move.invoice_line_ids]
                move.glosa = '\n'.join(descriptions)
                move._compute_formatted_text_facturas()
            # RUC
            elif move.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code == '6':
                _logger.warning("ENTRO ACA RUC")
                if move.amount_total_signed >= 700:
                    _logger.warning("ES MAYOR A 700")
                    # move.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search([('code', '=', '01')])
                    move.l10n_pe_edi_operation_type = '1001'
                    move.linked_to_detractions = True
                    move.detraction_percent_id = self.env['detractions.catalog.percent'].search([('code', '=', '005')])[
                        0].id
                    for line in move.invoice_line_ids:
                        _logger.warning(line.product_id.id)
                        _logger.warning(line.product_id.name)
                        _logger.warning(line.partner_id.id)
                        _logger.warning(line.partner_id.name)

                        # INTERMOTORS #TI-ODOO

                        if line.product_id.id == 348 and line.partner_id.id == 4555:
                            move.glosa = 'USUARIOS ODOO - ' + '@mes @año'
                            move._compute_formatted_text_facturas()
                            break

                        # LFO  #TI-ODOO

                        elif line.product_id.id == 348 and line.partner_id.id == 5182:
                            move.glosa = 'ERP ODOO - ' + '@mes @año'
                            move._compute_formatted_text_facturas()
                            break

                        # CLINICA ZEGARRA  #TI-ODOO

                        elif line.product_id.id == 348 and line.partner_id.id == 5421:
                            descriptions = [line.name for line in move.invoice_line_ids]
                            move.glosa = '\n'.join(descriptions)
                            move._compute_formatted_text_facturas()
                            break

                        # STLTH

                        elif line.partner_id.id == 5422:
                            descriptions = [line.name for line in move.invoice_line_ids]
                            move.glosa = '\n'.join(descriptions)
                            move._compute_formatted_text_facturas()
                            break

                        # INFOBIP # LEGAL

                        elif line.product_id.id == 322 and line.partner_id.id == 4552:
                            partner_id_to_check = 4552
                            product_id_to_check = 322
                            description_to_check = 'PAGO DE FEE DE ÉXITO DE LA CUOTA N° @cuota'
                            if line.partner_id.id == partner_id_to_check:
                                matching_lines = [line for line in move.invoice_line_ids if
                                                  line.product_id.id == product_id_to_check and line.name == description_to_check]
                                if matching_lines:
                                    move.glosa = matching_lines[0].name
                                    move.glosa = matching_lines[0].name.replace('@cuota',
                                                                                str(self.cuota_count))
                                    self.cuota_count += 1
                            move._compute_formatted_text_facturas()

                        move.glosa = move.invoice_line_ids[0].name
                        move._compute_formatted_text_facturas()

                if move.amount_total_signed <= 699:
                    _logger.warning("ES MENOR A 699")
                    # move.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search([('code', '=', '01')])
                    # move.write({'state': 'draft'})
                    move.l10n_pe_edi_operation_type = '0101'

                    for line in move.invoice_line_ids:
                        _logger.warning(line.product_id.id)
                        _logger.warning(line.product_id.name)
                        _logger.warning(line.partner_id.id)

                        # INTERMOTORS #TI-ODOO

                        if line.product_id.id == 348 and line.partner_id.id == 4555:
                            move.glosa = 'USUARIOS ODOO - ' + '@mes @año'
                            move._compute_formatted_text_facturas()
                            break

                        # LFO  #TI-ODOO

                        elif line.product_id.id == 348 and line.partner_id.id == 5182:
                            move.glosa = 'ERP ODOO - ' + '@mes @año'
                            move._compute_formatted_text_facturas()
                            break

                        # CLINICA ZEGARRA  #TI-ODOO

                        elif line.product_id.id == 348 and line.partner_id.id == 5421:
                            descriptions = [line.name for line in move.invoice_line_ids]
                            move.glosa = '\n'.join(descriptions)
                            move._compute_formatted_text_facturas()
                            break

                        # STLTH

                        elif line.partner_id.id == 5422:
                            descriptions = [line.name for line in move.invoice_line_ids]
                            move.glosa = '\n'.join(descriptions)
                            move._compute_formatted_text_facturas()
                            break

                        # INFOBIP  #LEGAL

                        elif line.product_id.id == 322 and line.partner_id.id == 4552:
                            partner_id_to_check = 4552
                            product_id_to_check = 322
                            description_to_check = 'PAGO DE FEE DE ÉXITO DE LA CUOTA N° @cuota'
                            if line.partner_id.id == partner_id_to_check:
                                matching_lines = [line for line in move.invoice_line_ids if
                                                  line.product_id.id == product_id_to_check and line.name == description_to_check]
                                if matching_lines:
                                    move.glosa = matching_lines[0].name
                                    move.glosa = matching_lines[0].name.replace('@cuota',
                                                                                str(self.cuota_count))
                                    self.cuota_count += 1
                            move._compute_formatted_text_facturas()

                        move.glosa = move.invoice_line_ids[0].name
                        move._compute_formatted_text_facturas()

            # DNI
            elif move.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code == '1':
                # move.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search(
                #     [('code', '=', '03')])[0].id

                move._compute_formatted_text_facturas()
                move.glosa = move.invoice_line_ids[0].name
            # DOCUMENTO EXTRANJERO
            elif move.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code == '0':
                _logger.info("DOCUMENTO EXTRANJERO")
                move.invoice_date = datetime.datetime.now() - datetime.timedelta(hours=5)

                _logger.info("PASOOOOOOOOOO ACA EXACTAMENTE")
                # move.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search(
                #     [('code', '=', '01')])[0].id
                move.l10n_pe_edi_operation_type = '0201'

                descriptions = [line.name for line in move.invoice_line_ids]
                move.glosa = '\n'.join(descriptions + ['@mes @año'])
                move._compute_formatted_text_facturas()
        return moves


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('name')
    def _compute_formatted_text(self):
        today = datetime.datetime.now()
        next_month = today.replace(day=1) + relativedelta(months=1)
        before_month = today.replace(day=1) - relativedelta(months=1)
        tag_replacements = {
            '@dia': datetime.datetime.now().strftime('%d'),
            '@mes': nombres_meses_espanol[datetime.datetime.now().month - 1],
            '@año': str(datetime.datetime.now().year),
            '@cuota': str(15),
            '@di_va_a': str(21),
            '@di_va_d': str(20),
            '@me_va_d': nombres_meses_espanol[next_month.month - 1],
            '@di_rpc_a': str(18),
            '@di_rpc_d': str(17),
            '@me_rpc_a': nombres_meses_espanol[before_month.month - 1],
        }
        for record in self:
            formatted_text = record.name

            if formatted_text:
                for tag, replacement in tag_replacements.items():
                    formatted_text = formatted_text.replace(tag, replacement)
            record.name = formatted_text

    def _prepare_invoice_line(self, **optional_values):
            res = super()._prepare_invoice_line(**optional_values)
            res.update({
                'name': self.name
            })
            return res


class accountmove(models.Model):
    _inherit = 'account.move'

    @api.onchange('glosa')
    def _compute_formatted_text_facturas(self):
        today = datetime.datetime.now()
        next_month = today.replace(day=1) + relativedelta(months=1)
        before_month = today.replace(day=1) - relativedelta(months=1)
        tag_replacements = {
            '@dia': datetime.datetime.now().strftime('%d'),
            '@mes': nombres_meses_espanol[datetime.datetime.now().month - 1],
            '@año': str(datetime.datetime.now().year),
            '@cuota': str(15),
            '@di_va_a': str(21),
            '@di_va_d': str(20),
            '@me_va_d': nombres_meses_espanol[next_month.month - 1],
            '@di_rpc_a': str(18),
            '@di_rpc_d': str(17),
            '@me_rpc_a': nombres_meses_espanol[before_month.month - 1],
        }

        for record in self:
            formatted_text = record.glosa

            if formatted_text:
                for tag, replacement in tag_replacements.items():
                    formatted_text = formatted_text.replace(tag, replacement)
            record.glosa = formatted_text



class SaleSubscriptionPlan(models.Model):
    _inherit = 'sale.subscription.plan'


    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company, readonly=True)
