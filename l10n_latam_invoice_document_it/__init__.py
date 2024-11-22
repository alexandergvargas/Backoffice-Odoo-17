# -*- coding: utf-8 -*-

from . import models

import logging

_logger = logging.getLogger(__name__)

def _set_default_document_type(env):
	DocumentType = env['l10n_latam.document.type']
	_logger.warning('Actualizando')
	document_type07b = env.ref('l10n_pe.document_type07b', raise_if_not_found=False)
	document_type07b.write({'active':False})
	document_type08b = env.ref('l10n_pe.document_type08b', raise_if_not_found=False)
	document_type08b.write({'active':False})
	env.cr.execute("""update l10n_latam_document_type set internal_code = code where active = True""")
	document_type01 = env.ref('l10n_pe.document_type01', raise_if_not_found=False)
	document_type01.write({'digits_serie':4,'digits_number':8})
	document_type03 = env.ref('l10n_pe.document_type03', raise_if_not_found=False)
	document_type03.write({'digits_serie':4,'digits_number':8})
	document_type02 = env.ref('l10n_pe.document_type02', raise_if_not_found=False)
	document_type02.write({'digits_serie':4,'digits_number':8})
	document_type07 = env.ref('l10n_pe.document_type07', raise_if_not_found=False)
	document_type07.write({'digits_serie':4,'digits_number':8})
	DocumentType.create({
		'code': '00',
		'name': 'Otros',
		'report_name': 'Otros Documentos',
		'internal_type':'all',
		'country_id': env.ref('base.pe').id,
		'internal_code': '00'
	})