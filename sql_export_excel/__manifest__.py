# Copyright 2019 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "SQL Export Excel",
    "version": "17.0.1.1.0",
    "author": "Akretion,Odoo Community Association (OCA),ITGRUPO-Glenda Julia Merma Mayhua",
    "website": "https://github.com/OCA/server-tools",
    "license": "AGPL-3",
    "category": "Generic Modules/Others",
    'summary': """- Obligatorio""",
    "depends": ["sql_export"],
    "data": [
        "views/sql_export_view.xml",
    ],
    "installable": True,
    'auto_install': True,
}
