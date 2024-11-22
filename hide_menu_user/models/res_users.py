# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    """
    Model to handle hiding specific menu items for certain users.
    """
    _inherit = 'res.users'

    def write(self, vals):
        """
         Write method for the ResUsers model.
         Ensure the menu will not remain hidden after removing it from the list.
           """
        res = super(ResUsers, self).write(vals)
        for record in self:
            for menu in record.hide_menu_ids:
                menu.write({
                    'restrict_user_ids': [fields.Command.link(record.id)]
                })
        return res

    def _get_is_admin(self):
        """
        Compute method to check if the user is an admin.
        The Hide specific menu tab will be hidden for the Admin user form.
        """
        for rec in self:
            rec.is_admin = False
            if rec.id == self.env.ref('base.user_admin').id:
                rec.is_admin = True

    hide_menu_ids = fields.Many2many(
        'ir.ui.menu', string="Ocultar Menu",
        store=True, help='Seleccione los elementos de menú que necesitan '
                         'Estar oculto para este usuario.')
    is_admin = fields.Boolean(compute=_get_is_admin, string="Es Admin",
                              help='Compruebe si el usuario es un administrador')


class IrUiMenu(models.Model):
    """
    Model to restrict the menu for specific users.
    """
    _inherit = 'ir.ui.menu'

    restrict_user_ids = fields.Many2many(
        'res.users', string="Usuarios restringidos",
        help='Usuarios restringidos para acceder a este menú')
