# -*- coding: utf-8 -*-

from odoo import fields, models


class HrDocumentType(models.Model):
    _name = 'hr.document.type'
    _description = "Hr Document Type"

    name = fields.Char(string="Nombre", required=True, help="Nombre del tipo de documento")
