# -*- coding: utf-8 -*-
import tempfile
import binascii
import xlrd
from odoo import models, fields, exceptions, api, _
from odoo.exceptions import ValidationError,UserError
import logging

_logger = logging.getLogger(__name__)
try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class gen_partnerpgm(models.TransientModel):
    _name = "gen.partner.pgm"

    file = fields.Binary('Archivo')
    file_name = fields.Char()
    partner_option = fields.Selection([('create', 'Crear Partner'), ('update', 'Actualizar Partner')], string='Opcion',
                                      required=True, default="create")

    def create_partner(self, values):

        parent = state = country = l10n_latam = saleperson = empresa = vendor_pmt_term = cust_pmt_term = False
        if values.get('type') == 'company':
            if values.get('parent'):
                raise Warning('No puede dar padre si ha seleccionado el tipo de empresa')
            type = 'company'
        else:
            type = 'person'
            if values.get('parent'):
                parent_search = self.env['res.partner'].search([('name', '=', values.get('parent'))], limit=1)
                if parent_search:
                    parent = parent_search.id
                else:
                    raise Warning("Contacto Padre no disponible")

        if values.get('type_document_id'):
            s = str(values.get("type_document_id"))
            type_document_id = s.rstrip('0').rstrip('.') if '.' in s else s
            l10n_latam_search = self.env['l10n_latam.identification.type'].search(
                [('l10n_pe_vat_code', '=', type_document_id)], limit=1)
            if not l10n_latam_search:
                raise Warning("Tipo de Doc.3 no disponible en el sistema")
            else:
                l10n_latam = l10n_latam_search.id

        is_customer = False
        is_supplier = False
        is_employee = False

        if ((values.get('customer')) == '1'):
            is_customer = True

        if ((values.get('vendor')) == '1'):
            is_supplier = True

        if ((values.get('employee')) == '1'):
            is_employee = True

        if ((values.get('customer')) == 'SI'):
            is_customer = True

        if ((values.get('vendor')) == 'SI'):
            is_supplier = True

        if ((values.get('employee')) == 'SI'):
            is_employee = True

        s = str(values.get("vat"))
        vat = s.rstrip('0').rstrip('.') if '.' in s else s

        s = str(values.get("ref"))
        ref = s.rstrip('0').rstrip('.') if '.' in s else s

        vals = {
            'company_type': type,
            'l10n_latam_identification_type_id': l10n_latam,
            'vat': vat,
            'mobile': values.get('mobile'),
            'email': values.get('email'),
            'customer_rank': 1 if is_customer else 0,
            'supplier_rank': 1 if is_supplier else 0,
            'is_customer': is_customer,
            'is_supplier': is_supplier,
            'is_employee': is_employee,
        }
        partner_search = self.env['res.partner'].search([('name', '=', values.get('name'))])
        if partner_search:
            raise Warning(_('"%s" Partner ya existe.') % values.get('name'))
        else:
            res = self.env['res.partner'].create(vals)
            res.verify_ruc()
            res.verify_dni()
            res._renombrar_ref()
            res._onchange_name_lang()
            res.write({'company_id': self.env.company})
            return res

    def verify_if_exists_partner(self):
        if self.file:
            file_name = str(self.file_name)
            extension = file_name.split('.')[1]
        if extension not in ['xls', 'xlsx', 'XLS', 'XLSX']:
            raise exceptions.Warning(_('Cargue solo el archivo xls.!'))
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file))
        fp.seek(0)
        values = {}
        res = {}
        result = []
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        for row_no in range(sheet.nrows):
            if row_no <= 0:
                fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(
                    map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))
                values.update(
                    {
                        'type_document_id': line[1],
                        'vat': line[2],

                    })
                gg = self.verify_partner(values)
                if gg:
                    result.append(gg)

        if len(result) > 0:
            import io
            from xlsxwriter.workbook import Workbook
            ReportBase = self.env['report.base']

            direccion = self.env['account.main.parameter'].search([('company_id', '=', self.env.company.id)],
                                                                  limit=1).dir_create_file

            if not direccion:
                raise UserError(
                    u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

            workbook = Workbook(direccion + 'Partners_Existentes.xlsx')
            workbook, formats = ReportBase.get_formats(workbook)

            import importlib
            import sys
            importlib.reload(sys)

            worksheet = workbook.add_worksheet("Partners")
            worksheet.set_tab_color('blue')

            HEADERS = ['TIPO DOC', 'NRO DOC']
            worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
            x = 1

            for line in result:
                worksheet.write(x, 0, line[1] if line[1] else '', formats['especial1'])
                worksheet.write(x, 1, str(line[2]) if str(line[2]) else '', formats['especial1'])

                x += 1

            widths = [19, 12]
            worksheet = ReportBase.resize_cells(worksheet, widths)
            workbook.close()

            f = open(direccion + 'Partners_Existentes.xlsx', 'rb')
            return self.env['popup.it'].get_file('Partners Duplicados.xlsx',
                                                 base64.encodebytes(b''.join(f.readlines())))

        else:
            return self.env['popup.it'].get_message('NO EXISTEN PARTNERS DUPLICADOS.')

    def verify_partner(self, values):
        l10n_latam = False
        if values.get('type_document_id'):
            s = str(values.get('type_document_id'))
            type_document_id = s.rstrip('0').rstrip('.') if '.' in s else s
            l10n_latam_search = self.env['l10n_latam.identification.type'].search(
                [('l10n_pe_vat_code', '=', type_document_id)], limit=1)
            if not l10n_latam_search:
                raise Warning("Tipo de Doc.1 %s no disponible en el sistema" % (type_document_id))
            else:
                l10n_latam = l10n_latam_search.id

        s = str(values.get('vat'))
        vat = s.rstrip('0').rstrip('.') if '.' in s else s
        search_partner = self.env['res.partner'].search(
            [('vat', '=', vat), ('l10n_latam_identification_type_id', '=', l10n_latam)], limit=1)
        if search_partner:
            return [values.get('name'), values.get('type_document_id'), values.get('vat')]

    def import_partner(self):
        if self.file:
            file_name = str(self.file_name)
            extension = file_name.split('.')[1]
        if extension not in ['xls', 'xlsx', 'XLS', 'XLSX']:
            raise exceptions.Warning(_('Cargue solo el archivo xls.!'))
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file))
        fp.seek(0)
        values = {}
        res = {}
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        for row_no in range(sheet.nrows):
            if row_no <= 0:
                fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(
                    map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))
                if self.partner_option == 'create':
                    values.update(
                        {
                            'type': line[0],
                            'type_document_id': line[1],
                            'vat': line[2],
                            'mobile': line[3],
                            'email': line[4],
                            'customer': line[5],
                            'vendor': line[6],
                            'employee': line[7],
                        })
                    res = self.create_partner(values)
                else:
                    l10n_latam = False
                    if line[1]:
                        s = str(line[1])
                        type_document_id = s.rstrip('0').rstrip('.') if '.' in s else s
                        l10n_latam_search = self.env['l10n_latam.identification.type'].search(
                            [('l10n_pe_vat_code', '=', type_document_id)], limit=1)
                        if not l10n_latam_search:
                            raise Warning("Tipo de Doc. %s no disponible en el sistema" % (type_document_id))
                        else:
                            l10n_latam = l10n_latam_search.id

                    s = str(line[2])
                    vat = s.rstrip('0').rstrip('.') if '.' in s else s
                    search_partner = self.env['res.partner'].search(
                        [('vat', '=', vat), ('l10n_latam_identification_type_id', '=', l10n_latam)], limit=1)
                    if not search_partner:
                        raise Warning('No existe un partner con Nro de Documento "%s" para actualizar' % (vat))
                    parent = False
                    state = False
                    country = False
                    saleperson = False
                    vendor_pmt_term = False
                    cust_pmt_term = False

                    is_customer = False
                    is_supplier = False

                    if ((line[4]) == '1'):
                        is_customer = True

                    if ((line[5]) == '1'):
                        is_supplier = True

                    if ((line[4]) == 'SI'):
                        is_customer = True

                    if ((line[5]) == 'SI'):
                        is_supplier = True

                    search_partner.mobile = line[3]
                    search_partner.email = line[4]
                    if search_partner.customer_rank < 1 and is_customer:
                        search_partner.customer_rank = 1
                    if search_partner.supplier_rank < 1 and is_supplier:
                        search_partner.supplier_rank = 1
                    search_partner.user_id = saleperson
                    search_partner.verify_ruc()
                    search_partner.verify_dni()
                    search_partner._renombrar_ref()
                    search_partner._onchange_name_lang()
        return self.env['popup.it'].get_message('SE IMPORTARON LOS PARTNERS DE MANERA CORRECTA.')

    def download_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_template_import_contactos',
            'target': 'new',
        }
