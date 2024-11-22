# Copyright (C) 2015 Akretion (<http://www.akretion.com>)
# @author: Florian da Costa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "SQL Export",
    "version": "17.0.1.1.0",
    "author": "Akretion,Odoo Community Association (OCA),ITGRUPO-Glenda Julia Merma Mayhua",
    "website": "https://github.com/OCA/server-tools",
    "license": "AGPL-3",
    "category": "Generic Modules/Others",
    'summary': """- Obligatorio""",
    "depends": [
        "sql_request_abstract",
        "spreadsheet_dashboard"
    ],
    "data": [
        "views/sql_export_view.xml",
        "wizard/wizard_file_view.xml",
        "security/sql_export_security.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    'auto_install': True,
}
