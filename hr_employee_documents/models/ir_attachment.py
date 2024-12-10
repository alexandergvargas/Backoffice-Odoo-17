# -*- coding: utf-8 -*-

from odoo import fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    doc_attach_rel_ids = fields.Many2many(comodel_name='hr.employee.document',
                                          relation='doc_attachment_ids',
                                          column1='attach_id3',
                                          column2='doc_id',
                                          string="Archivos Adjuntos",
                                          help="Archivos Adjuntos.",
                                          invisible=1)
