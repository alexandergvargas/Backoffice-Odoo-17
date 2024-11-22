# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.sql import column_exists, create_column, drop_index, index_exists

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
	_inherit = 'account.move'
	

	def _auto_init(self):
		if index_exists(self.env.cr, "account_move_unique_name"):
			drop_index(self.env.cr, "account_move_unique_name", self._table)
			self.env.cr.execute("""
				CREATE UNIQUE INDEX account_move_unique_name
								 ON account_move(id, journal_id)
							  WHERE (state = 'posted' AND id is not null
								AND (l10n_latam_document_type_id IS NULL OR move_type NOT IN ('in_invoice', 'in_refund', 'in_receipt')));
			""")
		return super()._auto_init()
